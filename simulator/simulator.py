from confluent_kafka import Producer
import time
import json
import random

# Kafka Producer Configuration
conf = {
    'bootstrap.servers': 'kafka:9092'
}
producer = Producer(conf)

# Simulated Area (City Center Lat/Lon)
CITY_CENTER = (28.7041, 77.1025)  # New Delhi as example
RADIUS = 0.05  # Movement radius (~5km variation)

# Fixed Number of Simulated Drivers
NUM_DRIVERS = 1000

# Generate fixed driver locations
drivers = {
    f"driver_{i}": {
        "lat": CITY_CENTER[0] + random.uniform(-RADIUS, RADIUS),
        "lon": CITY_CENTER[1] + random.uniform(-RADIUS, RADIUS)
    }
    for i in range(NUM_DRIVERS)
}

# Function to simulate slight movement
def update_driver_location(driver):
    driver["lat"] += random.uniform(-0.001, 0.001)  # Small latitude shift
    driver["lon"] += random.uniform(-0.001, 0.001)  # Small longitude shift
    return driver

# Send driver locations to Kafka every 30 seconds
def send_location_updates():
    while True:
        for driver_id, location in drivers.items():
            updated_location = update_driver_location(location)
            data = {
                "driver_id": driver_id,
                "lat": updated_location["lat"],
                "lon": updated_location["lon"]
            }
            producer.produce("driver-locations", json.dumps(data))
            producer.flush()
        print(f"Sent location updates for {NUM_DRIVERS} drivers")
        time.sleep(30)  # Update every 30 seconds

if __name__ == "__main__":
    send_location_updates()
