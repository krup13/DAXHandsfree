from NoiseSupressionModule import NoiseSuppressionModule
from MultiDialectSpeechRecognizer import MultiDialectSpeechRecognizer
from DriverIntentProcessor import DriverIntentProcessor
from DriverAssistant import DriverAssistant
from ResponseGenerator import ResponseGenerator
import google.generativeai as genai
import os
from typing import Tuple, Dict, Any


class DAXAssistantController:
    def __init__(self):
        """
        Main controller that coordinates all modules with Google AI integration
        """
        print("Initializing DAX Assistant components with Google AI...")
        
        # Initialize Google AI
        GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        genai.configure(api_key=GOOGLE_API_KEY)
        
        # Initialize Google AI model
        self.model = genai.GenerativeModel('gemini-pro')
        self.chat = self.model.start_chat(history=[])
        self.noise_suppressor = NoiseSuppressionModule()
        self.speech_recognizer = MultiDialectSpeechRecognizer()
        self.intent_processor = DriverIntentProcessor()
        self.driver_assistant = DriverAssistant()
        self.response_generator = ResponseGenerator()

        # Initialize default driver context
        self.driver_context = {
            "location": "downtown",
            "current_earnings": 75.50,
            "daily_goal": 150.00,
            "earnings_percentage": 50,  # percent of daily goal
            "shift_duration": 4.5,  # hours
            "current_traffic": "moderate",
            "rides_completed": 8,
            "next_destination": "airport",
            "weather": "clear"
        }

        print("DAX Assistant Controller initialized successfully")

    def process_command(self, audio_data=None, audio_file=None):
        """
        Process voice command end-to-end
        - From raw audio to spoken response

        Parameters:
        - audio_data: Raw audio data (numpy array)
        - audio_file: Audio file object from request

        Returns:
        - Response text
        - Processing steps and results
        """
        # For tracking the processing pipeline
        processing_steps = {}

        try:
            # Step 1: Process input audio
            if audio_data is not None:
                # Clean the audio
                processed_audio = self.noise_suppressor.process_audio(audio_data)
                processing_steps["noise_reduction"] = "Completed"

            elif audio_file is not None:
                # Save the uploaded file to a temporary file
                import tempfile
                import os
                from werkzeug.utils import secure_filename

                # Check if file has an allowed extension
                allowed_extensions = {'wav', 'aiff', 'flac'}
                filename = secure_filename(audio_file.filename)
                if '.' in filename and filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
                    return "Unsupported audio format. Please use WAV, AIFF, or FLAC.", {
                        "error": "Unsupported audio format"}

                temp_dir = tempfile.gettempdir()
                temp_path = os.path.join(temp_dir, "temp_audio.wav")

                try:
                    audio_file.save(temp_path)
                    print(f"Audio file saved to: {temp_path}")

                    # Use the temporary file for speech recognition
                    import speech_recognition as sr
                    recognizer = sr.Recognizer()

                    with sr.AudioFile(temp_path) as source:
                        print("Reading audio file...")
                        audio_data = recognizer.record(source)
                        print("Audio file processed successfully")

                    # Clean up the temporary file
                    os.remove(temp_path)

                    processing_steps["audio_processing"] = "File processed successfully"
                except Exception as e:
                    error_msg = f"Error processing audio file: {str(e)}"
                    print(error_msg)
                    return f"Error processing audio: {str(e)}", {"error": error_msg}
            else:
                return "No audio input provided", {"error": "No audio input"}

            # Step 2: Speech to text
            text, confidence = self.speech_recognizer.recognize(audio_data)
            processing_steps["speech_recognition"] = {"text": text, "confidence": confidence}

            # Step 3: Handle low confidence
            if confidence < 0.4:
                response = "I didn't quite catch that. Could you please repeat?"
                processing_steps["final_response"] = response
                return response, processing_steps

            # Step 4: Extract intent
            intent, entities, intent_confidence = self.intent_processor.extract_intent(
                text, context=self.driver_context
            )
            processing_steps["intent_processing"] = {
                "intent": intent,
                "entities": entities,
                "confidence": intent_confidence
            }

            # Step 5: Generate response
            response_text = self.driver_assistant.process_request(
                intent, entities, self.driver_context
            )
            processing_steps["assistant_response"] = response_text

            # Step 6: Generate AI response
            # Prepare context for AI
            ai_context = f"""
            Driver Context:
            - Location: {self.driver_context['location']}
            - Earnings: ${self.driver_context['current_earnings']} (Goal: ${self.driver_context['daily_goal']})
            - Shift Duration: {self.driver_context['shift_duration']} hours
            - Traffic: {self.driver_context['current_traffic']}
            
            User Intent: {intent}
            Detected Entities: {entities}
            """
            
            # Get AI response
            ai_response = self.chat.send_message(
                f"{ai_context}\n\nUser said: {text}\n\nRespond naturally as a helpful driving assistant.",
                stream=True
            )
            
            # Process streamed response
            final_response = ""
            for chunk in ai_response:
                if chunk.text:
                    final_response += chunk.text
            
            processing_steps["ai_response"] = final_response
            
            # Convert to speech with appropriate urgency
            urgency = "high" if intent == "help" else "normal"
            final_audio = self.response_generator.generate_response(final_response, urgency)
            processing_steps["final_response"] = final_response

            return final_audio, processing_steps

        except Exception as e:
            error_msg = f"Error processing command: {str(e)}"
            print(error_msg)
            return "Sorry, I encountered an error processing your request.", {"error": error_msg}

    def update_context(self, new_context_data):
        """
        Update driver context with new information

        Parameters:
        - new_context_data: Dictionary of context values to update
        """
        if new_context_data and isinstance(new_context_data, dict):
            self.driver_context.update(new_context_data)
            print(f"Context updated: {new_context_data.keys()}")
