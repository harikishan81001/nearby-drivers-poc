import requests
import time
import threading
import math
import random
import csv

# API URL
API_URL = "http://localhost:5000/nearby-drivers"

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

# Function to send requests and measure response times
def send_request(results):
    dynamic_radius = random.randint(1, 5)  # Dynamic radius between 1-5 km
    start_time = time.time()
    response = requests.get(API_URL, params={"lat": TEST_LAT, "lon": TEST_LON, "radius": dynamic_radius})
    end_time = time.time()
    response_time = end_time - start_time
    
    if response.status_code == 200:
        data = response.json()
        drivers = data.get("nearby_drivers", [])
        for driver in drivers:
            if isinstance(driver, dict) and "lat" in driver and "lon" in driver:
                lat, lon = driver["lat"], driver["lon"]
                distance = haversine_distance(TEST_LAT, TEST_LON, lat, lon)
                results.append([driver['id'], lat, lon, dynamic_radius, distance, response_time])
    else:
        print(f"Failed request with status code: {response.status_code}")

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
    writer.writerow(["Driver ID", "Latitude", "Longitude", "Queried Radius (km)", "Distance (km)", "Response Time (s)"])
    writer.writerows(results)

print(f"Total time taken for {TOTAL_REQUESTS} requests: {time_taken:.2f} seconds")
print(f"Results saved in {REPORT_FILE}")