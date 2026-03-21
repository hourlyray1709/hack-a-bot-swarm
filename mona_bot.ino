#include <Wire.h>
#include "Mona_ESP_lib.h"   //← real lib
#include <WiFi.h>
#include <WiFiUdp.h>

#define BOT_ID      1      //  ← change to 1, 2, or 3 per bot
#define WIFI_SSID   "eduroam"
#define WIFI_PASS   "1234"
#define LISTEN_PORT (5000 + BOT_ID) // ← auto: 5001, 5002, 5003
#define WATCHDOG_MS 500 