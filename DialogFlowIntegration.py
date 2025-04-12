from google.cloud import dialogflow_v2
import os
from dotenv import load_dotenv

class DialogFlowIntegration:
    def __init__(self):
        """Initialize DialogFlow client with project settings"""
        load_dotenv()
        self.project_id = os.getenv('DIALOGFLOW_PROJECT_ID')
        if not self.project_id:
            raise ValueError("DIALOGFLOW_PROJECT_ID environment variable is not set")
        
        self.session_client = dialogflow_v2.SessionsClient()
        self.language_code = "en"

    def detect_intent(self, text, session_id):
        """
        Detect intent from text using DialogFlow
        
        Parameters:
        - text: The input text to analyze
        - session_id: Unique session identifier for context management
        
        Returns:
        - intent: Detected intent name
        - entities: Extracted parameters/entities
        - confidence: Intent detection confidence score
        """
        try:
            session = self.session_client.session_path(self.project_id, session_id)
            text_input = dialogflow_v2.TextInput(text=text, language_code=self.language_code)
            query_input = dialogflow_v2.QueryInput(text=text_input)

            response = self.session_client.detect_intent(
                request={"session": session, "query_input": query_input}
            )

            result = response.query_result
            
            # Extract intent and confidence
            intent = result.intent.display_name
            confidence = result.intent_detection_confidence

            # Extract entities from parameters
            entities = dict(result.parameters)

            print(f"DialogFlow Intent detected: {intent} (confidence: {confidence:.2f})")
            return intent, entities, confidence

        except Exception as e:
            print(f"Error detecting intent: {str(e)}")
            return "unknown", {}, 0.0

    def get_intent_response(self, text, session_id):
        """
        Get the full response from DialogFlow including fulfillment text
        
        Parameters:
        - text: The input text to analyze
        - session_id: Unique session identifier for context management
        
        Returns:
        - response_text: Fulfillment text from DialogFlow
        - intent: Detected intent name
        - entities: Extracted parameters/entities
        """
        try:
            session = self.session_client.session_path(self.project_id, session_id)
            text_input = dialogflow_v2.TextInput(text=text, language_code=self.language_code)
            query_input = dialogflow_v2.QueryInput(text=text_input)

            response = self.session_client.detect_intent(
                request={"session": session, "query_input": query_input}
            )

            result = response.query_result
            return (
                result.fulfillment_text,
                result.intent.display_name,
                dict(result.parameters)
            )

        except Exception as e:
            print(f"Error getting intent response: {str(e)}")
            return "I'm having trouble understanding that right now.", "unknown", {}
