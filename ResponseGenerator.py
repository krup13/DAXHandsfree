import pyttsx3


class ResponseGenerator:
    def __init__(self):
        """
        Generate clear voice responses
        - Optimized for in-vehicle audio playback
        - Prioritizes clarity and brevity
        """
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
            print("Response Generator initialized successfully")

        except Exception as e:
            print(f"Warning: TTS initialization failed: {str(e)}")
            self.is_initialized = False

    def generate_response(self, response_text, urgency="normal"):
        """
        Convert response data to speech
        - Adjusts speech rate based on urgency
        - Emphasizes key information

        Parameters:
        - response_text: Text to convert to speech
        - urgency: Priority level ("normal", "high")

        Returns:
        - Response text (would return audio data in full implementation)
        """
        if not response_text:
            return ""

        # Format the text for better speech clarity
        formatted_text = self._format_for_speech(response_text)

        # Adjust properties based on urgency
        if self.is_initialized:
            if urgency == "high":
                self.engine.setProperty('rate', 170)  # Slightly faster
                self.engine.setProperty('volume', 1.0)  # Full volume
            else:
                self.engine.setProperty('rate', 150)  # Normal speed
                self.engine.setProperty('volume', 0.9)  # Standard volume

            try:
                # For hackathon, just play the audio directly
                self.engine.say(formatted_text)
                self.engine.runAndWait()
            except Exception as e:
                print(f"TTS playback error: {str(e)}")

        print(f"Response generated: {formatted_text}")
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