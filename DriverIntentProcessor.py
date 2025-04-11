class DriverIntentProcessor:
    def __init__(self):
        """
        Process driver intents and queries
        - Specialized for driver vocabulary and needs
        - Context-aware processing for partial inputs
        """
        # Define intent categories and keywords
        self.intent_keywords = {
            "earnings": ["earn", "money", "income", "how much", "today", "week", "earnings", "made", "profit",
                         "revenue"],
            "navigation": ["go", "route", "direction", "navigate", "turn", "where", "take me", "path", "fastest",
                           "quickest"],
            "hotspot": ["busy", "customer", "hotspot", "demand", "area", "where to go", "passengers", "pickup",
                        "riders"],
            "break": ["rest", "stop", "break", "tired", "pause", "coffee", "eat", "lunch", "bathroom", "toilet"],
            "help": ["help", "support", "assist", "emergency", "problem", "issue", "trouble", "stuck", "accident"]
        }

        print("Driver Intent Processor initialized")

    def extract_intent(self, text, context=None):
        """
        Extract intent from recognized text
        - Uses context from current ride status
        - Handles incomplete commands

        Parameters:
        - text: Recognized speech text
        - context: Current driver context (location, status, etc.)

        Returns:
        - intent: Classified intent
        - entities: Extracted information
        - confidence: Confidence score
        """
        if not text or len(text.strip()) == 0:
            return "unknown", {}, 0.0

        # Normalize text
        text = text.lower().strip()
        words = text.split()

        # Score each intent based on keyword matches
        intent_scores = {}
        for intent, keywords in self.intent_keywords.items():
            # Count matching keywords
            score = 0
            for keyword in keywords:
                if keyword in text or any(keyword in word for word in words):
                    score += 1

            # Weight longer multi-word keyword matches higher
            for keyword in keywords:
                if " " in keyword and keyword in text:
                    score += 1  # Additional point for multi-word matches

            intent_scores[intent] = score

        # Factor in context if available
        if context:
            # Example: If driver has been active for a long time, increase likelihood of "break" intent
            if context.get("shift_duration", 0) > 4:
                intent_scores["break"] = intent_scores.get("break", 0) + 0.5

            # If earnings are below target, increase likelihood of "hotspot" and "earnings" intents
            if context.get("earnings_percentage", 100) < 70:
                intent_scores["hotspot"] = intent_scores.get("hotspot", 0) + 0.5
                intent_scores["earnings"] = intent_scores.get("earnings", 0) + 0.5

        # Get highest scoring intent
        if any(intent_scores.values()):
            max_intent = max(intent_scores, key=intent_scores.get)
            max_score = intent_scores[max_intent]
            confidence = min(max_score / 3, 1.0)  # Normalize confidence
        else:
            max_intent = "unknown"
            confidence = 0.0

        # Extract basic entities based on intent
        entities = self._extract_entities(text, max_intent)

        print(f"Intent extracted: {max_intent} (confidence: {confidence:.2f})")
        return max_intent, entities, confidence

    def _extract_entities(self, text, intent):
        """Extract relevant entities based on intent"""
        entities = {}

        if intent == "navigation":
            # Look for location mentions
            location_indicators = ["to", "toward", "near", "at", "from"]
            for indicator in location_indicators:
                if indicator in text.split():
                    idx = text.split().index(indicator)
                    if idx + 1 < len(text.split()):
                        # Simple extraction - in a real system this would be more sophisticated
                        location = " ".join(text.split()[idx + 1:idx + 3])
                        entities["destination"] = location
                        break

        elif intent == "earnings":
            # Look for time period
            time_indicators = ["today", "this week", "this month", "yesterday", "last week"]
            for period in time_indicators:
                if period in text:
                    entities["time_period"] = period
                    break

        return entities