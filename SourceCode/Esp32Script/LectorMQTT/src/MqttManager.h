#ifndef MQTT_MANAGER_H
#define MQTT_MANAGER_H

#include <WiFi.h>
#include <PubSubClient.h>

class MqttManager {
private:
    WiFiClient wifiClient;
    PubSubClient mqttClient;
    const char* broker;
    int port;
    const char* username;
    const char* password;
    String clientId;

    void reconnect();

public:
    MqttManager(const char* mqttBroker, int mqttPort, const char* mqttUser, const char* mqttPass);
    void connectWiFi(const char* ssid, const char* pass);
    bool connectMqtt();
    void loop();
    PubSubClient& getClient();
};

#endif