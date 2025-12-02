🚛⛽ Fuel Optimization Route API

A Django-based REST API that calculates the optimal driving route between two U.S. locations and finds the most cost-effective fuel stops along the way.

Overview

This app:

Uses OpenRouteService for driving directions.

Tracks a vehicle range (500 miles per tank, 10 MPG).

Chooses cheap fuel stations from a local DB (pre-geocoded).

Returns a full itinerary: route geometry, fuel stops, and total fuel cost.

Key Feature

Pre-processes and geocodes fuel station addresses once (via a management command) and stores them locally so route queries return results in milliseconds.

Features

  Route geometry from OpenRouteService
  
  Fuel optimization with vehicle range constraints
  
  Local fuel-station DB with precomputed lat/lon
  
  Fast spatial lookups (bounding-box within radius)
  
  Simple JSON API response (route summary, stops, geometry)

Setup & Installation
1. Clone the repository
```
git clone https://github.com/your-username/fuel-route-api.git
cd fuel-route-api
```
2. Create and activate virtual environment
# Windows
```
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies
```
pip install django djangorestframework requests pandas polyline
```
4. Configure API key

Edit fuel_project/settings.py:
```
ORS_API_KEY = 'your-api-key-here'
```

5. Initialize database
```
python manage.py makemigrations
python manage.py migrate
```
6. Ingest fuel data (important)
```
python manage.py load_fuel_data
```

By default the script processes a limited number of rows to respect API rate limits. To load the full CSV, remove the .head() limit inside load_fuel_data.py.

7. Run the server
```
python manage.py runserver
```

API: Calculate Route
Endpoint
GET /api/route/

Query parameters

start — starting coordinates as "longitude,latitude"

finish — destination coordinates as "longitude,latitude"

Example request
```
GET http://127.0.0.1:8000/api/route/?start=-74.0060,40.7128&finish=-75.1652,39.9526
```

Example response
```
{
  "route_summary": {
    "total_distance_miles": 94.5,
    "total_fuel_cost": 32.45,
    "estimated_stops": 1
  },
  "fuel_stops": [
    {
      "station": "Bob's Gas",
      "city": "Edison",
      "state": "NJ",
      "price": 3.05,
      "coordinates": [40.518, -74.412]
    }
  ],
  "route_geometry": [
    [-74.0060, 40.7128],
    [-74.0065, 40.7129],
    ...
  ]
}
```
