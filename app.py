import os
import requests
import random
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
from DriverIntentProcessor import DriverIntentProcessor
from GoogleMapsIntegration import GoogleMapsIntegration
import threading
import time

# Load environment variables
load_dotenv()

# Initialize Flask app and components
app = Flask(__name__, template_folder='templates')
socketio = SocketIO(app, cors_allowed_origins="*")
maps = GoogleMapsIntegration()

# Mock data structures
MOCK_RIDES = [
    {
        "id": "R1",
        "passenger_name": "John Doe",
        "pickup_location": "Kuala Lumpur Sentral",
        "dropoff_location": "KLCC",
        "status": "pending",
        "estimated_fare": 15.50,
        "distance": "3.2 km",
        "estimated_time": "15 mins"
    }
]

MOCK_DESTINATIONS = [
    {
        "id": "D1",
        "name": "KLCC",
        "address": "Kuala Lumpur City Centre, 50088 Kuala Lumpur",
        "coordinates": {"lat": 3.1577, "lng": 101.7114}
    },
    {
        "id": "D2",
        "name": "KL Sentral",
        "address": "KL Sentral, 50470 Kuala Lumpur",
        "coordinates": {"lat": 3.1340, "lng": 101.6860}
    }
]

# Central KL coordinates for busy areas search
CENTRAL_KL = (3.1478, 101.6953)  # Latitude, Longitude of central Kuala Lumpur

# Active ride simulation
active_ride = None

# API Keys
GOOGLE_AI_API_KEY = os.getenv('GOOGLE_AI_API_KEY')
GOOGLE_AI_API_URL = 'https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent'

@app.route('/list_models', methods=['GET'])
def list_models():
    try:
        models_url = f'https://generativelanguage.googleapis.com/v1/models?key={GOOGLE_AI_API_KEY}'
        print(f"Fetching models from: {models_url}")

        models_response = requests.get(models_url)
        print(f"Models response status: {models_response.status_code}")

        if models_response.status_code == 200:
            models_data = models_response.json()
            return jsonify(models_data)
        else:
            return jsonify({'error': f'Failed to list models: {models_response.text}'}), models_response.status_code
    except Exception as e:
        return jsonify({'error': f'Error listing models: {str(e)}'}), 500

@app.before_request
def log_request_info():
    if request.path == '/process_query':
        print(f"Request Method: {request.method}")
        print(f"Request Headers: {request.headers}")
        print(f"Request Data: {request.get_data(as_text=True)}")

@app.route('/')
def index():
    return render_template('index.html')


# Initialize intent processor
intent_processor = DriverIntentProcessor()

@app.route('/process_query', methods=['POST'])
def process_query():
    try:
        data = request.json
        if not data or 'query' not in data:
            return jsonify({'error': 'No query provided'}), 400

        query = data['query']
        print(f"Received query: {query}")

        # Get current context
        context = {
            'driver_id': request.headers.get('X-Driver-ID', str(random.randint(1000, 9999))),
            'shift_duration': random.randint(0, 8),  # Mock shift duration
            'earnings_percentage': random.randint(50, 100),  # Mock earnings percentage
            'has_pending_ride': bool(next((r for r in MOCK_RIDES if r['status'] == 'pending'), None))
        }

        # First detect intent
        intent, entities, confidence = intent_processor.extract_intent(query, context)
        print(f"Detected intent: {intent} with confidence: {confidence}")

        # Handle ride acceptance/rejection intents
        if intent == "accept_ride" and context['has_pending_ride']:
            pending_ride = next((r for r in MOCK_RIDES if r['status'] == 'pending'), None)
            if pending_ride:
                accept_ride_response = accept_ride(pending_ride['id'])
                return jsonify({
                    'response': f"Accepting ride from {pending_ride['pickup_location']} to {pending_ride['dropoff_location']}",
                    'intent': intent,
                    'confidence': confidence,
                    'entities': entities
                })
        elif intent == "reject_ride" and context['has_pending_ride']:
            pending_ride = next((r for r in MOCK_RIDES if r['status'] == 'pending'), None)
            if pending_ride:
                MOCK_RIDES.remove(pending_ride)
                socketio.emit('ride_rejected', pending_ride)
                return jsonify({
                    'response': "Ride request rejected",
                    'intent': intent,
                    'confidence': confidence,
                    'entities': entities
                })

        # Prepare context for AI response
        intent_context = f"Intent: {intent}\nConfidence: {confidence}\nEntities: {entities}"
        
        # Send the query to Google AI Studio API with intent context
        headers = {
            'Content-Type': 'application/json',
        }
        payload = {
            'contents': [
                {
                    'parts': [
                        {
                            'text': f"""You are DAX, an AI assistant for drivers. 
                            Context: {intent_context}
                            Respond in a helpful, concise manner focused on the detected intent.
                            Always refer to yourself as DAX.
                            User query: {query}"""
                        }
                    ]
                }
            ]
        }

        print(f"Sending to Google AI API with intent context")
        response = requests.post(
            GOOGLE_AI_API_URL,
            params={"key": GOOGLE_AI_API_KEY},
            headers=headers,
            json=payload
        )
        print(f"Response status: {response.status_code}")

        if response.status_code == 200:
            api_response = response.json()
            # Extract the actual text response from Gemini API
            text_response = api_response['candidates'][0]['content']['parts'][0][
                'text'] if 'candidates' in api_response else "Sorry, I couldn't process that."
            
            # Return both the intent information and the response
            return jsonify({
                'response': text_response,
                'intent': intent,
                'confidence': confidence,
                'entities': entities
            })
        else:
            print(f"API error: {response.text}")
            return jsonify({'error': f'Google AI API error: {response.text}'}), response.status_code
    except Exception as e:
        print(f"Exception: {str(e)}")
        return jsonify({'error': f'Error processing query: {str(e)}'}), 500

