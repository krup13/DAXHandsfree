import googlemaps
import os
from datetime import datetime
from dotenv import load_dotenv

class GoogleMapsIntegration:
    def __init__(self):
        """
        Initialize Google Maps integration for navigation and location services
        - Handles route calculations
        - Provides real-time traffic updates
        - Identifies busy areas using Places API
        - Manages navigation instructions
        """
        load_dotenv()
        self.api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        self.region = 'MY'  # Malaysia region
        
        try:
            if not self.api_key:
                print("Warning: Google Maps API key not found, using mock data")
                self.client = None
            else:
                self.client = googlemaps.Client(key=self.api_key)
                print("Google Maps Integration initialized with API key")
        except ValueError as e:
            print(f"Warning: Invalid API key ({str(e)}), using mock data")
            self.client = None

    def get_mock_route_details(self, start_address, end_address):
        """Mock route details for testing"""
        return {
            'distance': 5.2,  # km
            'duration': 15,   # minutes
            'traffic_duration': 20,  # minutes
            'steps': [
                "Head north on Jalan Ampang",
                "Turn right onto Jalan P Ramlee",
                "Continue onto Jalan Raja Chulan"
            ],
            'status': 'success'
        }

    def get_route_details(self, start_address, end_address):
        """
        Get route details between two locations
        
        Parameters:
        - start_address: Starting location address
        - end_address: Destination address
        
        Returns:
        - Dictionary containing route details (distance, time, instructions)
        """
        # Use mock data if client is not available
        if not self.client:
            return self.get_mock_route_details(start_address, end_address)

        try:
            # Request directions from API
            directions = self.client.directions(
                start_address,
                end_address,
                region=self.region,
                departure_time=datetime.now()
            )

            if not directions:
                return {
                    'status': 'error',
                    'message': 'No route found'
                }

            route = directions[0]
            leg = route['legs'][0]

            return {
                'distance': leg['distance']['value'] / 1000,  # Convert meters to km
                'duration': leg['duration']['value'] / 60,    # Convert seconds to minutes
                'traffic_duration': leg.get('duration_in_traffic', {}).get('value', 0) / 60 if 'duration_in_traffic' in leg else None,
                'steps': [step['html_instructions'] for step in leg['steps']],
                'status': 'success'
            }
        except Exception as e:
            print(f"Error calculating route: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def get_navigation_url(self, destination_coords):
        """
        Get Google Maps navigation URL for the destination
        
        Parameters:
        - destination_coords: Tuple of (latitude, longitude)
        
        Returns:
        - Google Maps navigation URL
        """
        lat, lon = destination_coords
        return f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}&travelmode=driving"

    def get_live_traffic(self, route_coords):
        """
        Get live traffic information for a route
        
        Parameters:
        - route_coords: List of coordinate tuples [(lat1,lon1), (lat2,lon2),...]
        
        Returns:
        - Dictionary containing traffic info
        """
        try:
            # Get directions between first and last points with traffic data
            start = f"{route_coords[0][0]},{route_coords[0][1]}"
            end = f"{route_coords[-1][0]},{route_coords[-1][1]}"
            
            directions = self.client.directions(
                start,
                end,
                departure_time=datetime.now()
            )

            if not directions:
                return {
                    'status': 'error',
                    'message': 'No route found'
                }

            leg = directions[0]['legs'][0]
            regular_duration = leg['duration']['value']
            traffic_duration = leg.get('duration_in_traffic', {}).get('value', regular_duration)

            # Calculate traffic intensity
            traffic_ratio = traffic_duration / regular_duration
            if traffic_ratio > 1.5:
                intensity = 'heavy'
            elif traffic_ratio > 1.2:
                intensity = 'moderate'
            else:
                intensity = 'light'

            return {
                'current_time': traffic_duration / 60,  # minutes
                'regular_time': regular_duration / 60,  # minutes
                'traffic_intensity': intensity,
                'status': 'success'
            }
        except Exception as e:
            print(f"Error getting traffic info: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def calculate_distance(self, point1, point2):
        """
        Calculate the distance between two points using Google Maps Distance Matrix API
        
        Parameters:
        - point1: Tuple of (latitude, longitude) for first point
        - point2: Tuple of (latitude, longitude) for second point
        
        Returns:
        - Distance in kilometers
        """
        try:
            # Convert coordinates to strings
            origin = f"{point1[0]},{point1[1]}"
            destination = f"{point2[0]},{point2[1]}"
            
            # Get distance matrix
            matrix = self.client.distance_matrix(
                origins=[origin],
                destinations=[destination],
                mode="driving",
                units="metric"
            )
            
            if matrix['status'] == 'OK':
                # Extract distance in kilometers
                distance = matrix['rows'][0]['elements'][0]['distance']['value'] / 1000
                return distance
            else:
                return float('inf')  # Return infinity if calculation fails
        except Exception as e:
            print(f"Error calculating distance: {str(e)}")
            return float('inf')

    def get_mock_busy_areas(self, location):
        """Mock busy areas data for testing"""
        return [
            {
                'id': 'place1',
                'name': 'KLCC',
                'address': 'Kuala Lumpur City Centre',
                'type': 'shopping mall',
                'demand_level': 'high',
                'surge_multiplier': 1.5,
                'coordinates': {
                    'lat': 3.1577,
                    'lng': 101.7114
                }
            },
            {
                'id': 'place2',
                'name': 'KL Sentral',
                'address': 'KL Sentral, 50470 Kuala Lumpur',
                'type': 'train station',
                'demand_level': 'medium',
                'surge_multiplier': 1.2,
                'coordinates': {
                    'lat': 3.1340,
                    'lng': 101.6860
                }
            },
            {
                'id': 'place3',
                'name': 'Pavilion',
                'address': 'Bukit Bintang, Kuala Lumpur',
                'type': 'shopping mall',
                'demand_level': 'high',
                'surge_multiplier': 1.5,
                'coordinates': {
                    'lat': 3.1494,
                    'lng': 101.7131
                }
            }
        ]

    def get_busy_areas(self, location, radius=5000):
        """
        Identify busy areas with high demand using Places API
        
        Parameters:
        - location: Tuple of (latitude, longitude) for center point
        - radius: Search radius in meters (default 5km)
        
        Returns:
        - List of busy areas with demand levels
        """
        # Use mock data if client is not available
        if not self.client:
            return self.get_mock_busy_areas(location)

        try:
            # Search for places using Places API
            keywords = ['shopping mall', 'train station', 'airport', 'business district']
            busy_areas = []

            for keyword in keywords:
                places = self.client.places_nearby(
                    location=location,
                    radius=radius,
                    keyword=keyword
                )

                if places.get('results'):
                    for place in places['results']:
                        # Get place details for more information
                        details = self.client.place(place['place_id'])['result']
                        
                        # Use rating and user_ratings_total to estimate demand
                        rating = details.get('rating', 0)
                        total_ratings = details.get('user_ratings_total', 0)
                        
                        # Calculate demand level based on ratings and popularity
                        if total_ratings > 1000 and rating > 4.0:
                            demand_level = 'high'
                            surge_multiplier = 1.5
                        elif total_ratings > 500 and rating > 3.5:
                            demand_level = 'medium'
                            surge_multiplier = 1.2
                        else:
                            demand_level = 'low'
                            surge_multiplier = 1.0

                        busy_areas.append({
                            'id': place['place_id'],
                            'name': place['name'],
                            'address': place.get('vicinity', ''),
                            'type': keyword,
                            'demand_level': demand_level,
                            'surge_multiplier': surge_multiplier,
                            'coordinates': {
                                'lat': place['geometry']['location']['lat'],
                                'lng': place['geometry']['location']['lng']
                            }
                        })

            return busy_areas
        except Exception as e:
            print(f"Error finding busy areas: {str(e)}")
            return []
