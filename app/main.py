import os
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point

# Configuración desde variables de entorno
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "topic/temperatura")

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
        payload = float(msg.payload.decode())  # Convertir a número
        print(f"Recibido: {payload} en {msg.topic}")

        # Crear punto en InfluxDB
        point = Point("temperatura").tag("sensor", "esp32").field("valor", payload)

        # Guardar en InfluxDB
        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
    except Exception as e:
        print(f"Error procesando mensaje: {e}")

# Conectar a MQTT
mqtt_client = mqtt.Client()
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
mqtt_client.subscribe(MQTT_TOPIC)

print("Escuchando MQTT...")
mqtt_client.loop_forever()
