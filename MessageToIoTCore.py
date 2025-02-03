import sys
from awscrt import io, mqtt, auth, http
from awsiot import mqtt_connection_builder

# AWS IoT Core settings
ENDPOINT = "a1140mhsbiyi55-ats.iot.ap-south-1.amazonaws.com"
CLIENT_ID = "iotconsole-4bbfd858-579c-4247-bbdb-e512701f0bfb"
PATH_TO_CERT = "./1f6ac597c63b115272089fd752161bf1812d57df0b61a8d8dacb7c2983116b9c-certificate.pem.crt"
PATH_TO_KEY = "./1f6ac597c63b115272089fd752161bf1812d57df0b61a8d8dacb7c2983116b9c-public.pem.key"
PATH_TO_ROOT = "./AmazonRootCA1.pem"
TOPIC = "test/helloOrange"  # Replace with your topic

def on_message_received(topic, payload, **kwargs):
    print(f"Message received on topic '{topic}': {payload.decode('utf-8')}")

# Initialize the MQTT connection
event_loop_group = io.EventLoopGroup(1)
host_resolver = io.DefaultHostResolver(event_loop_group)
client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

mqtt_connection = mqtt_connection_builder.mtls_from_path(
    endpoint=ENDPOINT,
    cert_filepath=PATH_TO_CERT,
    pri_key_filepath=PATH_TO_KEY,
    client_bootstrap=client_bootstrap,
    ca_filepath=PATH_TO_ROOT,
    client_id=CLIENT_ID,
    clean_session=False,
    keep_alive_secs=30,
)

print(f"Connecting to {ENDPOINT}...")
connect_future = mqtt_connection.connect()
connect_future.result()
print("Connected!")

# Subscribe to the topic
print(f"Subscribing to topic '{TOPIC}'...")
subscribe_future, _ = mqtt_connection.subscribe(
    topic=TOPIC,
    qos=mqtt.QoS.AT_LEAST_ONCE,
    callback=on_message_received,
)
subscribe_future.result()
print(f"Subscribed to '{TOPIC}'!")

# Keep the script running to listen for messages
try:
    print("Listening for messages. Press Ctrl+C to exit.")
    while True:
        pass
except KeyboardInterrupt:
    print("\nDisconnecting...")
    disconnect_future = mqtt_connection.disconnect()
    disconnect_future.result()
    print("Disconnected!")