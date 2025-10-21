# Log Monitoring System

An end-to-end demo pipeline that generates synthetic application logs, streams them through Kafka, and indexes them into Elasticsearch. This system provides a robust solution for real-time log aggregation, processing, and analysis, enabling efficient monitoring and troubleshooting of distributed applications.

## Prerequisites

- Docker Engine 24.x or newer and the `docker compose` plugin.
- At least 4 GB of free memory; Elasticsearch and Kibana are memory-intensive.

## Quick Start

```bash
# Clone or open the repository, then launch the stack
docker compose -f deployment/Docker-compose.yml pull
docker compose -f deployment/Docker-compose.yml up -d --build

# Follow the logs (optional)
docker compose -f deployment/Docker-compose.yml logs -f producer consumer kafka elasticsearch
```

Endpoints:

- Kafka broker (internal): `kafka:9092` (PLAINTEXT)
- Elasticsearch REST API: `http://localhost:9200`
- Kibana: `http://localhost:5601`

To shut everything down and remove containers:

```bash
docker compose -f deployment/Docker-compose.yml down
```

Add `-v` to delete the Elasticsearch volume (`es-data`) if you want a clean slate.

## Service Environment Variables

All services read their defaults from `deployment/Docker-compose.yml`:

| Service  | Variable               | Default value                 | Purpose                               |
| -------- | ---------------------- | ----------------------------- | ------------------------------------- |
| Producer | `KAFKA_BROKER`       | `kafka:9093`                | Broker endpoint for producing logs    |
|          | `TOPIC_NAME`         | `application-logs`          | Kafka topic to write logs to          |
|          | `LOGS_PER_SECOND`    | `5`                         | Throttle for synthetic log generation |
| Consumer | `KAFKA_BROKER`       | `kafka:9093`                | Broker endpoint for consuming logs    |
|          | `TOPIC_NAME`         | `application-logs`          | Kafka topic to read from              |
|          | `ELASTICSEARCH_HOST` | `http://elasticsearch:9200` | Elasticsearch cluster URL             |
|          | `CONSUMER_GROUP`     | `log-consumer-group`        | Kafka consumer group id               |
|          | `BATCH_SIZE`         | `100`                       | Bulk size for Elasticsearch writes    |

Adjust these in the compose file or override with environment files as needed.

## Working With Kafka in KRaft Mode

The Kafka service is configured with:

- `KAFKA_PROCESS_ROLES=broker,controller`
- Listeners for client traffic (`PLAINTEXT`, `PLAINTEXT_HOST`) and controller traffic (`CONTROLLER://kafka:9094`)
- Single-node quorum voters (`KAFKA_CONTROLLER_QUORUM_VOTERS=1@kafka:9094`)

If you scale to multiple brokers, assign unique `KAFKA_NODE_ID` values and extend the quorum list accordingly.

## Observability Tips

- Check Elasticsearch health: `curl localhost:9200/_cluster/health?pretty`
- Verify topics and consumer lag: `docker compose -f deployment/Docker-compose.yml exec kafka /usr/bin/kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group log-consumer-group`

### Tracking Logs for All Endpoints

To effectively track logs for all endpoints, you can leverage Kibana's powerful querying and visualization capabilities. Once logs are indexed in Elasticsearch via the consumer, you can:

1. **Access Kibana**: Navigate to `http://localhost:5601` in your browser.
2. **Discover Logs**: Go to the "Discover" section in Kibana.
3. **Filter by Endpoint**: Use the KQL (Kibana Query Language) search bar to filter logs. For example, to see logs related to a specific service or action, you can use queries like `service: "user-service"` or `action: "login"`.
4. **Create Visualizations**: Build dashboards to monitor key metrics per endpoint, such as error rates, response times, and traffic volume.

This setup allows for comprehensive monitoring and analysis of application behavior across all defined endpoints.

## Development Notes

- Python packaging: the multi-service image is built from `deployment/Dockerfile` and installs dependencies from `requirements.txt`.
- The stack uses health checks on Kafka and Elasticsearch before dependent services start; start-up may take a minute while Kafka forms the KRaft quorum and Elasticsearch boots.

## Troubleshooting

- **Kafka refuses connections** – confirm ports `9092/9093` are free and the broker logs show “Transitioning to active controller”.
- **Elasticsearch fails to start** – bump JVM heap (`ES_JAVA_OPTS`) or allocate more Docker memory.
- **Consumer lag grows** – enlarge `BATCH_SIZE` or scale consumers; check Elasticsearch indexing speed.
- **Permission issues on volume** – remove the `es-data` volume (`docker volume rm log-monitoringsystem_es-data`) and relaunch.
