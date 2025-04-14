import pyttsx3
import threading
import queue
import time


class ResponseGenerator:
    def __init__(self):
        """
        Generate clear voice responses
        - Optimized for in-vehicle audio playback
        - Prioritizes clarity and brevity
        - Uses background thread for non-blocking operation
        """
        self.speech_queue = queue.Queue()
        self.is_initialized = False
        self.is_speaking = False
        
        # Initialize TTS in a separate thread to avoid blocking
        self.init_thread = threading.Thread(target=self._initialize_tts)
        self.init_thread.daemon = True
        self.init_thread.start()
        
        # Start speech processing thread
        self.speech_thread = threading.Thread(target=self._process_speech_queue)
        self.speech_thread.daemon = True
        self.speech_thread.start()
        
        print("Response Generator initialized in background")

    def _initialize_tts(self):
        """Initialize TTS engine in background thread"""
        try:
            self.engine = pyttsx3.init()
            # Configure speech properties
            self.engine.setProperty('rate', 150)  # Speaking rate
            self.engine.setProperty('volume', 0.9)  # Volume (0-1)

            # Get available voices and set a clear voice
            voices = self.engine.getProperty('voices')
            if voices:
                # Try to use a clear, natural voice if available
                self.engine.setProperty('voice', voices[0].id)

            self.is_initialized = True
            print("TTS engine initialized successfully")

        except Exception as e:
            print(f"Warning: TTS initialization failed: {str(e)}")
            self.is_initialized = False

    def _process_speech_queue(self):
        """Process speech queue in background thread"""
        while True:
            try:
                # Wait for items in the queue
                if not self.speech_queue.empty():
                    text, urgency = self.speech_queue.get()
                    
                    # Only process if TTS is initialized
                    if self.is_initialized:
                        self.is_speaking = True
                        
                        # Adjust properties based on urgency
                        if urgency == "high":
                            self.engine.setProperty('rate', 170)  # Slightly faster
                            self.engine.setProperty('volume', 1.0)  # Full volume
                        else:
                            self.engine.setProperty('rate', 150)  # Normal speed
                            self.engine.setProperty('volume', 0.9)  # Standard volume
                        
                        try:
                            # Play the audio
                            self.engine.say(text)
                            self.engine.runAndWait()
                        except Exception as e:
                            print(f"TTS playback error: {str(e)}")
                        
                        self.is_speaking = False
                    
                    # Mark task as done
                    self.speech_queue.task_done()
                else:
                    # Sleep to avoid high CPU usage
                    time.sleep(0.1)
            except Exception as e:
                print(f"Speech queue processing error: {str(e)}")
                time.sleep(1)  # Wait before retrying

    def generate_response(self, response_text, urgency="normal"):
        """
        Convert response data to speech (non-blocking)
        - Adds speech to queue for background processing
        - Adjusts speech rate based on urgency
        - Emphasizes key information

        Parameters:
        - response_text: Text to convert to speech
        - urgency: Priority level ("normal", "high")

        Returns:
        - Response text
        """
        if not response_text:
            return ""

        # Format the text for better speech clarity
        formatted_text = self._format_for_speech(response_text)
        
        # Add to speech queue for background processing
        self.speech_queue.put((formatted_text, urgency))

        print(f"Response queued: {formatted_text}")
        return formatted_text

    def _format_for_speech(self, text):
        """Format text for better TTS clarity"""
        # Replace abbreviations
        replacements = {
            "GPS": "G P S",
            "ETA": "estimated time of arrival",
            "km": "kilometers",
            "min": "minutes",
            "$": "dollar"
        }

        formatted = text
        for orig, repl in replacements.items():
            formatted = formatted.replace(orig, repl)

        return formatted
        
    def is_busy(self):
        """Check if the speech engine is currently speaking"""
        return self.is_speaking
