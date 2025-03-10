import requests
import time
import threading
import math
import random
import csv
from datetime import datetime

# API URLs
NEARBY_DRIVERS_API = "http://localhost:5000/nearby-drivers"
LAST_KNOWN_LOCATIONS_API = "http://localhost:5000/last-known-locations"
FLUSH_REDIS_API = "http://localhost:5000/flush-redis"  # New endpoint for Redis flushing

# Base Location (Example City Center)
BASE_LAT = 28.7041
BASE_LON = 77.1025

# Total Requests
TOTAL_REQUESTS = 100
CONCURRENT_THREADS = 20  # Batch size

# CSV Report File
REPORT_FILE = "nearby_drivers_report.csv"

# Function to calculate Haversine distance
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of Earth in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c  # Distance in km

# Function to randomly generate lat/lon within a small offset
def randomize_location(base_lat, base_lon):
    lat_offset = random.uniform(-0.02, 0.02)  # Small random offset
    lon_offset = random.uniform(-0.02, 0.02)
    return base_lat + lat_offset, base_lon + lon_offset

# Function to periodically flush Redis
def flush_redis():
    print("Flushing Redis Cache...")
    response = requests.post(FLUSH_REDIS_API)
    if response.status_code == 200:
        print("Redis cache flushed successfully.")
    else:
        print(f"Failed to flush Redis: {response.status_code}")

# Function to request nearby drivers
def fetch_nearby_drivers(results):
    lat, lon = randomize_location(BASE_LAT, BASE_LON)
    radius = random.randint(1, 5)  # Dynamic radius between 1-5 km
    start_time = time.time()
    response = requests.get(NEARBY_DRIVERS_API, params={"lat": lat, "lon": lon, "radius": radius})
    end_time = time.time()
    response_time = end_time - start_time

    if response.status_code == 200:
        data = response.json()
        drivers = data.get("nearby_drivers", [])

        # Extract driver IDs
        driver_ids = [driver["id"] for driver in drivers if "id" in driver]

        # Fetch last known locations
        last_known_data = fetch_last_known_locations(driver_ids)

        for driver in last_known_data:
            driver_id = driver.get("id", "Unknown")
            driver_lat, driver_lon = driver.get("lat", None), driver.get("lon", None)
            last_updated = driver.get("last_updated", "N/A")

            # Calculate distance
            distance = haversine_distance(lat, lon, driver_lat, driver_lon) if driver_lat and driver_lon else "N/A"
            print(response_time)
            results.append([
                lat, lon, radius, driver_id, driver_lat, driver_lon, last_updated, distance, response_time
            ])
    else:
        print(f"Failed request with status code: {response.status_code}")

# Function to fetch last known locations
def fetch_last_known_locations(driver_ids):
    if not driver_ids:
        return []
    
    headers = {"Content-Type": "application/json"}
    payload = {"driver_ids": driver_ids}
    
    response = requests.post(LAST_KNOWN_LOCATIONS_API, json=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json().get("drivers", [])
    else:
        print(f"Failed to fetch last known locations: {response.status_code}, Response: {response.text}")
        return []

# Function to run tests in batches of 50 with a 30s pause
def run_load_test():
    results = []
    total_batches = TOTAL_REQUESTS // CONCURRENT_THREADS

    for batch in range(total_batches):
        print(f"Starting batch {batch + 1} of {total_batches}")

        threads = []
        for _ in range(CONCURRENT_THREADS):
            thread = threading.Thread(target=fetch_nearby_drivers, args=(results,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        print(f"Batch {batch + 1} completed. Pausing for 30 seconds...")
        time.sleep(1)  # Pause between batches

        if batch % 5 == 0:  # Flush Redis every 5 batches
            flush_redis()

    return results

# Start Load Testing
start_time = time.time()
results = run_load_test()
end_time = time.time()
total_time_taken = end_time - start_time

# Save results to CSV
with open(REPORT_FILE, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow([
        "Requested Lat", "Requested Lon", "Radius (km)", 
        "Driver ID", "Last Known Lat", "Last Known Lon", 
        "Last Updated", "Distance (km)", "Response Time (s)"
    ])
    writer.writerows(results)

print(f"Total time taken for {TOTAL_REQUESTS} requests: {total_time_taken:.2f} seconds")
print(f"Results saved in {REPORT_FILE}")
