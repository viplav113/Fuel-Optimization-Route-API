import os
import time
import requests
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
from api.models import FuelStation

class Command(BaseCommand):
    help = 'Load fuel prices and Geocode addresses'

    def handle(self, *args, **kwargs):
     
        API_KEY = getattr(settings, 'ORS_API_KEY', None)
        
        if not API_KEY:
            self.stdout.write(self.style.ERROR('Error: ORS_API_KEY is missing from settings.py'))
            return

        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, 'fuel-prices-for-be-assessment.csv')

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        try:
            df = pd.read_csv(file_path)
            df.columns = [c.strip().title() for c in df.columns]
            self.stdout.write(f"Columns found: {list(df.columns)}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading CSV: {e}"))
            return

        stations = []
        self.stdout.write("Starting geocoding (Limited to first 20 for testing)...")
        
        for index, row in df.head(20).iterrows(): 
            
            address_part = row.get('Address', '')
            city_part = row.get('City', '')
            state_part = row.get('State', '')
            
            if pd.isna(address_part) or pd.isna(city_part) or pd.isna(state_part):
                continue

            full_address = f"{address_part}, {city_part}, {state_part}, USA"
            
            lat, lon = self.get_coordinates(full_address, API_KEY)
            
            if lat and lon:
                price_raw = row.get('Retail Price', 0.0)
                if isinstance(price_raw, str):
                    price_raw = price_raw.replace('$', '').strip()
                try:
                    final_price = float(price_raw)
                except (ValueError, TypeError):
                    final_price = 0.0

                stations.append(FuelStation(
                    name=row.get('Truckstop Name', 'Unknown'),
                    address=address_part,
                    city=city_part,
                    state=state_part,
                    price=final_price,
                    latitude=lat,
                    longitude=lon
                ))
                self.stdout.write(self.style.SUCCESS(f"Found: {full_address} -> {lat}, {lon}"))
            else:
                self.stdout.write(self.style.WARNING(f"Could not find coordinates for: {full_address}"))
            
            time.sleep(1.5) 

        
        if stations:
            
            
            FuelStation.objects.bulk_create(stations)
            self.stdout.write(self.style.SUCCESS(f'Successfully loaded {len(stations)} stations into database!'))
        else:
            self.stdout.write(self.style.WARNING('No stations were loaded.'))

    def get_coordinates(self, address, api_key):
        """Helper function to call OpenRouteService Geocoding API"""
        url = "https://api.openrouteservice.org/geocode/search"
        params = {
            'api_key': api_key,
            'text': address,
            'boundary.country': 'US'
        }
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data['features']:
                    coords = data['features'][0]['geometry']['coordinates']
                    return coords[1], coords[0] 
        except Exception as e:
            pass
        return None, None