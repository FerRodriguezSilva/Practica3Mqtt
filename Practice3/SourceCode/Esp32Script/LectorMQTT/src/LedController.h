#ifndef LED_CONTROLLER_H
#define LED_CONTROLLER_H

#include <Arduino.h>

class LedController {
private:
    uint8_t ledPins[3];

public:
    LedController(uint8_t pin1, uint8_t pin2, uint8_t pin3);
    void allOff();
    void handleCommand(const String& command);
};

#endif