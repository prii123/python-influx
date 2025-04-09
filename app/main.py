import os
import json
import time
import threading
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from datetime import datetime

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

# Almacenar último dato por topic
last_values = {}

# Función cuando llega un mensaje MQTT
def on_message(client, userdata, msg):
    try:
        payload = float(msg.payload.decode())
        print(f"Recibido: {payload} en {msg.topic}")

        topic_config = topics_config.get(msg.topic)
        if not topic_config:
            print(f"⚠️ Topic {msg.topic} no configurado en topics.json, ignorando...")
            return

        # Guardar último valor para procesamiento posterior
        last_values[msg.topic] = {
            "value": payload,
            "config": topic_config,
            "timestamp": datetime.utcnow()
        }

    except Exception as e:
        print(f"❌ Error procesando mensaje: {e}")

# Función periódica cada hora
def procesar_periodicamente():
    while True:
        print("⏱ Procesando datos cada hora...")
        for topic, data in last_values.items():
            value = data["value"]
            config = data["config"]
            timestamp = data["timestamp"]

            try:
                # Guardar valor original como temperatura_medida
                point_original = (
                    Point(config["measurement"])
                    .tag(config["tag"], config["sensor_name"])
                    .field("temperatura_medida", value)
                    .time(timestamp)
                )
                write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point_original)

                # Guardar valor calculado como temperatura_calculada
                point_calculado = (
                    Point(config["measurement"])
                    .tag(config["tag"], config["sensor_name"])
                    .field("temperatura_calculada", value + 1.5)
                    .time(timestamp)
                )
                write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point_calculado)

                print(f"✅ Guardado: medida={value}, calculada={value + 1.5} en {topic}")

            except Exception as e:
                print(f"❌ Error guardando en InfluxDB para {topic}: {e}")

        # Esperar una hora
        time.sleep(3600)

# Función periódica cada 5 segundos
def procesar_cada_5_segundos():
    while True:
        print("📥 Guardando datos cada 5 segundos...")
        for topic, data in last_values.items():
            value = data["value"]
            config = data["config"]
            timestamp = datetime.utcnow()  # Usamos el tiempo actual

            try:
                # Guardar valor como temperatura_medida_rapida
                point_rapido = (
                    Point(config["measurement"])
                    .tag(config["tag"], config["sensor_name"])
                    .field("temperatura_medida_rapida", value)
                    .time(timestamp)
                )
                write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point_rapido)

                print(f"✅ [5s] Guardado rápido: {value} en {topic}")

            except Exception as e:
                print(f"❌ [5s] Error guardando en InfluxDB para {topic}: {e}")

        time.sleep(5)

# Iniciar threads para procesamiento periódico
thread_hourly = threading.Thread(target=procesar_periodicamente, daemon=True)
thread_hourly.start()

thread_fast = threading.Thread(target=procesar_cada_5_segundos, daemon=True)
thread_fast.start()

# Conectar a MQTT y comenzar loop
mqtt_client = mqtt.Client()
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT)

# Suscribirse a todos los topics definidos en el JSON
for topic in topics_config.keys():
    mqtt_client.subscribe(topic)
    print(f"📡 Suscrito a {topic}")

print("🚀 Escuchando MQTT...")
mqtt_client.loop_forever()
# # Iniciar thread para procesamiento periódico
# thread = threading.Thread(target=procesar_periodicamente, daemon=True)
# thread.start()

# # Conectar a MQTT
# mqtt_client = mqtt.Client()
# mqtt_client.on_message = on_message
# mqtt_client.connect(MQTT_BROKER, MQTT_PORT)

# # Suscribirse a todos los topics definidos en el JSON
# for topic in topics_config.keys():
#     mqtt_client.subscribe(topic)
#     print(f"📡 Suscrito a {topic}")

# print("🚀 Escuchando MQTT...")
# mqtt_client.loop_forever()
