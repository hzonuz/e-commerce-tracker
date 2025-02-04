from kafka import KafkaProducer
import json
import random
import time
from faker import Faker
from datetime import datetime

fake = Faker()
TOPIC = "user_clicks"

# Kafka Producer Configuration
producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

# Define Product Categories
PRODUCTS = [
    {"id": "P001", "category": "Electronics"},
    {"id": "P002", "category": "Books"},
    {"id": "P003", "category": "Clothing"},
    {"id": "P004", "category": "Home Appliances"},
    {"id": "P005", "category": "Gaming"},
]


# Generate a Random User Event
def generate_event():
    user_id = fake.uuid4()
    session_id = fake.uuid4()
    product = random.choice(PRODUCTS)
    timestamp = datetime.now().isoformat()

    event_type = random.choices(["click", "purchase"], weights=[0.8, 0.2])[0]

    event = {
        "user_id": user_id,
        "session_id": session_id,
        "event_type": event_type,
        "product_id": product["id"],
        "category": product["category"],
        "timestamp": timestamp,
        "referrer": random.choice(
            ["google.com", "facebook.com", "direct", "instagram.com"]
        ),
    }
    return event


# Produce Events to Kafka
def produce_events():
    while True:
        event = generate_event()
        producer.send(TOPIC, value=event)
        print(f"Sent: {event}")
        time.sleep(random.uniform(0.1, 1))  # Simulate real-time events


if __name__ == "__main__":
    produce_events()
