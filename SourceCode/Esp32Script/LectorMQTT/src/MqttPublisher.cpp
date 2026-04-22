#include "MqttPublisher.h"

MqttPublisher::MqttPublisher(PubSubClient& mqttClient) : client(mqttClient) {}

bool MqttPublisher::publish(const char* topic, const char* payload) {
    return client.publish(topic, payload);
}

bool MqttPublisher::publishInt(const char* topic, int value) {
    char buffer[16];
    snprintf(buffer, sizeof(buffer), "%d", value);
    return publish(topic, buffer);
}