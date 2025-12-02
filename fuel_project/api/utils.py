import requests
import polyline
import math
from django.conf import settings # Import settings
from .models import FuelStation

def get_route(start_coords, end_coords):
    """
    Fetch route from OpenRouteService. 
    start_coords: "lon,lat" string
    end_coords: "lon,lat" string
    """
    # DIRECTIONS Endpoint (Different from Geocoding endpoint)
    url = "https://api.openrouteservice.org/v2/directions/driving-car"
    
    # USE KEY FROM SETTINGS (Best Practice)
    headers = {
        'Authorization': settings.ORS_API_KEY,
        'Content-Type': 'application/json; charset=utf-8'
    }
    
    params = {
        'start': start_coords,
        'end': end_coords,
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # 1. Get the Geometry (The map line)
            # ORS returns coordinates in [lon, lat] format
            geometry = data['features'][0]['geometry']['coordinates']
            
            # Convert to [lat, lon] for our math functions if needed, 
            # but usually map frontends want [lat, lon] or [lon, lat]. 
            # Let's stick to the raw list for the JSON response.
            
            # 2. Get Total Distance
            # properties -> segments -> distance (in meters)
            distance_meters = data['features'][0]['properties']['segments'][0]['distance']
            
            # We return the raw geometry (list of lists)
            return geometry, distance_meters
            
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            return None, 0
            
    except Exception as e:
        print(f"Request Failed: {e}")
        return None, 0

def haversine_distance(coord1, coord2):
    """ 
    Calculate distance in miles between two (lat, lon) tuples.
    Note: coord1 and coord2 must be (latitude, longitude)
    """
    R = 3958.8  
    
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def find_optimal_stops(route_path, total_distance_miles):
    """
    Logic:
    1. Traverse the route.
    2. Keep track of distance traveled.
    3. If distance since last stop > 450 miles (buffer for 500 range), look for gas.
    4. Find cheapest station within 15 miles of current location on route.
    """
    MAX_RANGE = 500
    MPG = 10
    
    stops = []
    total_fuel_cost = 0.0
    
    current_fuel_range = MAX_RANGE
    dist_since_last_stop = 0
    
    last_point = route_path[0] 
    for i in range(1, len(route_path)):
        point = route_path[i] 
        
        step_dist = haversine_distance(
            (last_point[1], last_point[0]), 
            (point[1], point[0])
        )
        
        dist_since_last_stop += step_dist
        current_fuel_range -= step_dist
        
        if current_fuel_range < 50:
           
            curr_lat = point[1]
            curr_lon = point[0]
            
            lat_min, lat_max = curr_lat - 0.3, curr_lat + 0.3
            lon_min, lon_max = curr_lon - 0.3, curr_lon + 0.3
            
            candidates = FuelStation.objects.filter(
                latitude__range=(lat_min, lat_max),
                longitude__range=(lon_min, lon_max)
            )
            
            best_station = None
            min_price = float('inf')
            
            for station in candidates:
                
                d = haversine_distance((curr_lat, curr_lon), (station.latitude, station.longitude))
                if d <= 20: 
                    if station.price < min_price:
                        min_price = station.price
                        best_station = station
            
            if best_station:
                stops.append({
                    "station": best_station.name,
                    "city": best_station.city,
                    "state": best_station.state,
                    "price": float(best_station.price),
                    "coordinates": [best_station.latitude, best_station.longitude]
                })
                
                gallons_needed = dist_since_last_stop / MPG
                total_fuel_cost += float(best_station.price) * gallons_needed
               
                current_fuel_range = MAX_RANGE
                dist_since_last_stop = 0
           

        last_point = point


    if stops:
        last_price = stops[-1]['price']
        gallons_needed = dist_since_last_stop / MPG
        total_fuel_cost += last_price * gallons_needed
    else:
        gallons_needed = total_distance_miles / MPG
        total_fuel_cost = 3.50 * gallons_needed

    return stops, round(total_fuel_cost, 2)