#ifndef MQTT_PUBLISHER_H
#define MQTT_PUBLISHER_H

#include <PubSubClient.h>

class MqttPublisher {
private:
    PubSubClient& client;

public:
    MqttPublisher(PubSubClient& mqttClient);
    bool publish(const char* topic, const char* payload);
    bool publishInt(const char* topic, int value);
};

#endif