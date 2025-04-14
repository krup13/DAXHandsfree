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
from ResponseGenerator import ResponseGenerator

# Load environment variables
load_dotenv()

# Initialize Flask app and components
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['JSON_SORT_KEYS'] = False  # Prevent JSON sorting for faster responses
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False  # Disable pretty printing for faster responses
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
maps = GoogleMapsIntegration()
response_generator = ResponseGenerator()

# Cache for API responses
cache = {
    'busy_areas': {
        'data': None,
        'last_updated': None,
        'ttl': 300  # 5 minutes cache
    },
    'earnings': {
        'data': None,
        'last_updated': None,
        'ttl': 60  # 1 minute cache
    },
    'profile': {
        'data': None,
        'last_updated': None,
        'ttl': 3600  # 1 hour cache
    },
    'destinations': {
        'data': None,
        'last_updated': None,
        'ttl': 3600  # 1 hour cache
    }
}

# Preload common data
def preload_cache():
    """Preload cache with common data to avoid initial delays"""
    try:
        # Preload earnings data
        cache['earnings']['data'] = {
            "today": {
                "amount": 150.00,
                "trips": 8,
                "hours": 6.5
            },
            "weekly": {
                "amount": 950.00,
                "trips": 45,
                "average_daily": 135.71
            }
        }
        cache['earnings']['last_updated'] = datetime.now()
        
        # Preload profile data
        cache['profile']['data'] = {
            "personal": {
                "name": "John Doe",
                "driver_id": "GD12345",
                "rating": 4.8,
                "total_trips": 1234,
                "member_since": "January 2023"
            },
            "vehicle": {
                "type": "Sedan",
                "license_plate": "ABC 1234",
                "model": "Toyota Camry 2022"
            }
        }
        cache['profile']['last_updated'] = datetime.now()
        
        # Preload destinations
        cache['destinations']['data'] = MOCK_DESTINATIONS
        cache['destinations']['last_updated'] = datetime.now()
        
        print("Cache preloaded successfully")
    except Exception as e:
        print(f"Error preloading cache: {str(e)}")

# Lazy loading for voice responses
voice_enabled = True

