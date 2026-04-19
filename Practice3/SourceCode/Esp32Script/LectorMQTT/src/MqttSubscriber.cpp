#include "MqttSubscriber.h"

MqttSubscriber::MqttSubscriber(PubSubClient& mqttClient, LedController& ledController)
    : client(mqttClient), leds(ledController) {}

void MqttSubscriber::begin(const char* topic) {
    client.setCallback([this](char* topic, byte* payload, unsigned int length) {
        this->callback(topic, payload, length);
    });
    subscribe(topic);
}

bool MqttSubscriber::subscribe(const char* topic) {
    return client.subscribe(topic);
}

void MqttSubscriber::callback(char* topic, byte* payload, unsigned int length) {
    Serial.print("Message received on topic: ");
    Serial.println(topic);

    String message;
    for (unsigned int i = 0; i < length; i++) {
        message += (char)payload[i];
    }
    Serial.print("Payload: ");
    Serial.println(message);

    leds.handleCommand(message);
}