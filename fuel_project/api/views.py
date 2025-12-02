from rest_framework.views import APIView
from rest_framework.response import Response
from .utils import get_route, find_optimal_stops, haversine_distance

class RouteView(APIView):
    def get(self, request):
        start_location = request.query_params.get('start')
        finish_location = request.query_params.get('finish')
        
        if not start_location or not finish_location:
            return Response({"error": "Please provide start and finish coordinates (lon,lat)"}, status=400)

        route_path, distance_meters = get_route(start_location, finish_location)
        
        if not route_path:
            return Response({"error": "Could not find route"}, status=400)

        distance_miles = distance_meters * 0.000621371

        stops, fuel_cost = find_optimal_stops(route_path, distance_miles)

        return Response({
            "route_summary": {
                "total_distance_miles": round(distance_miles, 2),
                "total_fuel_cost": fuel_cost,
                "estimated_stops": len(stops)
            },
            "fuel_stops": stops,
            "route_geometry": route_path 
        })