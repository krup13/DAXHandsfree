import speech_recognition as sr


class MultiDialectSpeechRecognizer:
    def __init__(self, languages=["en-US", "en-SG", "ms-MY", "id-ID"]):
        """
        Speech recognition system tuned for Southeast Asian languages and dialects

        Parameters:
        - languages: List of language codes to attempt recognition with
        """
        self.recognizer = sr.Recognizer()
        self.languages = languages

        # Adjust sensitivity parameters
        self.recognizer.energy_threshold = 300  # Minimum audio energy to consider
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8  # Seconds of silence before considering the phrase complete

        print(f"Multi-Dialect Speech Recognizer initialized with languages: {languages}")

    def recognize(self, audio_data, language=None):
        """
        Convert processed audio to text

        Parameters:
        - audio_data: Audio data object from speech_recognition
        - language: Specific language to use (optional)

        Returns:
        - Recognized text and confidence score
        """
        if not audio_data:
            return "", 0.0

        try:
            # If language specified, use that
            if language and language in self.languages:
                text = self.recognizer.recognize_google(audio_data, language=language)
                return text, 0.8  # Estimated confidence

            # Try each language in sequence, use the first successful one
            for lang in self.languages:
                try:
                    text = self.recognizer.recognize_google(audio_data, language=lang)
                    return text, 0.75  # Slightly lower confidence for auto-detected language
                except:
                    continue

            # If all fail, try without specifying language
            text = self.recognizer.recognize_google(audio_data)
            return text, 0.7

        except sr.UnknownValueError:
            print("Speech Recognition could not understand audio")
            return "", 0.0
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            return "", 0.0
        except Exception as e:
            print(f"Error in speech recognition: {str(e)}")
            return "", 0.0