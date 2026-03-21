#include <Wire.h>
#include "Mona_ESP_lib.h"
#include <WiFi.h>
#include <WiFiUdp.h>

#define BOT_ID      1              // CHANGE to 1, 2, or 3 per bot
#define WIFI_SSID   "TP-Link_6C24" // change to hackathon AP on the day
#define WIFI_PASS   "17346559"
#define LISTEN_PORT (5000 + BOT_ID)
#define WATCHDOG_MS 500

WiFiUDP udp;
int leftSpeed  = 0;
int rightSpeed = 0;
unsigned long lastCmdTime = 0;

void set_wheel(int left, int right) {
  if (left > 0)        Left_mot_forward(left);
  else if (left < 0)   Left_mot_backward(-left);
  else                 Left_mot_stop();

  if (right > 0)       Right_mot_forward(right);
  else if (right < 0)  Right_mot_backward(-right);
  else                 Right_mot_stop();
}

void setup() {
  Serial.begin(115200);
  Mona_ESP_init();

  Set_LED(1, 255, 80, 0);
  Set_LED(2, 255, 80, 0);

  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print(".");
  }

  Serial.printf("\nBot %d ready! IP: %s  Port: %d\n",
                BOT_ID,
                WiFi.localIP().toString().c_str(),
                LISTEN_PORT);

  udp.begin(LISTEN_PORT);

  Set_LED(1, 0, 220, 0);
  Set_LED(2, 0, 220, 0);
}

void loop() {
  int packetSize = udp.parsePacket();
  if (packetSize > 0) {
    char buf[64];
    int len = udp.read(buf, sizeof(buf) - 1);
    buf[len] = '\0';
    parseCommand(buf);
    lastCmdTime = millis();
  }

  if (millis() - lastCmdTime > WATCHDOG_MS) {
    leftSpeed  = 0;
    rightSpeed = 0;
    Set_LED(1, 255, 0, 0);
    Set_LED(2, 255, 0, 0);
  } else {
    Set_LED(1, 0, 220, 0);
    Set_LED(2, 0, 220, 0);
  }

  set_wheel(leftSpeed, rightSpeed);
  delay(10);
}

void parseCommand(const char* cmd) {
  int l = 0, r = 0;

  if (sscanf(cmd, "L%d R%d", &l, &r) == 2) {
    leftSpeed  = constrain(l, -255, 255);
    rightSpeed = constrain(r, -255, 255);
    Serial.printf("Bot %d: L=%d R=%d\n", BOT_ID, leftSpeed, rightSpeed);

  } else if (strncmp(cmd, "STOP", 4) == 0) {
    leftSpeed  = 0;
    rightSpeed = 0;
    Serial.printf("Bot %d: STOP\n", BOT_ID);
  }
}