# Greet on bootup - using a separate thread to avoid blocking
@app.before_first_request
def on_startup():
    def delayed_greeting():
        time.sleep(1)  # Delay greeting to allow UI to load first
        if voice_enabled:
            response_generator.generate_response("Hello! I'm DAX, your driving assistant. I'm ready to help you navigate and manage your rides.")
    
    # Preload cache data
    preload_cache()
    
    # Start greeting in background
    greeting_thread = threading.Thread(target=delayed_greeting)
    greeting_thread.daemon = True
    greeting_thread.start()

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
        print(f"Detected entities: {entities}")

        # Check for page navigation intents
        if "page" in entities:
            page_url = entities["page"]
            response_text = f"Navigating to {intent} page"
            response_generator.generate_response(response_text)
            return jsonify({
                'response': response_text,
                'intent': intent,
                'confidence': confidence,
                'entities': entities,
                'navigate_to': page_url
            })
        
        # Handle different intents
        if intent == "accept_ride" and context['has_pending_ride']:
            pending_ride = next((r for r in MOCK_RIDES if r['status'] == 'pending'), None)
            if pending_ride:
                accept_ride_response = accept_ride(pending_ride['id'])
                response_text = f"Accepting ride from {pending_ride['pickup_location']} to {pending_ride['dropoff_location']}"
                response_generator.generate_response(response_text)
                return jsonify({
                    'response': response_text,
                    'intent': intent,
                    'confidence': confidence,
                    'entities': entities
                })
        elif intent == "reject_ride" and context['has_pending_ride']:
            pending_ride = next((r for r in MOCK_RIDES if r['status'] == 'pending'), None)
            if pending_ride:
                MOCK_RIDES.remove(pending_ride)
                socketio.emit('ride_rejected', pending_ride)
                response_text = "Ride request rejected"
                response_generator.generate_response(response_text)
                return jsonify({
                    'response': response_text,
                    'intent': intent,
                    'confidence': confidence,
                    'entities': entities
                })
        elif intent == "earnings":
            current_time = datetime.now()
            
            # Check cache first
            if (cache['earnings']['data'] is not None and 
                cache['earnings']['last_updated'] is not None and
                (current_time - cache['earnings']['last_updated']).seconds < cache['earnings']['ttl']):
                earnings = cache['earnings']['data']
            else:
                # Mock earnings data
                earnings = {
                    "today": {
                        "amount": 150.00,
                        "trips": 8,
                        "hours": 6.5
                    },
                    "weekly": {
                        "amount": 950.00,
                        "trips": 45,
                        "average_daily": 135.71
                    }
                }
                # Update cache
                cache['earnings']['data'] = earnings
                cache['earnings']['last_updated'] = current_time
            
            response_text = f"Today you've earned {earnings['today']['amount']} dollars from {earnings['today']['trips']} trips over {earnings['today']['hours']} hours. Your weekly earnings are {earnings['weekly']['amount']} dollars."
            response_generator.generate_response(response_text)
            
            # If not already on earnings page, navigate there
            if "page" in entities:
                return jsonify({
                    'response': response_text,
                    'intent': intent,
                    'confidence': confidence,
                    'entities': entities,
                    'earnings': earnings,
                    'navigate_to': entities["page"]
                })
            else:
                return jsonify({
                    'response': response_text,
                    'intent': intent,
                    'confidence': confidence,
                    'entities': entities,
                    'earnings': earnings
                })
        elif intent == "navigation" or intent == "hotspot":
            current_time = datetime.now()
            current_location = (3.1390, 101.6869)  # KL coordinates
            
            # Check cache first
            if (cache['busy_areas']['data'] is not None and 
                cache['busy_areas']['last_updated'] is not None and
                (current_time - cache['busy_areas']['last_updated']).seconds < cache['busy_areas']['ttl']):
                sorted_areas = cache['busy_areas']['data']
            else:
                # Get busy areas sorted by distance from current location
                busy_areas = maps.get_busy_areas(current_location)
                sorted_areas = []
                
                for area in busy_areas:
                    area_location = (area['coordinates']['lat'], area['coordinates']['lng'])
                    area['distance'] = maps.calculate_distance(current_location, area_location)
                    sorted_areas.append(area)
                
                sorted_areas = sorted(sorted_areas, key=lambda x: x['distance'])
                
                # Update cache
                cache['busy_areas']['data'] = sorted_areas
                cache['busy_areas']['last_updated'] = current_time
            
            # Get top 3 areas
            top_areas = sorted_areas[:3]
            
            response_text = "The top three busy areas near you are: "
            for i, area in enumerate(top_areas, 1):
                response_text += f"{i}. {area['name']}, {area['distance']:.1f} kilometers away. "
            
            response_generator.generate_response(response_text)
            
            # If not already on navigation page, navigate there
            if "page" in entities:
                return jsonify({
                    'response': response_text,
                    'intent': intent,
                    'confidence': confidence,
                    'entities': entities,
                    'busy_areas': top_areas,
                    'navigate_to': entities["page"]
                })
            else:
                return jsonify({
                    'response': response_text,
                    'intent': intent,
                    'confidence': confidence,
                    'entities': entities,
                    'busy_areas': top_areas
                })
        elif intent == "profile":
            # Get profile data
            current_time = datetime.now()
            
            # Check cache first
            if (cache['profile']['data'] is not None and 
                cache['profile']['last_updated'] is not None and
                (current_time - cache['profile']['last_updated']).seconds < cache['profile']['ttl']):
                profile = cache['profile']['data']
            else:
                # Mock profile data
                profile = {
                    "personal": {
                        "name": "John Doe",
                        "driver_id": "GD12345",
                        "rating": 4.8,
                        "total_trips": 1234,
                        "member_since": "January 2023"
                    },
                    "vehicle": {
                        "type": "Sedan",
                        "license_plate": "ABC 1234",
                        "model": "Toyota Camry 2022"
                    }
                }
                # Update cache
                cache['profile']['data'] = profile
                cache['profile']['last_updated'] = current_time
            
            # Ensure the page entity is set for profile intent
            if "page" not in entities:
                entities["page"] = "/profile"
                
            response_text = f"Navigating to profile page. Your driver rating is {profile['personal']['rating']} stars with {profile['personal']['total_trips']} completed trips."
            response_generator.generate_response(response_text)
            
            print(f"Profile response - navigate_to: {entities['page']}")
            
            return jsonify({
                'response': response_text,
                'intent': intent,
                'confidence': confidence,
                'entities': entities,
                'profile': profile,
                'navigate_to': entities["page"]
            })
        elif intent == "chat":
            if "message" in entities:
                message = {
                    'sender': 'driver',
                    'message': entities['message'],
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'customer_name': active_ride['passenger_name'] if active_ride else "Customer"
                }
                chat_history.append(message)
                socketio.emit('new_chat_message', message)
                response_text = f"Message sent to {message['customer_name']}: {message['message']}"
                response_generator.generate_response(response_text)
                return jsonify({
                    'response': response_text,
                    'intent': intent,
                    'confidence': confidence,
                    'entities': entities,
                    'message': message
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
            
            # Generate voice response for the AI response
            response_generator.generate_response(text_response)
            
            # Return both the intent information and the response with voice flag
            return jsonify({
                'response': text_response,
                'intent': intent,
                'confidence': confidence,
                'entities': entities,
                'should_speak': True  # Flag to indicate the response should be spoken
            })
        else:
            print(f"API error: {response.text}")
            return jsonify({'error': f'Google AI API error: {response.text}'}), response.status_code
    except Exception as e:
        print(f"Exception: {str(e)}")
        return jsonify({'error': f'Error processing query: {str(e)}'}), 500

# Profile API Endpoints
@app.route('/api/profile', methods=['GET'])
def get_profile():
    # Mock profile data
    profile = {
        "personal": {
            "name": "John Doe",
            "driver_id": "GD12345",
            "rating": 4.8,
            "total_trips": 1234,
            "member_since": "January 2023"
        },
        "vehicle": {
            "type": "Sedan",
            "license_plate": "ABC 1234",
            "model": "Toyota Camry 2022"
        }
    }
    return jsonify(profile)

# Earnings API Endpoints
@app.route('/api/earnings', methods=['GET'])
def get_earnings():
    current_time = datetime.now()
    
    # Check cache first
    if (cache['earnings']['data'] is not None and 
        cache['earnings']['last_updated'] is not None and
        (current_time - cache['earnings']['last_updated']).seconds < cache['earnings']['ttl']):
        earnings = cache['earnings']['data']
    else:
        # Mock earnings data
        earnings = {
            "today": {
                "amount": 150.00,
                "trips": 8,
                "hours": 6.5
            },
            "weekly": {
                "amount": 950.00,
                "trips": 45,
                "average_daily": 135.71
            }
        }
        # Update cache
        cache['earnings']['data'] = earnings
        cache['earnings']['last_updated'] = current_time
    
    # Generate voice response for earnings
    earnings_text = f"Today you've earned {earnings['today']['amount']} dollars from {earnings['today']['trips']} trips over {earnings['today']['hours']} hours. Your weekly earnings are {earnings['weekly']['amount']} dollars."
    response_generator.generate_response(earnings_text)
    
    return jsonify(earnings)

@app.route('/api/earnings/history', methods=['GET'])
def get_earnings_history():
    # Mock customer history
    history = [
        {
            "name": "Sarah Chen",
            "pickup": "KL Sentral",
            "dropoff": "KLCC",
            "fare": 25.00,
            "rating": 5,
            "date": "Today 2:30 PM"
        },
        {
            "name": "Ahmad Razak",
            "pickup": "Bukit Bintang",
            "dropoff": "Pavilion",
            "fare": 15.00,
            "rating": 4,
            "date": "Today 11:45 AM"
        },
        {
            "name": "Michael Wong",
            "pickup": "Mid Valley",
            "dropoff": "Bangsar",
            "fare": 20.00,
            "rating": 5,
            "date": "Today 9:15 AM"
        }
    ]
    return jsonify(history)

# Navigation API Endpoints
@app.route('/api/navigation/nearby-busy', methods=['GET'])
def get_nearby_busy_areas():
    try:
        current_time = datetime.now()
        
        # Check cache first
        if (cache['busy_areas']['data'] is not None and 
            cache['busy_areas']['last_updated'] is not None and
            (current_time - cache['busy_areas']['last_updated']).seconds < cache['busy_areas']['ttl']):
            sorted_areas = cache['busy_areas']['data']
        else:
            # Get current location (mock for demo)
            current_location = (3.1390, 101.6869)  # KL coordinates
            
            # Get busy areas sorted by distance from current location
            busy_areas = maps.get_busy_areas(current_location)
            
            # Sort areas by distance from current location
            sorted_areas = []
            for area in busy_areas:
                area_location = (area['coordinates']['lat'], area['coordinates']['lng'])
                area['distance'] = maps.calculate_distance(current_location, area_location)
                sorted_areas.append(area)
            
            sorted_areas = sorted(sorted_areas, key=lambda x: x['distance'])
            
            # Update cache
            cache['busy_areas']['data'] = sorted_areas
            cache['busy_areas']['last_updated'] = current_time
        
        # Generate voice response for top 3 busy areas
        if sorted_areas:
            top_three = sorted_areas[:3]
            areas_text = "The top three busy areas near you are: "
            for i, area in enumerate(top_three, 1):
                areas_text += f"{i}. {area['name']}, {area['distance']:.1f} kilometers away. "
            response_generator.generate_response(areas_text)
        
        return jsonify(sorted_areas)
    except Exception as e:
        print(f"Error getting nearby busy areas: {str(e)}")
        return jsonify([])

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

# Chat functionality
chat_history = []

@app.route('/api/chat/send', methods=['POST'])
def send_chat_message():
    data = request.json
    if not data or 'message' not in data or 'customer_name' not in data:
        return jsonify({'error': 'Invalid request'}), 400
    
    message = {
        'sender': 'driver',
        'message': data['message'],
        'timestamp': datetime.now().strftime('%H:%M:%S'),
        'customer_name': data['customer_name']
    }
    chat_history.append(message)
    socketio.emit('new_chat_message', message)
    return jsonify(message)

@app.route('/api/chat/receive', methods=['POST'])
def receive_chat_message():
    data = request.json
    if not data or 'message' not in data or 'customer_name' not in data:
        return jsonify({'error': 'Invalid request'}), 400
    
    message = {
        'sender': 'customer',
        'message': data['message'],
        'timestamp': datetime.now().strftime('%H:%M:%S'),
        'customer_name': data['customer_name']
    }
    chat_history.append(message)
    # Generate voice response for customer message
    response_generator.generate_response(f"{message['customer_name']} says {message['message']}")
    socketio.emit('new_chat_message', message)
    return jsonify(message)

@app.route('/api/chat/history', methods=['GET'])
def get_chat_history():
    return jsonify(chat_history)

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
    # Initial delay to allow app to fully load
    time.sleep(10)
    
    while True:
        try:
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
            time.sleep(random.randint(60, 120))  # Reduced frequency - every 1-2 minutes
        except Exception as e:
            print(f"Error in mock ride generation: {str(e)}")
            time.sleep(60)  # Wait a minute before retrying

def update_busy_areas():
    """Background task to update busy areas using Google Maps Places API"""
    # Initial delay to allow app to fully load
    time.sleep(15)
    
    # Initial data load
    try:
        busy_areas = maps.get_busy_areas(CENTRAL_KL)
        if busy_areas:
            sorted_areas = []
            for area in busy_areas:
                area_location = (area['coordinates']['lat'], area['coordinates']['lng'])
                area['distance'] = maps.calculate_distance(CENTRAL_KL, area_location)
                sorted_areas.append(area)
            
            sorted_areas = sorted(sorted_areas, key=lambda x: x['distance'])
            
            # Update cache
            cache['busy_areas']['data'] = sorted_areas
            cache['busy_areas']['last_updated'] = datetime.now()
    except Exception as e:
        print(f"Error in initial busy areas load: {str(e)}")
    
    # Regular updates
    while True:
        try:
            current_time = datetime.now()
            
            # Only update if cache is expired or empty
            if (cache['busy_areas']['data'] is None or
                cache['busy_areas']['last_updated'] is None or
                (current_time - cache['busy_areas']['last_updated']).seconds >= cache['busy_areas']['ttl']):
                
                # Get busy areas from Google Maps
                busy_areas = maps.get_busy_areas(CENTRAL_KL)
                if busy_areas:
                    sorted_areas = []
                    for area in busy_areas:
                        area_location = (area['coordinates']['lat'], area['coordinates']['lng'])
                        area['distance'] = maps.calculate_distance(CENTRAL_KL, area_location)
                        sorted_areas.append(area)
                    
                    sorted_areas = sorted(sorted_areas, key=lambda x: x['distance'])
                    
                    # Update cache
                    cache['busy_areas']['data'] = sorted_areas
                    cache['busy_areas']['last_updated'] = current_time
                    
                    socketio.emit('busy_areas_update', sorted_areas)
            
            time.sleep(120)  # Reduced frequency - check every 2 minutes
        except Exception as e:
            print(f"Error updating busy areas: {str(e)}")
            time.sleep(60)  # Retry after 1 minute on error

# Toggle voice response
@app.route('/api/toggle-voice', methods=['POST'])
def toggle_voice():
    global voice_enabled
    data = request.json
    if data and 'enabled' in data:
        voice_enabled = data['enabled']
        return jsonify({'voice_enabled': voice_enabled})
    return jsonify({'error': 'Invalid request'}), 400

if __name__ == '__main__':
    # Preload cache
    preload_cache()
    
    # Start background tasks with lower priority
    ride_generator = threading.Thread(target=generate_mock_rides, daemon=True)
    busy_areas_updater = threading.Thread(target=update_busy_areas, daemon=True)
    ride_generator.start()
    busy_areas_updater.start()
    
    # Run the app with SocketIO
    socketio.run(app, debug=False, allow_unsafe_werkzeug=True)
