from WazeRouteCalculator import WazeRouteCalculator
import logging

class WazeIntegration:
    def __init__(self):
        """
        Initialize Waze integration for navigation
        - Handles route calculations
        - Provides real-time traffic updates
        - Manages navigation instructions
        """
        logging.getLogger("WazeRouteCalculator").setLevel(logging.ERROR)
        self.region = 'MY'  # Malaysia region
        print("Waze Integration initialized")

    def get_route_details(self, start_address, end_address):
        """
        Get route details between two locations
        
        Parameters:
        - start_address: Starting location address
        - end_address: Destination address
        
        Returns:
        - Dictionary containing route details (distance, time, instructions)
        """
        try:
            # Calculate route
            route = WazeRouteCalculator.WazeRouteCalculator(
                start_address, 
                end_address,
                region=self.region
            )
            
            # Get route info
            route_time, route_distance = route.calc_route_info()
            
            return {
                'distance': round(route_distance, 2),  # km
                'duration': round(route_time, 2),      # minutes
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
        Get Waze navigation URL for the destination
        
        Parameters:
        - destination_coords: Tuple of (latitude, longitude)
        
        Returns:
        - Waze navigation URL
        """
        lat, lon = destination_coords
        return f"https://www.waze.com/ul?ll={lat}%2C{lon}&navigate=yes"

    def get_live_traffic(self, route_coords):
        """
        Get live traffic information for a route
        
        Parameters:
        - route_coords: List of coordinate tuples [(lat1,lon1), (lat2,lon2),...]
        
        Returns:
        - Dictionary containing traffic info
        """
        try:
            # Initialize route calculator with first and last points
            start = f"{route_coords[0][0]},{route_coords[0][1]}"
            end = f"{route_coords[-1][0]},{route_coords[-1][1]}"
            
            route = WazeRouteCalculator.WazeRouteCalculator(
                start, 
                end,
                region=self.region
            )
            
            # Get real-time traffic info
            route_time, route_distance = route.calc_route_info()
            
            return {
                'current_time': route_time,
                'regular_time': route_time * 0.7,  # Estimated regular time without traffic
                'traffic_intensity': 'heavy' if route_time > route_distance * 2 else 'moderate',
                'status': 'success'
            }
        except Exception as e:
            print(f"Error getting traffic info: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
