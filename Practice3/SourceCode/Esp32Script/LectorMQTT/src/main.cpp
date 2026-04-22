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
const unsigned long PUBLISH_INTERVAL = 2000;  // Measurement interval

int lastRangeIndex = -1;   // -1 means no valid range has been published yet

// ------------------------------------------------------------------------
// Helper function: map distance (cm) to a range index.
// Returns:
//   0 for distances in (0, 10] cm
//   1 for distances in (10, 20] cm
//   2 for distances in (20, 30] cm
//  -1 for any other value (including 0 = out of range / error)
int getRangeIndex(unsigned int distance) {
    if (distance > 0 && distance <= 10) {
        return 0;
    } else if (distance > 10 && distance <= 20) {
        return 1;
    } else if (distance > 20 && distance <= 30) {
        return 2;
    } else {
        return -1;   // invalid range
    }
}

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
    Serial.println("Valid ranges: 0-10 cm, 10-20 cm, 20-30 cm.");
    Serial.println("Messages will be sent only when the distance moves between these ranges.");
}

void loop() {
    mqttManager.loop();

    unsigned long now = millis();
    if (now - lastPublishTime >= PUBLISH_INTERVAL) {
        lastPublishTime = now;

        unsigned int distance = ultrasonic.getDistanceCm();
        int currentRange = getRangeIndex(distance);

        // Only consider valid ranges
        if (currentRange != -1) {
            // Publish if the range index has changed
            if (currentRange != lastRangeIndex) {
                Serial.print("Range changed! New distance: ");
                Serial.print(distance);
                Serial.print(" cm -> range ");
                Serial.println(currentRange);

                if (publisher) {
                    publisher->publishInt(TOPIC_DISTANCE, distance);
                }
                lastRangeIndex = currentRange;
            } else {
                Serial.print("Same range (");
                Serial.print(distance);
                Serial.println(" cm) - not publishing");
            }
        } else {
            // Invalid range: if we previously were in a valid range, we might want to note it,
            // but no publication occurs.
            if (lastRangeIndex != -1) {
                Serial.println("Distance left valid ranges. No publication.");
                lastRangeIndex = -1;
            } else {
                if (distance == 0) {
                    Serial.println("Sensor out of range or error.");
                } else {
                    Serial.print("Distance ");
                    Serial.print(distance);
                    Serial.println(" cm is outside valid ranges (0-10, 10-20, 20-30).");
                }
            }
        }
    }
}