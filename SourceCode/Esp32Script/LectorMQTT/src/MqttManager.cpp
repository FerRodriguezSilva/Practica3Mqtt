#include "MqttManager.h"

MqttManager::MqttManager(const char* mqttBroker, int mqttPort, const char* mqttUser, const char* mqttPass)
    : mqttClient(wifiClient), broker(mqttBroker), port(mqttPort),
      username(mqttUser), password(mqttPass) {
    clientId = "ESP32Client-" + String(random(0xffff), HEX);
}

void MqttManager::connectWiFi(const char* ssid, const char* pass) {
    Serial.print("Connecting to WiFi ");
    Serial.println(ssid);
    WiFi.begin(ssid, pass);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nWiFi connected. IP address: " + WiFi.localIP().toString());
}

bool MqttManager::connectMqtt() {
    mqttClient.setServer(broker, port);
    Serial.print("Connecting to MQTT broker ");
    Serial.print(broker);
    Serial.print(":");
    Serial.print(port);
    Serial.print(" ... ");

    if (mqttClient.connect(clientId.c_str(), username, password)) {
        Serial.println("connected.");
        return true;
    } else {
        Serial.print("failed, rc=");
        Serial.println(mqttClient.state());
        return false;
    }
}

void MqttManager::loop() {
    if (!mqttClient.connected()) {
        reconnect();
    }
    mqttClient.loop();
}

void MqttManager::reconnect() {
    while (!mqttClient.connected()) {
        Serial.print("Attempting MQTT reconnection...");
        if (mqttClient.connect(clientId.c_str(), username, password)) {
            Serial.println("connected");
        } else {
            Serial.print("failed, rc=");
            Serial.print(mqttClient.state());
            Serial.println(". Retrying in 5 seconds.");
            delay(5000);
        }
    }
}

PubSubClient& MqttManager::getClient() {
    return mqttClient;
}