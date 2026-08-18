import os
import json
import time
import urllib.request
import requests
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_CSV = os.path.join(PROJECT_ROOT, "fuel-prices-for-be-assessment.csv")
DATA_DIR = os.path.join(PROJECT_ROOT, "backend", "data")
CACHE_FILE = os.path.join(DATA_DIR, "geocode_cache.json")
OUTPUT_CSV = os.path.join(DATA_DIR, "processed_fuel_prices.csv")
US_CITIES_CSV = os.path.join(DATA_DIR, "us_cities.csv")

# Standard US 50 States + DC postal codes
US_STATES = {
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
}

def ensure_us_cities_db():
    if not os.path.exists(US_CITIES_CSV):
        url = "https://raw.githubusercontent.com/kelvins/US-Cities-Database/main/csv/us_cities.csv"
        print(f"Downloading US Cities reference database to {US_CITIES_CSV}...")
        urllib.request.urlretrieve(url, US_CITIES_CSV)

def process_data():
    os.makedirs(DATA_DIR, exist_ok=True)
    ensure_us_cities_db()
    
    print(f"Reading raw dataset from {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)
    print(f"Original record count: {len(df)}")
    
    # 1. Validate required fields
    required_cols = ['OPIS Truckstop ID', 'Truckstop Name', 'Address', 'City', 'State', 'Retail Price']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
            
    # 2. Clean whitespace and drop missing
    for col in df.select_dtypes(['object']).columns:
        df[col] = df[col].astype(str).str.strip()
        
    df = df.dropna(subset=['OPIS Truckstop ID', 'Address', 'City', 'State', 'Retail Price'])
    
    # Filter for US States only
    df['State_Upper'] = df['State'].str.upper()
    df = df[df['State_Upper'].isin(US_STATES)].copy()
    
    # Convert Retail Price to float
    df['Retail Price'] = pd.to_numeric(df['Retail Price'], errors='coerce')
    df = df.dropna(subset=['Retail Price'])
    
    # Deduplicate: for same OPIS ID & Address, keep the lowest retail price
    df = df.sort_values('Retail Price').drop_duplicates(
        subset=['OPIS Truckstop ID', 'Address'],
        keep='first'
    )
    print(f"Deduplicated US stations count: {len(df)}")
    
    # 3. Match against US Cities Reference Database
    cities_df = pd.read_csv(US_CITIES_CSV)
    cities_df['CITY_upper'] = cities_df['CITY'].astype(str).str.strip().str.upper()
    cities_df['STATE_upper'] = cities_df['STATE_CODE'].astype(str).str.strip().str.upper()
    
    cities_lookup = cities_df.groupby(['CITY_upper', 'STATE_upper']).first().reset_index()
    
    df['City_Upper'] = df['City'].str.upper()
    
    merged = pd.merge(
        df,
        cities_lookup[['CITY_upper', 'STATE_upper', 'LATITUDE', 'LONGITUDE']],
        left_on=['City_Upper', 'State_Upper'],
        right_on=['CITY_upper', 'STATE_upper'],
        how='left'
    )
    
    # 4. Load cache for remaining geocoding
    cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                cache = json.load(f)
        except Exception:
            cache = {}
            
    latitudes = []
    longitudes = []
    
    headers = {"User-Agent": "FuelRoutePlannerPreprocessor/1.0"}
    
    unmatched_count = 0
    geocoded_online = 0
    
    for i, row in merged.iterrows():
        lat = row['LATITUDE']
        lon = row['LONGITUDE']
        
        if pd.notna(lat) and pd.notna(lon):
            latitudes.append(float(lat))
            longitudes.append(float(lon))
            continue
            
        city = row['City']
        state = row['State']
        cache_key = f"{city}, {state}"
        
        if cache_key in cache:
            cached_lat, cached_lon = cache[cache_key]
            latitudes.append(cached_lat)
            longitudes.append(cached_lon)
        else:
            # Query Nominatim for the city + state
            try:
                url = "https://nominatim.openstreetmap.org/search"
                params = {"q": f"{city}, {state}, USA", "format": "json", "countrycodes": "us", "limit": "1"}
                resp = requests.get(url, params=params, headers=headers, timeout=5.0)
                if resp.status_code == 200 and len(resp.json()) > 0:
                    c_lat = float(resp.json()[0]["lat"])
                    c_lon = float(resp.json()[0]["lon"])
                    cache[cache_key] = (c_lat, c_lon)
                    latitudes.append(c_lat)
                    longitudes.append(c_lon)
                    geocoded_online += 1
                else:
                    cache[cache_key] = (None, None)
                    latitudes.append(None)
                    longitudes.append(None)
                    unmatched_count += 1
                time.sleep(1.0)
            except Exception as e:
                latitudes.append(None)
                longitudes.append(None)
                unmatched_count += 1
                
    # Save cache
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)
        
    df['latitude'] = latitudes
    df['longitude'] = longitudes
    
    # Drop rows that could not be geocoded
    valid_df = df.dropna(subset=['latitude', 'longitude']).copy()
    
    # Clean up auxiliary columns
    if 'State_Upper' in valid_df.columns:
        valid_df = valid_df.drop(columns=['State_Upper'])
    if 'City_Upper' in valid_df.columns:
        valid_df = valid_df.drop(columns=['City_Upper'])
        
    # Save processed CSV
    valid_df.to_csv(OUTPUT_CSV, index=False)
    
    print(f"Successfully processed dataset saved to {OUTPUT_CSV}")
    print(f"Total valid geocoded US fuel stations: {len(valid_df)}")
    print(f"Excluded/unresolved records: {len(df) - len(valid_df)}")

if __name__ == "__main__":
    process_data()
