import os
import requests
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app with correct folders
app = Flask(__name__, template_folder='templates')

# Google AI Studio API key
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


@app.route('/process_query', methods=['POST'])
def process_query():
    try:
        data = request.json
        if not data or 'query' not in data:
            return jsonify({'error': 'No query provided'}), 400

        query = data['query']
        print(f"Received query: {query}")

        # Send the query to Google AI Studio API
        headers = {
            'Content-Type': 'application/json',
        }
        payload = {
            'contents': [
                {
                    'parts': [
                        {
                            'text': f"You are DAX, an AI assistant for drivers. You should respond in a helpful, concise manner and always refer to yourself as DAX. User query: {query}"
                        }
                    ]
                }
            ]
        }

        print(f"Sending to Google AI API")
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
            print(f"AI response: {text_response}")
            return jsonify({'response': text_response})
        else:
            print(f"API error: {response.text}")
            return jsonify({'error': f'Google AI API error: {response.text}'}), response.status_code
    except Exception as e:
        print(f"Exception: {str(e)}")
        return jsonify({'error': f'Error processing query: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)