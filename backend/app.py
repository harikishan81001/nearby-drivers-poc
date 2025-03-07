from fastapi import FastAPI, Query
import redis
import h3
import cassandra.cluster

app = FastAPI()

# Connect to Redis
redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

# Connect to Cassandra
cassandra_cluster = cassandra.cluster.Cluster(["cassandra"])
session = cassandra_cluster.connect()
session.set_keyspace("uber_poc")

@app.get("/nearby-drivers")
def get_nearby_drivers(lat: float, lon: float, radius: int = Query(1, ge=1, le=10)):
    """Find nearby drivers using H3 indexing and Redis, returning their locations."""
    h3_index = h3.latlng_to_cell(lat, lon, 9)  # Correct method for latest H3
    nearby_indexes = h3.grid_disk(h3_index, radius)  # Correct replacement for k_ring
    drivers = []

    for index in nearby_indexes:
        cached_drivers = redis_client.smembers(f"drivers:{index}")
        for driver_id in cached_drivers:
            driver_data = redis_client.hgetall(f"driver:{driver_id}")
            if driver_data:
                drivers.append({
                    "id": driver_id,
                    "lat": float(driver_data.get("lat", 0)),
                    "lon": float(driver_data.get("lon", 0))
                })
    
    if not drivers:
        # Fallback to Cassandra if Redis cache misses
        rows = session.execute("SELECT driver_id, lat, lon FROM locations WHERE h3_index = %s", (h3_index,))
        drivers = [{"id": row.driver_id, "lat": row.lat, "lon": row.lon} for row in rows]
    
    return {"nearby_drivers": drivers}