# Ride Management API Endpoints
@app.route('/api/rides', methods=['GET'])
def get_rides():
    return jsonify(MOCK_RIDES)

@app.route('/api/rides/active', methods=['GET'])
def get_active_ride():
    global active_ride
    return jsonify(active_ride) if active_ride else jsonify({"message": "No active ride"})

@app.route('/api/rides/accept', methods=['POST'])
def accept_ride(ride_id=None):
    global active_ride
    if active_ride:
        return jsonify({"error": "Already have an active ride"}), 400
    
    # Handle both direct ride_id parameter and JSON request
    if ride_id is None:
        ride_id = request.json.get('ride_id')
    
    ride = next((r for r in MOCK_RIDES if r['id'] == ride_id), None)
    if not ride:
        return jsonify({"error": "Ride not found"}), 404
    
    # Get navigation details from Google Maps
    try:
        route_details = maps.get_route_details(
            "Current Location",  # This would be actual driver location in production
            ride['pickup_location']
        )
        
        if route_details['status'] == 'success':
            ride['route_details'] = route_details
            # Get navigation URL for pickup location (using mock coordinates for demo)
            pickup_coords = MOCK_DESTINATIONS[0]['coordinates']  # Using KLCC coords as example
            ride['navigation_url'] = maps.get_navigation_url((pickup_coords['lat'], pickup_coords['lng']))
        else:
            print(f"Google Maps route calculation error: {route_details.get('message')}")
    except Exception as e:
        print(f"Error getting Waze navigation: {str(e)}")
    
    ride['status'] = 'accepted'
    active_ride = ride
    
    # Emit ride update with navigation details and voice prompt
    socketio.emit('ride_status_update', {
        **ride,
        'voice_prompt': f"Ride accepted. Navigating to pickup at {ride['pickup_location']}",
        'navigation_details': {
            'pickup': ride.get('route_details', {}),
            'navigation_url': ride.get('navigation_url', '')
        }
    })
    
    return jsonify(ride)

@app.route('/api/rides/complete', methods=['POST'])
def complete_ride():
    global active_ride
    if not active_ride:
        return jsonify({"error": "No active ride"}), 400
    
    active_ride['status'] = 'completed'
    completed_ride = active_ride
    active_ride = None
    socketio.emit('ride_completed', completed_ride)
    return jsonify(completed_ride)

# Destination and Navigation API Endpoints
@app.route('/api/destinations', methods=['GET'])
def get_destinations():
    return jsonify(MOCK_DESTINATIONS)

@app.route('/api/busy-areas', methods=['GET'])
def get_busy_areas():
    try:
        busy_areas = maps.get_busy_areas(CENTRAL_KL)
        return jsonify(busy_areas)
    except Exception as e:
        print(f"Error getting busy areas: {str(e)}")
        return jsonify([])

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connection_response', {'data': 'Connected'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

def generate_mock_rides():
    """Background task to generate mock ride requests"""
    while True:
        if not active_ride:
            new_ride = {
                "id": f"R{random.randint(100, 999)}",
                "passenger_name": f"Passenger {random.randint(1, 100)}",
                "pickup_location": random.choice(["KLCC", "KL Sentral", "Bukit Bintang", "Pavilion"]),
                "dropoff_location": random.choice(["Mid Valley", "Bangsar", "Petaling Jaya", "Subang Jaya"]),
                "status": "pending",
                "estimated_fare": round(random.uniform(10, 50), 2),
                "distance": f"{round(random.uniform(1, 15), 1)} km",
                "estimated_time": f"{random.randint(5, 45)} mins"
            }
            MOCK_RIDES.append(new_ride)
            # Emit with voice prompt
            socketio.emit('new_ride_available', {
                **new_ride,
                'voice_prompt': f"New ride request from {new_ride['pickup_location']} to {new_ride['dropoff_location']}. Say accept or reject."
            })
        time.sleep(random.randint(30, 60))  # Generate new ride every 30-60 seconds

def update_busy_areas():
    """Background task to update busy areas using Google Maps Places API"""
    while True:
        try:
            # Get busy areas from Google Maps
            busy_areas = maps.get_busy_areas(CENTRAL_KL)
            if busy_areas:
                socketio.emit('busy_areas_update', busy_areas)
            time.sleep(300)  # Update every 5 minutes
        except Exception as e:
            print(f"Error updating busy areas: {str(e)}")
            time.sleep(60)  # Retry after 1 minute on error

if __name__ == '__main__':
    # Start background tasks
    ride_generator = threading.Thread(target=generate_mock_rides, daemon=True)
    busy_areas_updater = threading.Thread(target=update_busy_areas, daemon=True)
    ride_generator.start()
    busy_areas_updater.start()
    
    # Run the app with SocketIO
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
