/*
 * ESP32 MQTT Ultrasonic Sensor and LED Controller
 * Multi-file OOP structure.
 */

#include "UltrasonicSensor.h"
#include "LedController.h"
#include "MqttPublisher.h"
#include "MqttSubscriber.h"
#include "MqttManager.h"

// ---------------------------- Configuration ----------------------------
const char* WIFI_SSID = "HONORX7";
const char* WIFI_PASSWORD = "71767607";

const char* MQTT_BROKER = "broker.hivemq.com";
const int   MQTT_PORT = 1883;
const char* MQTT_USERNAME = "";
const char* MQTT_PASSWORD = "";

const char* TOPIC_DISTANCE = "home/garden/UCBBOL/IotEC3Mqttdistance";
const char* TOPIC_LED_CMD   = "home/garden/UCBBOL/IotEC3Mqttactuator";

#define TRIG_PIN   5
#define ECHO_PIN   18
#define MAX_DIST   400

#define LED1_PIN   25
#define LED2_PIN   26
#define LED3_PIN   27

// ---------------------------- Global Objects ----------------------------
UltrasonicSensor ultrasonic(TRIG_PIN, ECHO_PIN, MAX_DIST);
LedController leds(LED1_PIN, LED2_PIN, LED3_PIN);
MqttManager mqttManager(MQTT_BROKER, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD);

MqttPublisher* publisher = nullptr;
MqttSubscriber* subscriber = nullptr;

unsigned long lastPublishTime = 0;
const unsigned long PUBLISH_INTERVAL = 2000;

// ------------------------------------------------------------------------
void setup() {
    Serial.begin(115200);

    mqttManager.connectWiFi(WIFI_SSID, WIFI_PASSWORD);
    if (mqttManager.connectMqtt()) {
        publisher = new MqttPublisher(mqttManager.getClient());
        subscriber = new MqttSubscriber(mqttManager.getClient(), leds);
        subscriber->begin(TOPIC_LED_CMD);
    }

    Serial.println("System initialized. Publishing distance to " + String(TOPIC_DISTANCE));
}

void loop() {
    mqttManager.loop();

    unsigned long now = millis();
    if (now - lastPublishTime >= PUBLISH_INTERVAL) {
        lastPublishTime = now;

        unsigned int distance = ultrasonic.getDistanceCm();
        if (distance > 0) {
            Serial.print("Distance: ");
            Serial.print(distance);
            Serial.println(" cm");
            if (publisher) {
                publisher->publishInt(TOPIC_DISTANCE, distance);
            }
        } else {
            Serial.println("Ultrasonic sensor out of range or error.");
        }
    }
}