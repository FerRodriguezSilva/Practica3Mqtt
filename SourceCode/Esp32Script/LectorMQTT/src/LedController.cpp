#include "LedController.h"

LedController::LedController(uint8_t pin1, uint8_t pin2, uint8_t pin3) {
    ledPins[0] = pin1;
    ledPins[1] = pin2;
    ledPins[2] = pin3;

    for (int i = 0; i < 3; i++) {
        pinMode(ledPins[i], OUTPUT);
        digitalWrite(ledPins[i], LOW);
    }
}

void LedController::allOff() {
    for (int i = 0; i < 3; i++) {
        digitalWrite(ledPins[i], LOW);
    }
}

void LedController::handleCommand(const String& command) {
    allOff();

    if (command == "1") {
        digitalWrite(ledPins[0], HIGH);
        Serial.println("LED 1 ON");
    }
    else if (command == "2") {
        digitalWrite(ledPins[1], HIGH);
        Serial.println("LED 2 ON");
    }
    else if (command == "3") {
        digitalWrite(ledPins[2], HIGH);
        Serial.println("LED 3 ON");
    }
    else {
        Serial.println("All LEDs OFF");
    }
}