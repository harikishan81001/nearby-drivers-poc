# 🚀 Ride Matching Platform - Proof of Concept

This repository contains a **Proof of Concept (PoC)** for a **ride matching platform** that can handle **1 million requests per second**, inspired by real-world implementations.

## **🛠️ Tech Stack**
### **Core Technologies Used**
- **FastAPI** - Lightweight and high-performance API framework for backend services.
- **Apache Cassandra** - NoSQL distributed database for storing driver locations with time-to-live (TTL).
- **Redis** - In-memory database for **fast geospatial lookups** of active drivers.
- **Kafka** - Distributed message broker for handling driver location updates in real-time.
- **H3 (Geospatial Indexing Library)** - Used for efficient **hexagonal grid-based geospatial indexing**.
- **Docker & Docker Compose** - Containerized deployment for all services.

---
## **📌 System Overview**
This PoC mimics how ride-matching platforms efficiently find nearby drivers **at scale**. Here’s how it works:

### **1️⃣ Driver Location Updates (Kafka Producer)**
- A **Simulator Service** continuously generates **1000 driver location updates** every **30 seconds**.
- These updates are **published to Kafka** in the `driver-locations` topic.

### **2️⃣ Location Processing (Kafka Consumer)**
- A **Consumer Service** subscribes to the Kafka `driver-locations` topic and processes each message.
- **H3 hexagonal grid indexing** is used to assign each driver to a **grid cell**.
- Driver locations are stored in **Cassandra with a TTL** of **1 hour**, ensuring old locations expire automatically.
- Driver locations are also **cached in Redis** for quick lookups.

### **3️⃣ Finding Nearby Drivers (API Request)**
- The **FastAPI backend** exposes an endpoint to fetch nearby drivers.
- The request contains **user latitude, longitude, and search radius**.
- The system:
  - Converts **lat/lon to an H3 hex index**.
  - Uses **H3's `grid_disk` function** to find neighboring cells.
  - Looks up drivers in **Redis** for ultra-fast response times.
  - Falls back to **Cassandra** if Redis misses the data.
- Returns a list of **nearby drivers sorted by proximity**.

---
## **⚙️ Docker-Based Local Setup**

### **🔹 Step 1: Clone the Repository**
```sh
git clone <repo-url>
cd <repo-directory>
```

### **🔹 Step 2: Start the System**
```sh
docker-compose up --build
```
This will start:
- **Cassandra** (Database)
- **Redis** (Cache Layer)
- **Kafka & Zookeeper** (Message Queue)
- **FastAPI Backend** (Driver Matching API)
- **Kafka Consumer** (Processes driver locations)
- **Simulator** (Generates driver location updates)

---
## **🚀 API Endpoints**

### **🔹 Get Nearby Drivers**
**URL:** `GET /nearby-drivers`

**Query Parameters:**
| Parameter  | Type  | Description  |
|------------|------|--------------|
| `lat`      | float | User's latitude |
| `lon`      | float | User's longitude |
| `radius`   | int   | Search radius in hexagonal rings (default: 1) |

**Example Request:**
```sh
GET http://localhost:5000/nearby-drivers?lat=28.7041&lon=77.1025&radius=1
```

**Example Response:**
```json
{
  "nearby_drivers": [
    "driver_23",
    "driver_87",
    "driver_192"
  ]
}
```

---
## **🔧 Architecture Explained**

### **1️⃣ Kafka-Based Driver Location Updates**
- The **simulator** generates fake driver movements and **publishes them to Kafka**.
- Kafka ensures **fault-tolerant, real-time message processing**.

### **2️⃣ Cassandra as a Long-Term Storage Layer**
- Stores **driver locations with TTL (1 hour)** to automatically remove stale data.
- Allows **fast writes with partitioning on H3 index**.

### **3️⃣ Redis for Fast Driver Lookup**
- Nearby drivers are first looked up in **Redis** (hot cache).
- If missing, data is fetched from **Cassandra**.

### **4️⃣ H3 Geospatial Indexing**
- Converts **lat/lon to a hex index** (H3 grid resolution 9).
- **`grid_disk`** is used to efficiently **query adjacent hexagons**.

---
## **📌 Key Improvements Over Traditional Approaches**
| Approach | Challenge | Our Optimization |
|------------|------------|----------------|
| **Raw Lat/Lon Queries** | Inefficient for large-scale lookups | **H3 Geospatial Indexing** reduces query time |
| **SQL Joins for Distance Calculation** | High compute cost | **Redis caching + Cassandra partitioning** ensures fast lookup |
| **No Message Queue** | Handling **real-time updates** becomes complex | **Kafka decouples location updates from lookup queries** |

---
## **🛠️ Troubleshooting**

### **1️⃣ Cassandra Connection Issue**
```sh
cqlsh cassandra 9042
```
If it fails, restart the Cassandra service:
```sh
docker-compose restart cassandra
```

### **2️⃣ Kafka Not Processing Messages**
```sh
docker logs -f consumer
```
If there’s an error, restart Kafka:
```sh
docker-compose restart kafka
```

### **3️⃣ API Not Returning Drivers**
- Ensure **simulator is running**:
  ```sh
  docker logs -f simulator
  ```
- Check if drivers exist in Cassandra:
  ```sql
  SELECT * FROM ride_matching.locations LIMIT 10;
  ```

---
## **🚀 Future Enhancements**
✅ **Implement ETA Calculation** (ML-based estimations).
✅ **Optimize Redis TTL** (Adjust expiration based on driver activity).
✅ **Support Multi-Region Lookups** (Extend `grid_disk` radius dynamically).

---
## **💡 Credits & References**
- **H3 Library:** [https://h3geo.org](https://h3geo.org)
- **Kafka Documentation:** [https://kafka.apache.org](https://kafka.apache.org)
- **Cassandra Docs:** [https://cassandra.apache.org](https://cassandra.apache.org)

---
## **✅ Conclusion**
This PoC demonstrates a **scalable and efficient way** to match riders with nearby drivers using **H3 indexing, Redis caching, Kafka event streaming, and Cassandra storage**. 🚀

If you have suggestions or improvements, feel free to contribute! 💡

