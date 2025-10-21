import json
import time
import os
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
from fake_logs import generate_log

KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
TOPIC_NAME = os.getenv('TOPIC_NAME', 'application-logs')
LOGS_PER_SECOND = int(os.getenv('LOGS_PER_SECOND', '5'))

def create_producer(max_retries=10, retry_delay=5):
    for attempt in range(max_retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKER,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3,
                max_in_flight_requests_per_connection=1
            )
            print(f"✓ Connected to Kafka broker at {KAFKA_BROKER}")
            return producer
        except NoBrokersAvailable:
            print(f"⚠ Kafka broker not available. Retrying in {retry_delay}s... (Attempt {attempt + 1}/{max_retries})")
            time.sleep(retry_delay)
    
    raise Exception("Failed to connect to Kafka broker after maximum retries")

def send_logs():
    producer = create_producer()
    
    print(f"Starting log producer. Sending {LOGS_PER_SECOND} logs/second to topic '{TOPIC_NAME}'")
    print("Press Ctrl+C to stop\n")
    
    try:
        count = 0
        while True:
            log = generate_log()
            
            # Send to Kafka
            future = producer.send(TOPIC_NAME, value=log)
            
            # Optional: Wait for confirmation
            try:
                record_metadata = future.get(timeout=10)
                count += 1
                if count % 10 == 0:
                    print(f"Sent {count} logs | Last: [{log['level']}] {log['service']} - {log['message'][:50]}")
            except Exception as e:
                print(f"✗ Error sending log: {e}")
            
            time.sleep(1 / LOGS_PER_SECOND)
            
    except KeyboardInterrupt:
        print(f"\n\n✓ Producer stopped. Total logs sent: {count}")
    finally:
        producer.close()

if __name__ == "__main__":
    send_logs()
