import requests
import time
import threading
import math
import random
import csv

# API URLs
NEARBY_DRIVERS_API = "http://localhost:5000/nearby-drivers"
LAST_KNOWN_LOCATIONS_API = "http://localhost:5000/last-known-locations"

# Location for testing (City Center Example)
TEST_LAT = 28.7041
TEST_LON = 77.1025

# Number of requests to send
TOTAL_REQUESTS = 1000000
CONCURRENT_THREADS = 100

# CSV Report File
REPORT_FILE = "nearby_drivers_report.csv"

# Function to calculate Haversine distance
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of the Earth in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c  # Distance in km

# Function to fetch last known locations
def fetch_last_known_locations(driver_ids):
    response = requests.post(LAST_KNOWN_LOCATIONS_API, json=driver_ids)
    if response.status_code == 200:
        data = response.json()
        return data.get("last_known_locations", [])
    return []

# Function to send requests and measure response times
def send_request(results):
    dynamic_radius = random.randint(1, 5)  # Dynamic radius between 1-5 km
    response = requests.get(NEARBY_DRIVERS_API, params={"lat": TEST_LAT, "lon": TEST_LON, "radius": dynamic_radius})
    if response.status_code == 200:
        data = response.json()
        drivers = data.get("nearby_drivers", [])
        driver_ids = [driver["id"] for driver in drivers if isinstance(driver, dict)]
        last_known_locations = fetch_last_known_locations(driver_ids)
        for driver in last_known_locations:
            distance = haversine_distance(TEST_LAT, TEST_LON, driver["lat"], driver["lon"])
            results.append([driver["id"], driver["lat"], driver["lon"], driver["last_updated"], distance])

# Function to run tests with multiple threads
def run_load_test():
    results = []
    threads = []
    for _ in range(CONCURRENT_THREADS):
        thread = threading.Thread(target=send_request, args=(results,))
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
    
    return results

# Start load testing
start_time = time.time()
results = run_load_test()
end_time = time.time()

time_taken = end_time - start_time

# Save results to CSV
with open(REPORT_FILE, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Driver ID", "Latitude", "Longitude", "Last Updated", "Distance (km)"])
    writer.writerows(results)

print(f"Total time taken for {TOTAL_REQUESTS} requests: {time_taken:.2f} seconds")
print(f"Results saved in {REPORT_FILE}")
