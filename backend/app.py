from fastapi import FastAPI, Query
import redis
import h3
import cassandra.cluster
from pydantic import BaseModel
from typing import List
from fastapi import HTTPException

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
    h3_index = h3.latlng_to_cell(lat, lon, 9)
    nearby_indexes = h3.grid_disk(h3_index, radius)
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
        query = (
            "SELECT driver_id, lat, lon, last_updated FROM locations WHERE h3_index IN (%s)" % ",".join([
                "'%s'" % idx for idx in nearby_indexes])
        )
        rows = session.execute(query)
        for row in rows:
            drivers.append({
                "id": row.driver_id,
                "lat": row.lat,
                "lon": row.lon,
                "last_updated": row.last_updated.strftime("%Y-%m-%dT%H:%M:%S")
            })

    # Sort by last updated timestamp (most recent first)
    drivers.sort(key=lambda x: x["last_updated"], reverse=True)    
    return {"nearby_drivers": drivers}



# Define expected request body format
class DriverRequest(BaseModel):
    driver_ids: List[str]

@app.post("/last-known-locations")
async def last_known_locations(request: DriverRequest):
    if not request.driver_ids:
        raise HTTPException(status_code=400, detail="Driver IDs list cannot be empty")

    # Fetch last known locations from Redis or Cassandra
    drivers_data = []
    for driver_id in request.driver_ids:
        data = redis_client.hgetall(f"driver:{driver_id}")
        if data:
            drivers_data.append({
                "id": driver_id,
                "lat": float(data.get("lat", 0.0)),
                "lon": float(data.get("lon", 0.0)),
                "last_updated": data.get("last_updated", "N/A")
            })

    return {"drivers": sorted(drivers_data, key=lambda x: x["last_updated"], reverse=True)}



@app.post("/flush-redis")
async def flush_redis():
    redis_client.flushall()  # Clears all Redis data
    return {"message": "Redis cache flushed successfully"}
