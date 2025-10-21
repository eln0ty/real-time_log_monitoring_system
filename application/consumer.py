import json
import time
import os
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from elasticsearch import Elasticsearch, helpers
from datetime import datetime

KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
TOPIC_NAME = os.getenv('TOPIC_NAME', 'application-logs')
ELASTICSEARCH_HOST = os.getenv('ELASTICSEARCH_HOST', 'http://localhost:9200')
CONSUMER_GROUP = os.getenv('CONSUMER_GROUP', 'log-consumer-group')
BATCH_SIZE = int(os.getenv('BATCH_SIZE', '100'))

def create_consumer(max_retries=10, retry_delay=5):
    for attempt in range(max_retries):
        try:
            consumer = KafkaConsumer(
                TOPIC_NAME,
                bootstrap_servers=KAFKA_BROKER,
                group_id=CONSUMER_GROUP,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                max_poll_records=BATCH_SIZE
            )
            print(f"✓ Connected to Kafka broker at {KAFKA_BROKER}")
            return consumer
        except NoBrokersAvailable:
            print(f"⚠ Kafka broker not available. Retrying in {retry_delay}s... (Attempt {attempt + 1}/{max_retries})")
            time.sleep(retry_delay)
    
    raise Exception("Failed to connect to Kafka broker")

def create_elasticsearch_client(max_retries=10, retry_delay=5):
    for attempt in range(max_retries):
        try:
            es = Elasticsearch([ELASTICSEARCH_HOST])
            if es.ping():
                print(f"✓ Connected to Elasticsearch at {ELASTICSEARCH_HOST}")
                return es
            else:
                raise Exception("Elasticsearch ping failed")
        except Exception as e:
            print(f"⚠ Elasticsearch not available. Retrying in {retry_delay}s... (Attempt {attempt + 1}/{max_retries})")
            time.sleep(retry_delay)
    
    raise Exception("Failed to connect to Elasticsearch")

def create_index_template(es):
    index_template = {
        "index_patterns": ["application-logs-*"],
        "template": {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            },
            "mappings": {
                "properties": {
                    "timestamp": {"type": "date"},
                    "level": {"type": "keyword"},
                    "service": {"type": "keyword"},
                    "action": {"type": "keyword"},
                    "user_id": {"type": "keyword"},
                    "ip_address": {"type": "ip"},
                    "message": {"type": "text"},
                    "response_time_ms": {"type": "integer"},
                    "status_code": {"type": "integer"},
                    "user_agent": {"type": "text"},
                    "session_id": {"type": "keyword"},
                    "error_message": {"type": "text"},
                    "stack_trace": {"type": "text"}
                }
            }
        }
    }
    
    try:
        es.indices.put_index_template(name="application-logs-template", body=index_template)
        print("✓ Index template created/updated")
    except Exception as e:
        print(f"⚠ Error creating index template: {e}")

def consume_and_index_logs():
    consumer = create_consumer()
    es = create_elasticsearch_client()
    create_index_template(es)
    
    print(f"\nStarting log consumer. Reading from topic '{TOPIC_NAME}'")
    print("Press Ctrl+C to stop\n")
    
    batch = []
    count = 0
    
    try:
        for message in consumer:
            log = message.value
            
            # Prepare document for Elasticsearch
            index_name = f"application-logs-{datetime.utcnow().strftime('%Y.%m.%d')}"
            
            batch.append({
                "_index": index_name,
                "_source": log
            })
            
            # Bulk index when batch is full
            if len(batch) >= BATCH_SIZE:
                try:
                    helpers.bulk(es, batch)
                    count += len(batch)
                    print(f"✓ Indexed {count} logs to Elasticsearch")
                    batch = []
                except Exception as e:
                    print(f"✗ Error indexing to Elasticsearch: {e}")
                    batch = []
    
    except KeyboardInterrupt:
        # Index remaining logs
        if batch:
            try:
                helpers.bulk(es, batch)
                count += len(batch)
            except Exception as e:
                print(f"✗ Error indexing final batch: {e}")
        
        print(f"\n✓ Consumer stopped. Total logs indexed: {count}")
    finally:
        consumer.close()

if __name__ == "__main__":
    consume_and_index_logs()
