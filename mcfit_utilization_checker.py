import requests
import json
from configparser import ConfigParser
import paho.mqtt.client as mqtt

studios = {
    "Giesing": 1879795550,
    "Laim": 1882151370,
    "Schwabing": 1858374200,
    "Forstenried": 1858377100,
}

def read_config():
    cfg = ConfigParser()
    configpath = "/opt/python/mqtt.ini"
    cfg.read(configpath)
    if cfg.sections() == []:
        print("MQTT: empty config")
    return cfg

def create_mqtt_client(config):
    mqtt_user = config.get("mqtt", "user")
    mqtt_password = config.get("mqtt", "password")
    mqtt_client = mqtt.Client("mcfit")
    mqtt_client.username_pw_set(mqtt_user, mqtt_password)
    mqtt_client.connect(host="localhost")
    return mqtt_client

headers = {
    "authority": "my.mcfit.com",
    "referer": "https://my.mcfit.com/studio/cnNnLWdyb3VwOjE4Nzk3OTU1NTA%3D?v=1",
    "x-public-facility-group": "MCFIT-2DBEBDE87C264635B943F583D13156C0",
    "x-tenant": "rsg-group",
}

if __name__ == "__main__":
    config = read_config()
    mqtt_client = create_mqtt_client(config)

    for studio_name, studio_id in studios.items():
        address = f"https://my.mcfit.com/nox/public/v1/studios/{studio_id}/utilization"
        response = requests.get(address, headers=headers)

        utilization_dict = json.loads(response.text)
        utilization = [
            entry["percentage"]
            for entry in utilization_dict["items"]
            if entry["isCurrent"]
        ][0]

        print(studio_name, utilization)

        ha_config = {
            "unique_id": f"mcfit/utilization_{studio_name.lower()}",
            "state_topic": f"mcfit/utilization_{studio_name.lower()}",
            "name": f"McFit Utilization {studio_name}",
            "device": {
                "identifiers": [
                    "mcfit",
                ],
                "manufacturer": "Jule",
                "model": "McFit",
                "name": "McFit",
            },
            "expire_after": 2100,
            "force_update": True,
            "icon": "mdi:dumbbell",
            "unit_of_measurement": "%",
        }
        topic_config = (
            f"homeassistant/sensor/mcfit/utilization_{studio_name.lower()}/config"
        )
        mqtt_client.publish(topic_config, json.dumps(ha_config), retain=True)

        topic = f"mcfit/utilization_{studio_name.lower()}"
        payload = utilization
        mqtt_client.publish(topic, payload)
