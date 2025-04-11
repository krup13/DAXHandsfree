class DriverAssistant:
    def __init__(self):
        """
        Core assistant logic for driver support
        - Trip optimization
        - Earnings management
        - Safety alerts
        - Ride coordination
        """
        # Initialize default context
        self.default_context = {
            "location": "downtown",
            "current_earnings": 75.50,
            "daily_goal": 150.00,
            "shift_duration": 4.5,  # hours
            "current_traffic": "moderate",
            "rides_completed": 8,
            "next_destination": "airport",
            "weather": "clear"
        }

        print("Driver Assistant initialized")

    def process_request(self, intent, entities, driver_context=None):
        """
        Process driver request based on intent
        - Generates appropriate response or action

        Parameters:
        - intent: Classified intent
        - entities: Extracted information
        - driver_context: Current driver context (defaults used if None)

        Returns:
        - Response text
        """
        # Use default context if none provided
        if not driver_context:
            driver_context = self.default_context

        # Process based on intent
        if intent == "earnings":
            return self.handle_earnings_query(entities, driver_context)

        elif intent == "navigation":
            return self.handle_navigation(entities, driver_context)

        elif intent == "hotspot":
            return self.suggest_earning_hotspots(driver_context)

        elif intent == "break":
            return self.suggest_break(driver_context)

        elif intent == "help":
            return self.provide_assistance(entities, driver_context)

        else:
            return "I didn't quite understand. Could you rephrase your request?"

    def handle_earnings_query(self, entities, context):
        """Handle earnings-related queries"""
        time_period = entities.get("time_period", "today")

        if time_period == "today":
            earnings = context.get("current_earnings", 0)
            goal = context.get("daily_goal", 100)
            percentage = min(int((earnings / goal) * 100), 100)

            response = f"You've earned ${earnings:.2f} today, which is {percentage}% of your daily goal. "

            # Add personalized recommendation
            if percentage < 50:
                response += "To meet your target, I recommend heading to the city center where demand is high right now."
            elif percentage < 80:
                response += "You're making good progress! Another 2-3 hours should help you reach your goal."
            else:
                response += "Great work! You're on track to exceed your daily target."

        elif "week" in time_period:
            # Simulate weekly earnings (would come from actual data)
            weekly_earnings = context.get("current_earnings", 0) * 5.5  # Simplified calculation
            response = f"This week, you've earned approximately ${weekly_earnings:.2f}. Your performance is above average compared to other drivers in your area."

        else:
            response = f"You're currently earning at a rate of ${context.get('current_earnings', 0) / context.get('shift_duration', 4):.2f} per hour."

        return response

    def handle_navigation(self, entities, context):
        """Handle navigation requests"""
        destination = entities.get("destination", context.get("next_destination", "your destination"))
        current_location = context.get("location", "current location")
        traffic = context.get("current_traffic", "moderate")

        # Generate appropriate navigation instructions
        if traffic == "heavy":
            response = f"Taking you to {destination} via an alternate route to avoid heavy traffic. Continue straight for 2 kilometers, then turn right at the next major intersection."
        else:
            response = f"Navigating from {current_location} to {destination}. Estimated arrival time is 15 minutes. Proceed straight and prepare to turn left in 500 meters."

        # Add weather-based advice if available
        if context.get("weather") == "rain":
            response += " Drive carefully as roads are wet due to rain."

        return response

    def suggest_earning_hotspots(self, context):
        """Suggest high-demand areas nearby"""
        time_of_day = "evening"  # Would be actual time in real implementation
        current_location = context.get("location", "downtown")

        hotspots = {
            "morning": ["airport", "business district", "train stations"],
            "afternoon": ["shopping malls", "tourist attractions", "university area"],
            "evening": ["entertainment district", "restaurant row", "hotel zone"],
            "night": ["nightlife area", "residential zones", "airport"]
        }

        suggested_spots = hotspots.get(time_of_day, ["downtown", "airport"])
        primary_suggestion = suggested_spots[0]

        response = f"Based on current demand patterns, {primary_suggestion} shows high activity right now. "
        response += f"Head there for increased ride opportunities. I also see rising demand near {suggested_spots[1]}."

        # Add personalized recommendation
        if context.get("current_earnings", 0) < 50:
            response += " Focusing on these areas could help boost your earnings significantly today."

        return response

    def suggest_break(self, context):
        """Provide break recommendations"""
        shift_duration = context.get("shift_duration", 4)
        rides_completed = context.get("rides_completed", 5)

        if shift_duration > 4:
            response = f"You've been driving for {shift_duration:.1f} hours without a substantial break. Consider taking a 15-minute rest now to stay alert."
            response += " There's a rest area 2 kilometers ahead on your route."
        elif rides_completed > 10:
            response = f"You've completed {rides_completed} rides so far. A quick 10-minute break could help you stay refreshed for the remaining shifts."
        else:
            response = "Based on your driving pattern, now would be a good time for a short break. This can help maintain your alertness and safety."

        return response

    def provide_assistance(self, entities, context):
        """Provide help and assistance"""
        response = "I'm here to help. What specific assistance do you need? You can ask about navigation, earnings, finding passengers, or taking a break."

        # If context suggests an issue, provide targeted help
        if context.get("current_traffic") == "heavy":
            response = "I notice you're in heavy traffic. Would you like me to find an alternate route to your destination?"

        return response