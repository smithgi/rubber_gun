#include <Arduino.h>
 
#define RX_PIN 0
#define TX_PIN 1
#define BAUD_RATE 256000
 
// Variables
uint8_t RX_BUF[64] = {0};
uint8_t RX_count = 0;
uint8_t RX_temp = 0;
 
// Target details
int16_t target1_x = 0, target1_y = 0;
int16_t target1_speed = 0;
uint16_t target1_distance_res = 0;
float target1_distance = 0;
float target1_angle =0;
 
// Single-Target Detection Commands
uint8_t Single_Target_Detection_CMD[12] = {0xFD, 0xFC, 0xFB, 0xFA, 0x02, 0x00, 0x80, 0x00, 0x04, 0x03, 0x02, 0x01};
uint8_t Multi_Target_Detection_CMD[12] = {0xFD, 0xFC, 0xFB, 0xFA, 0x02, 0x00, 0x90, 0x00, 0x04, 0x03, 0x02, 0x01};


void setup() {
    Serial.begin(115200);                  // Debugging
    Serial.println("Running setup");
    Serial1.begin();
    Serial.println("RD-03D Radar Module Initialized");
 
    // Send single-target detection command
    Serial1.write(Single_Target_Detection_CMD, sizeof(Single_Target_Detection_CMD));
    delay(200);
    Serial.println("Single-target detection mode activated.");
 
    RX_count = 0;
    Serial1.flush();
}
 
void processRadarData() {
 
   // output data
   //printBuffer();
 
   /* RX_BUF: 0xAA 0xFF 0x03 0x00                   Header
    *  0x05 0x01 0x19 0x82 0x00 0x00 0x68 0x01      target1
    *  0xE3 0x81 0x33 0x88 0x20 0x80 0x68 0x01      target2
    *  0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00      target3
    *  0x55 0xCC
  */
    if (RX_count >= 32) {
        // Extract data for Target 1
        target1_x = (RX_BUF[4] | (RX_BUF[5] << 8)) - 0x200;
        target1_y = (RX_BUF[6] | (RX_BUF[7] << 8)) - 0x8000;
        target1_speed = (RX_BUF[8] | (RX_BUF[9] << 8)) - 0x10;
        target1_distance_res = (RX_BUF[10] | (RX_BUF[11] << 8));
        target1_distance = sqrt(pow(target1_x, 2) + pow(target1_y, 2));
        target1_angle = atan2(target1_y, target1_x) * 180.0 / PI;
 
        Serial.print("Target 1 - Distance: ");
        Serial.print(target1_distance / 10.0);
        Serial.print(" cm, Angle: ");
        Serial.print(target1_angle);
        Serial.print(" degrees, X: ");
        Serial.print(target1_x);
        Serial.print(" mm, Y: ");
        Serial.print(target1_y);
        Serial.print(" mm, Speed: ");
        Serial.print(target1_speed);
        Serial.print(" cm/s, Distance Resolution: ");
        Serial.print(target1_distance_res);
        Serial.println(" mm");
 
        
        // Reset buffer and counter
        memset(RX_BUF, 0x00, sizeof(RX_BUF));
        RX_count = 0;
    }
}
 
void loop() {
    // Read data from Serial1
    while (Serial1.available()) {
        RX_temp = Serial1.read();
        RX_BUF[RX_count++] = RX_temp;
 
        // Prevent buffer overflow
        if (RX_count >= sizeof(RX_BUF)) {
            RX_count = sizeof(RX_BUF) - 1;
        }
 
        // Check for end of frame (0xCC, 0x55)
        if ((RX_count > 1) && (RX_BUF[RX_count - 1] == 0xCC) && (RX_BUF[RX_count - 2] == 0x55)) {
            processRadarData();
        }
    }
}
 
 
 
// Function to print buffer contents
void printBuffer() {
    Serial.print("RX_BUF: ");
    for (int i = 0; i < RX_count; i++) {
        Serial.print("0x");
        if (RX_BUF[i] < 0x10) Serial.print("0");  // Add leading zero for single-digit hex values
        Serial.print(RX_BUF[i], HEX);
        Serial.print(" ");
    }
    Serial.println();
}