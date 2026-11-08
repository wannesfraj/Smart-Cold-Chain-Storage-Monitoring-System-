#include "console.h"

#include <Arduino.h>
#include <ctype.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

namespace sccs {
namespace {
char buffer[80];
size_t used = 0;
bool overflowing = false;

void printConfig(const Config& c) {
  Serial.printf("CONFIG ON=%.2f OFF=%.2f HIGH=%.2f CLEAR=%.2f DOOR=%lus LUX=%.0f\n",
                c.coolingOnC, c.coolingOffC, c.criticalC, c.criticalClearC,
                static_cast<unsigned long>(c.doorTimeoutMs / 1000), c.lightAlarmLux);
}

void execute(char* command, Config& config) {
  for (char* p = command; *p; ++p) *p = toupper(static_cast<unsigned char>(*p));
  if (strcmp(command, "HELP") == 0) {
    Serial.println("HELP | CONFIG | RESET | SET ON/OFF/HIGH/CLEAR/DOOR/LUX valeur");
    Serial.println("Temperatures en C, DOOR entier en secondes, configuration en RAM.");
    return;
  }
  if (strcmp(command, "CONFIG") == 0) { printConfig(config); return; }
  if (strcmp(command, "RESET") == 0) {
    config = Config{};
    Serial.println("OK RESET");
    printConfig(config);
    return;
  }
  char verb[12], key[12], extra;
  float value = 0;
  if (sscanf(command, "%11s %11s %f %c", verb, key, &value, &extra) != 3 ||
      strcmp(verb, "SET") != 0 || !isfinite(value)) {
    Serial.println("ERR syntaxe ; taper HELP");
    return;
  }
  Config next = config;
  if (strcmp(key, "ON") == 0) next.coolingOnC = value;
  else if (strcmp(key, "OFF") == 0) next.coolingOffC = value;
  else if (strcmp(key, "HIGH") == 0) next.criticalC = value;
  else if (strcmp(key, "CLEAR") == 0) next.criticalClearC = value;
  else if (strcmp(key, "LUX") == 0) next.lightAlarmLux = value;
  else if (strcmp(key, "DOOR") == 0 && value >= 1 && value <= 300 && floorf(value) == value) {
    next.doorTimeoutMs = static_cast<uint32_t>(value) * 1000;
  } else {
    Serial.println("ERR parametre ; DOOR entier de 1 a 300");
    return;
  }
  if (!validConfig(next)) {
    Serial.println("ERR seuils : -55<=OFF<ON<HIGH<=125 ; OFF<=CLEAR<HIGH ; LUX 1..100000");
    return;
  }
  config = next;
  Serial.println("OK SET");
  printConfig(config);
}
}  // namespace

void beginConsole() {
  Serial.begin(115200);
  Serial.println("SCCS READY - HELP pour les commandes");
  printConfig(Config{});
}

void updateConsole(Config& config) {
  // Un flot serie ne peut monopoliser la boucle principale.
  for (uint8_t budget = 0; budget < 32 && Serial.available(); ++budget) {
    const char c = static_cast<char>(Serial.read());
    if (c == '\r') continue;
    if (c == '\n') {
      if (overflowing) Serial.println("ERR commande trop longue");
      else if (used) { buffer[used] = '\0'; execute(buffer, config); }
      used = 0;
      overflowing = false;
    } else if (!overflowing) {
      if (used < sizeof(buffer) - 1) buffer[used++] = c;
      else overflowing = true;
    }
  }
}

void printStatus(const Measurements& d, const Status& s, uint32_t now) {
  Serial.printf("STATUS t_ms=%lu storage=", static_cast<unsigned long>(now));
  if (s.storageUsable) Serial.print(d.storageC, 2); else Serial.print("NA");
  Serial.print(" ambient=");
  if (d.ambientValid) Serial.print(d.ambientC, 1); else Serial.print("NA");
  Serial.print(" humidity=");
  if (d.ambientValid) Serial.print(d.humidity, 1); else Serial.print("NA");
  Serial.printf(" lux=%.1f door=%s door_s=%lu state=%s cooling=%u alarms=",
                d.lux, d.doorOpen ? "OPEN" : "CLOSED",
                static_cast<unsigned long>(s.doorOpenMs / 1000),
                stateName(s.state), s.cooling ? 1 : 0);
  if (!s.alarms) Serial.print("NONE");
  bool separator = false;
  const uint8_t bits[] = {TEMPERATURE, DOOR_TIMEOUT, LIGHT_ON, STORAGE_FAULT};
  const char* names[] = {"TEMP", "DOOR", "LIGHT", "SENSOR"};
  for (uint8_t i = 0; i < 4; ++i) {
    if (!(s.alarms & bits[i])) continue;
    if (separator) Serial.print('|');
    Serial.print(names[i]);
    separator = true;
  }
  Serial.println();
}

}  // namespace sccs
