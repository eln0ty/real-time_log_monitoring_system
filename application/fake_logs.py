import json
import random
import time
from datetime import datetime
from faker import Faker

fake = Faker()

LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
SERVICES = ['auth-service', 'payment-service', 'user-service', 'inventory-service', 'notification-service']
ACTIONS = ['login', 'logout', 'purchase', 'update', 'delete', 'create', 'fetch']

def generate_log():
    log_level = random.choices(
        LOG_LEVELS,
        weights=[10, 50, 20, 15, 5],  # INFO logs are most common
        k=1
    )[0]
    
    service = random.choice(SERVICES)
    action = random.choice(ACTIONS)
    
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'level': log_level,
        'service': service,
        'action': action,
        'user_id': fake.uuid4(),
        'ip_address': fake.ipv4(),
        'message': fake.sentence(),
        'response_time_ms': random.randint(10, 2000),
        'status_code': random.choices(
            [200, 201, 400, 401, 403, 404, 500, 503],
            weights=[50, 10, 5, 5, 3, 5, 2, 1],
            k=1
        )[0],
        'user_agent': fake.user_agent(),
        'session_id': fake.uuid4()[:8]
    }
    
    # Add error details for ERROR and CRITICAL logs
    if log_level in ['ERROR', 'CRITICAL']:
        log_entry['error_message'] = fake.sentence()
        log_entry['stack_trace'] = f"at {fake.file_path()} line {random.randint(1, 1000)}"
    
    return log_entry

def generate_logs(count=1):
    return [generate_log() for _ in range(count)]

if __name__ == "__main__":
    # Test the generator
    for _ in range(5):
        log = generate_log()
        print(json.dumps(log, indent=2))
        time.sleep(0.5)