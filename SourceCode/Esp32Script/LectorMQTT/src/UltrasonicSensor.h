#ifndef ULTRASONIC_SENSOR_H
#define ULTRASONIC_SENSOR_H

#include <NewPing.h>

class UltrasonicSensor {
private:
    NewPing sonar;

public:
    UltrasonicSensor(uint8_t trigPin, uint8_t echoPin, unsigned int maxDist);
    unsigned int getDistanceCm();
};

#endif