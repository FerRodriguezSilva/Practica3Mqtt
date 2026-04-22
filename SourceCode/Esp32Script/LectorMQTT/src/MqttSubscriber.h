#ifndef MQTT_SUBSCRIBER_H
#define MQTT_SUBSCRIBER_H

#include <PubSubClient.h>
#include "LedController.h"

class MqttSubscriber {
private:
    PubSubClient& client;
    LedController& leds;

    void callback(char* topic, byte* payload, unsigned int length);

public:
    MqttSubscriber(PubSubClient& mqttClient, LedController& ledController);
    void begin(const char* topic);
    bool subscribe(const char* topic);
};

#endif