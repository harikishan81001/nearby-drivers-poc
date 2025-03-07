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
    """Find nearby drivers using H3 indexing and Redis."""
    h3_index = h3.latlng_to_cell(lat, lon, 9)  # Resolution 9 gives a fine-grained search
    nearby_indexes = h3.grid_disk(h3_index, radius)  # Correct replacement for k_ring
    drivers = []

    for index in nearby_indexes:
        cached_drivers = redis_client.smembers(f"drivers:{index}")
        drivers.extend(cached_drivers)
    
    if not drivers:
        # Fallback to Cassandra if Redis cache misses
        rows = session.execute("SELECT driver_id FROM locations WHERE h3_index = %s", (h3_index,))
        drivers = [row.driver_id for row in rows]
    
    return {"nearby_drivers": drivers}
