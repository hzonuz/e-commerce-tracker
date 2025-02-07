from confluent_kafka import Producer
import json
import random
import time
from faker import Faker
from datetime import datetime

fake = Faker()
TOPIC = "user_clicks"

conf = {
    "bootstrap.servers": "127.0.0.1:9092",
    "client.id": "user-click-producer",
}

producer = Producer(conf)


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


def delivery_report(err, msg):
    """Callback for successful or failed message delivery."""
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")


def produce_events():
    while True:
        event = generate_event()
        print(event)
        producer.produce(
            TOPIC,
            key=event["user_id"],  # Optional: Partitioning key
            value=json.dumps(event),
            callback=delivery_report,
        )
        producer.poll(0)  # Trigger callback
        time.sleep(random.uniform(0.1, 1))  # Simulate real-time events


if __name__ == "__main__":
    produce_events()
