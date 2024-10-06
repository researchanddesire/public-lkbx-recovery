#include "Arduino.h"

void setup() {
    Serial.begin(115200);
}

void loop() {
    Serial.println("LKBX Ready to upload firmware.");
    delay(1000);
}