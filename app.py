from flask import Flask, render_template, request, jsonify, Response
import speech_recognition as sr
from DAXAssistantController import DAXAssistantController
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
assistant = DAXAssistantController()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/process_audio', methods=['POST'])
def process_audio():
    """Process audio from the web interface"""
    if 'audio' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No audio file provided'
        })

    try:
        audio_file = request.files['audio']

        # Process the audio using our assistant
        response, processing_steps = assistant.process_command(audio_file=audio_file)

        # Return the response directly
        return jsonify({
            'success': True,
            'text': processing_steps.get('speech_recognition', {}).get('text', ''),
            'intent': processing_steps.get('intent_processing', {}).get('intent', 'unknown'),
            'confidence': processing_steps.get('intent_processing', {}).get('confidence', 0),
            'response': response,
            'processing_steps': processing_steps
        })

    except Exception as e:
        print(f"Error in processing audio: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/update_context', methods=['POST'])
def update_context():
    """Update the driver context"""
    try:
        context_data = request.json
        assistant.update_context(context_data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/test', methods=['GET'])
def test_assistant():
    """Simple test endpoint for verifying the assistant works"""
    try:
        test_response = {
            'noise_suppression': 'Module initialized',
            'speech_recognition': 'Module initialized',
            'intent_processor': 'Module initialized',
            'response_generator': 'Module initialized',
            'status': 'DAX Assistant ready'
        }
        return jsonify(test_response)
    except Exception as e:
        return jsonify({'error': str(e)})


if __name__ == '__main__':
    app.run(debug=True)
