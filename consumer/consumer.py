from confluent_kafka import Consumer
import redis
import h3
import cassandra.cluster
import json
import datetime

# Kafka consumer setup
conf = {
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'driver-location-group',
    'auto.offset.reset': 'earliest'
}
consumer = Consumer(conf)
consumer.subscribe(['driver-locations'])

# Connect to Redis
redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

# Connect to Cassandra
cassandra_cluster = cassandra.cluster.Cluster(["cassandra"])
session = cassandra_cluster.connect()
session.set_keyspace("uber_poc")

while True:
    msg = consumer.poll(1.0)
    if msg is None: continue
    if msg.error():
        print(f"Kafka error: {msg.error()}")
        continue
    
    # Parse driver location
    data = json.loads(msg.value())
    driver_id = data['driver_id']
    lat, lon = data['lat'], data['lon']
    timestamp = datetime.datetime.utcnow()
    h3_index = h3.latlng_to_cell(lat, lon, 9)
    
    redis_client.sadd(f"drivers:{h3_index}", driver_id)
    redis_client.hset(f"driver:{driver_id}", mapping={
        "lat": lat,
        "lon": lon,
        "last_updated": timestamp.isoformat()
    })
    redis_client.expire(f"driver:{driver_id}", 300)  # TTL: 5 mins
    redis_client.expire(f"drivers:{h3_index}", 300)
    
    # Store in Cassandra (durability)
    session.execute("""
        INSERT INTO locations (h3_index, driver_id, lat, lon, last_updated)
        VALUES (%s, %s, %s, %s, %s) USING TTL 3600
    """, (h3_index, driver_id, lat, lon, timestamp))
    
    print(f"Stored driver {driver_id} at {lat},{lon} -> H3 {h3_index} (Last Updated: {timestamp})")
