import requests
import time
import threading
import math
import random
import csv
import numpy as np  # For percentile calculations
from datetime import datetime

# API URLs
NEARBY_DRIVERS_API = "http://localhost:5000/nearby-drivers"
LAST_KNOWN_LOCATIONS_API = "http://localhost:5000/last-known-locations"

# Load Test Configurations
TOTAL_REQUESTS = 500  # Total number of API calls
CONCURRENT_THREADS = 50  # Number of concurrent threads per batch
BATCH_SIZE = 100  # Number of requests per batch
PAUSE_BETWEEN_BATCHES = 0  # Pause (seconds) between batches

# Base Location (Example City Center)
BASE_LAT = 28.7041
BASE_LON = 77.1025

# CSV Report File
REPORT_FILE = "latency_benchmark.csv"

# Store latency results
latency_results = []

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

# Function to send request and measure latency
def send_request(api_url, params, method="GET", json_body=None, results=None):
    start_time = time.time()
    
    try:
        if method == "GET":
            response = requests.get(api_url, params=params)
        elif method == "POST":
            headers = {"Content-Type": "application/json"}
            response = requests.post(api_url, json=json_body, headers=headers)
        else:
            raise ValueError("Unsupported HTTP method")
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to ms

        if response.status_code == 200 and results is not None:
            results.append(response_time)
        else:
            print(f"Failed request to {api_url} with status code: {response.status_code}")
    except Exception as e:
        print(f"Error in request: {e}")

# Function to load test APIs
def run_load_test():
    global latency_results
    total_batches = TOTAL_REQUESTS // BATCH_SIZE

    for batch in range(total_batches):
        print(f"Starting batch {batch + 1} of {total_batches}")

        results = []
        threads = []

        for _ in range(BATCH_SIZE):
            lat, lon = randomize_location(BASE_LAT, BASE_LON)
            radius = random.randint(1, 5)

            # Randomly choose API to simulate real usage
            # if random.choice([True, False]):
            # GET request for nearby drivers
            params = {"lat": lat, "lon": lon, "radius": radius}
            thread = threading.Thread(target=send_request, args=(NEARBY_DRIVERS_API, params, "GET", None, results))
            # else:
            #     # POST request for last known locations
            #     driver_ids = [f"driver_{random.randint(1, 1000)}" for _ in range(10)]
            #     json_body = {"driver_ids": driver_ids}
            #     thread = threading.Thread(target=send_request, args=(LAST_KNOWN_LOCATIONS_API, None, "POST", json_body, results))

            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        # Append batch results to main latency results
        latency_results.extend(results)

        print(f"Batch {batch + 1} completed. Pausing for {PAUSE_BETWEEN_BATCHES} seconds...")
        time.sleep(PAUSE_BETWEEN_BATCHES)

    return latency_results

# Start Load Testing
start_time = time.time()
latencies = run_load_test()
end_time = time.time()
total_time_taken = end_time - start_time

# Calculate Latency Benchmarks
p50 = np.percentile(latencies, 50)
p95 = np.percentile(latencies, 95)
p99 = np.percentile(latencies, 99)
max_latency = max(latencies)
min_latency = min(latencies)

# Save results to CSV
with open(REPORT_FILE, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["P50 (ms)", "P95 (ms)", "P99 (ms)", "Min (ms)", "Max (ms)", "Total Time (s)"])
    writer.writerow([p50, p95, p99, min_latency, max_latency, total_time_taken])

print("\n=== Load Test Completed ===")
print(f"P50 Latency: {p50:.2f} ms")
print(f"P95 Latency: {p95:.2f} ms")
print(f"P99 Latency: {p99:.2f} ms")
print(f"Min Latency: {min_latency:.2f} ms")
print(f"Max Latency: {max_latency:.2f} ms")
print(f"Total Time for {TOTAL_REQUESTS} requests: {total_time_taken:.2f} seconds")
print(f"Latency results saved in {REPORT_FILE}")
