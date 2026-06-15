import os
import ssl
import json
import csv
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv
from paho.mqtt import client as mqtt

# Load environment variables
load_dotenv()

MQTT_HOST = os.getenv("MQTT_HOST", "f6f78e87db4a4c189dd3d706745a5e93.s1.eu.hivemq.cloud")
MQTT_PORT = int(os.getenv("MQTT_PORT", "8883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "DVKN2026")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "ThaiBao12A@")
MQTT_INPUT_TOPIC = os.getenv("MQTT_INPUT_TOPIC", "smart-campus/raw/access/rfid-uid")
MQTT_OUTPUT_TOPIC = os.getenv("MQTT_OUTPUT_TOPIC", "smart-campus/events/access")

WHITELIST_FILE = "uid_whitelist.csv"

# Load whitelist
whitelist = {}
def load_whitelist():
    global whitelist
    if not os.path.exists(WHITELIST_FILE):
        print(f"Error: Whitelist file '{WHITELIST_FILE}' not found.")
        return
    
    with open(WHITELIST_FILE, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            uid = row.get("uid", "").strip().upper()
            if uid:
                whitelist[uid] = {
                    "student_id": row.get("student_id"),
                    "full_name": row.get("full_name"),
                    "class_name": row.get("class_name")
                }
    print(f"Loaded {len(whitelist)} whitelisted UIDs.")

load_whitelist()

# Define callbacks using paho-mqtt v2 API
def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print(f"Successfully connected to broker {MQTT_HOST}:{MQTT_PORT}")
        # Subscribe to input topic with QoS 1
        client.subscribe(MQTT_INPUT_TOPIC, qos=1)
        print(f"Subscribed to topic: {MQTT_INPUT_TOPIC}")
    else:
        print(f"Failed to connect, reason code: {reason_code}")

def on_message(client, userdata, msg):
    try:
        payload_str = msg.payload.decode("utf-8")
        print(f"\n[Received] Topic: {msg.topic}")
        print(f"Payload: {payload_str}")
        
        # Parse JSON
        raw_event = json.loads(payload_str)
        
        # Validate required fields
        required_fields = ["event_id", "event_type", "timestamp", "uid", "door_id", "direction"]
        missing_fields = [field for field in required_fields if field not in raw_event]
        if missing_fields:
            print(f"Warning: Missing required fields: {missing_fields}. Message ignored.")
            return

        uid_raw = raw_event["uid"]
        uid_normalized = uid_raw.strip().upper()
        
        # Check against whitelist
        student_info = whitelist.get(uid_normalized)
        
        if student_info:
            access_result = "granted"
            reason = "uid_matched"
            student_id = student_info["student_id"]
            full_name = student_info["full_name"]
            class_name = student_info["class_name"]
        else:
            access_result = "denied"
            reason = "uid_not_found"
            student_id = None
            full_name = None
            class_name = None

        # Build output event
        # Format output timestamp as ISO 8601 with timezone (e.g. 2026-06-07T14:30:11+07:00)
        timestamp_str = datetime.now(timezone.utc).astimezone().isoformat()
        
        # Unique access-event ID
        processed_event_id = f"access-event-{uuid.uuid4().hex[:8]}"
        
        processed_payload = {
            "event_id": processed_event_id,
            "event_type": "access.swipe.processed",
            "source_service": "team-gate",
            "timestamp": timestamp_str,
            "raw_event_id": raw_event["event_id"],
            "uid": uid_raw,
            "student_id": student_id,
            "full_name": full_name,
            "class_name": class_name,
            "door_id": raw_event["door_id"],
            "location": raw_event.get("location", "Unknown Gate"),
            "direction": raw_event["direction"],
            "access_result": access_result,
            "reason": reason
        }
        
        # Publish output payload
        output_str = json.dumps(processed_payload, ensure_ascii=False)
        print(f"[Processed] Result: {access_result} ({reason}) for UID {uid_raw}")
        print(f"[Publishing] Topic: {MQTT_OUTPUT_TOPIC}")
        print(f"Payload: {output_str}")
        
        result = client.publish(MQTT_OUTPUT_TOPIC, output_str, qos=1)
        status = result[0]
        if status == 0:
            print("Publish successful!")
        else:
            print(f"Failed to send message to topic {MQTT_OUTPUT_TOPIC}")

    except json.JSONDecodeError:
        print("Error: Received message payload is not a valid JSON string.")
    except Exception as e:
        print(f"Error processing message: {str(e)}")

# Initialize MQTT Client with Callback API version 2
client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

# Set TLS configuration
client.tls_set(tls_version=ssl.PROTOCOL_TLS_CLIENT)

client.on_connect = on_connect
client.on_message = on_message

print(f"Connecting to MQTT Broker {MQTT_HOST}:{MQTT_PORT}...")
client.connect(MQTT_HOST, MQTT_PORT)

try:
    print("AccessGate service is running. Press Ctrl+C to stop.")
    client.loop_forever()
except KeyboardInterrupt:
    print("\nService stopped by user.")
    client.disconnect()
