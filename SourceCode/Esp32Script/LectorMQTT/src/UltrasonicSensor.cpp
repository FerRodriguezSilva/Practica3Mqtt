#include "UltrasonicSensor.h"

UltrasonicSensor::UltrasonicSensor(uint8_t trigPin, uint8_t echoPin, unsigned int maxDist)
    : sonar(trigPin, echoPin, maxDist) {}

unsigned int UltrasonicSensor::getDistanceCm() {
    return sonar.ping_cm();
}