import os
import json
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point

# Cargar configuración desde topics.json
TOPICS_FILE = os.path.join(os.path.dirname(__file__), "topics.json")
with open(TOPICS_FILE, "r") as f:
    topics_config = json.load(f)

# Configuración desde variables de entorno
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))

INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "your-token")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "iot")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "iot-device")

# Conectar a InfluxDB
client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
write_api = client.write_api()

# Función cuando llega un mensaje MQTT
def on_message(client, userdata, msg):
    try:
        payload = float(msg.payload.decode())  # Convertir mensaje a número
        print(f"Recibido: {payload} en {msg.topic}")

        # Buscar configuración del topic
        topic_config = topics_config.get(msg.topic)
        if not topic_config:
            print(f"⚠️ Topic {msg.topic} no configurado en topics.json, ignorando...")
            return

        # Crear punto en InfluxDB dinámicamente
        point = (
            Point(topic_config["measurement"])
            .tag(topic_config["tag"], topic_config["sensor_name"])
            .field(topic_config["value_field"], payload)
        )

        # Guardar en InfluxDB
        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
        print(f"✅ Guardado en InfluxDB: {point}")

    except Exception as e:
        print(f"❌ Error procesando mensaje: {e}")

# Conectar a MQTT
mqtt_client = mqtt.Client()
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT)

# Suscribirse a todos los topics definidos en el JSON
for topic in topics_config.keys():
    mqtt_client.subscribe(topic)
    print(f"📡 Suscrito a {topic}")

print("🚀 Escuchando MQTT...")
mqtt_client.loop_forever()

