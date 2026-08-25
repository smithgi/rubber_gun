#include <ESP32Servo.h>
#include <string.h>

Servo upServo;
Servo turnServo;
Servo triggerServo;

const int SERVO1_PIN = 18;
const int SERVO2_PIN = 19;
const int TRIGGER_SERVO_PIN = 5;

const int TRIGGER_FIRE_DEG = 50;
const int TRIGGER_IDLE_DEG = 0;

int upServoPos = 90;
int turnServoPos = 90;
int triggerServoPos = TRIGGER_IDLE_DEG;

int upServoStartPos = 0;
int turnServoStartPos = 90;

int servoSpeed = 1;

bool useFastMovement = true;

// UART command buffer: {"h":90,"v":90}
#define CMD_BUFFER_LEN 64
char cmdBuffer[CMD_BUFFER_LEN];

bool parseJsonAngles(char* buf, int* turnAngle, int* upAngle) {
  // Format: {"h":<angle>,"v":<angle>}
  int h = -1, v = -1;
  char* p;

  if ((p = strstr(buf, "\"h\":")) != NULL || (p = strstr(buf, "\"H\":")) != NULL) {
    p += 4;  // skip past "h":
    h = atoi(p);
  }
  if ((p = strstr(buf, "\"v\":")) != NULL || (p = strstr(buf, "\"V\":")) != NULL) {
    p += 4;  // skip past "v":
    v = atoi(p);
  }

  if (h >= 0 && h <= 180 && v >= 0 && v <= 180) {
    *turnAngle = h;
    *upAngle = v;
    return true;
  }
  return false;
}

bool parseShoot(char* buf) {
  char* p = strstr(buf, "\"shoot\":");
  if (p == NULL) {
    p = strstr(buf, "\"SHOOT\":");
  }
  if (p == NULL) return false;
  p += 8;
  while (*p == ' ' || *p == '\t') p++;
  return strncmp(p, "true", 4) == 0;
}

bool parseTriggerPos(char* buf, int* deg) {
  char* p = strstr(buf, "\"trigger_pos\"");
  if (p == NULL) p = strstr(buf, "\"TRIGGER_POS\"");
  if (p == NULL) return false;
  p = strchr(p, ':');
  if (p == NULL) return false;
  p++;
  while (*p == ' ' || *p == '\t') p++;
  int v = atoi(p);
  if (v >= 0 && v <= 180) {
    *deg = v;
    return true;
  }
  return false;
}

void fireTrigger() {
  triggerServo.write(TRIGGER_FIRE_DEG);
  triggerServoPos = TRIGGER_FIRE_DEG;
  delay(500);
  triggerServo.write(TRIGGER_IDLE_DEG);
  triggerServoPos = TRIGGER_IDLE_DEG;
}

void setup() {
  Serial.begin(115200);

  upServo.setPeriodHertz(50);
  turnServo.setPeriodHertz(50);
  triggerServo.setPeriodHertz(50);

  upServo.attach(SERVO1_PIN, 500, 2400);
  turnServo.attach(SERVO2_PIN, 500, 2400);
  triggerServo.attach(TRIGGER_SERVO_PIN, 500, 2400);

  upServo.write(upServoPos);
  turnServo.write(turnServoPos);
  triggerServo.write(TRIGGER_IDLE_DEG);
  triggerServoPos = TRIGGER_IDLE_DEG;

  moveSmooth(upServo, upServoPos, upServoStartPos, servoSpeed);
  moveSmooth(turnServo, upServoPos, turnServoStartPos, servoSpeed);

  delay(1000);
}

void loop() {
  // Read UART commands: {"h":90,"v":90}
  if (Serial.available() > 0) {
    int idx = 0;
    memset(cmdBuffer, 0, CMD_BUFFER_LEN);

    while (Serial.available() > 0 && idx < CMD_BUFFER_LEN - 1) {
      char c = Serial.read();
      if (c == '\n' || c == '\r') break;
      cmdBuffer[idx++] = c;
    }
    cmdBuffer[idx] = '\0';

    if (idx > 0) {
      int newTurn, newUp;
      int triggerDeg;
      bool anglesOk = parseJsonAngles(cmdBuffer, &newTurn, &newUp);
      bool shoot = parseShoot(cmdBuffer);
      bool triggerPosOk = parseTriggerPos(cmdBuffer, &triggerDeg);

      if (!anglesOk && !shoot && !triggerPosOk) {
        Serial.println("{\"err\":\"invalid\"}");
      } else {
        if (anglesOk) {
          if (useFastMovement) {
            moveFast(turnServo, newTurn);
            turnServoPos = newTurn;

            moveFast(upServo, newUp);
            upServoPos = newUp;

            Serial.printf("{\"h\":%d,\"v\":%d}\n", newTurn, newUp);
          } else {
            moveSmooth(turnServo, turnServoPos, newTurn, servoSpeed);
            turnServoPos = newTurn;

            moveSmooth(upServo, upServoPos, newUp, servoSpeed);
            upServoPos = newUp;

            Serial.printf("{\"h\":%d,\"v\":%d}\n", turnServoPos, upServoPos);
          }
        }
        if (triggerPosOk) {
          moveFast(triggerServo, triggerDeg);
          triggerServoPos = triggerDeg;
        }
        if (shoot) {
          fireTrigger();
        }
        if (!anglesOk) {
          if (triggerPosOk && shoot) {
            Serial.printf("{\"trigger_pos\":%d,\"shoot\":true}\n", triggerDeg);
          } else if (triggerPosOk) {
            Serial.printf("{\"trigger_pos\":%d}\n", triggerDeg);
          } else if (shoot) {
            Serial.println("{\"shoot\":true}");
          }
        }
      }
    }
  }
  delay(10);
}

void moveSmooth(Servo &servo, int fromPos, int toPos, int stepDelayMs) {
  if (fromPos < toPos) {
    for (int pos = fromPos; pos <= toPos; pos++) {
      servo.write(pos);
      delay(stepDelayMs);
    }
  } else {
    for (int pos = fromPos; pos >= toPos; pos--) {
      servo.write(pos);
      delay(stepDelayMs);
    }
  }
}

void moveFast(Servo &servo, int toPos) {
  servo.write(toPos);
}
