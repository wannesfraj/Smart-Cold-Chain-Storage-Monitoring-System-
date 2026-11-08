#pragma once

#include <stdint.h>

namespace sccs {

namespace pins {
constexpr uint8_t STORAGE = 4;
constexpr uint8_t AMBIENT = 16;
constexpr uint8_t DOOR = 27;
constexpr uint8_t LIGHT = 34;  // ADC1 : entree uniquement.
constexpr uint8_t LCD_SDA = 21;
constexpr uint8_t LCD_SCL = 22;
constexpr uint8_t LED_NORMAL = 25;
constexpr uint8_t COOLING = 26;  // LED bleue : compresseur simule uniquement.
constexpr uint8_t LED_ALARM = 33;
constexpr uint8_t BUZZER = 32;
}  // namespace pins

namespace timing {
constexpr uint32_t STORAGE_PERIOD_MS = 1000;
constexpr uint32_t STORAGE_CONVERSION_MS = 750;  // DS18B20, 12 bits.
constexpr uint32_t STORAGE_STALE_MS = 2500;
constexpr uint32_t STARTUP_GRACE_MS = 1500;
constexpr uint32_t AMBIENT_PERIOD_MS = 2200;
constexpr uint32_t LIGHT_PERIOD_MS = 100;
constexpr uint32_t DEBOUNCE_MS = 40;
constexpr uint32_t DISPLAY_PERIOD_MS = 250;
constexpr uint32_t SERIAL_PERIOD_MS = 1000;
constexpr uint32_t LIGHT_ALARM_MS = 5000;
}  // namespace timing

struct Config {
  float coolingOnC = 6.0f;
  float coolingOffC = 4.0f;
  float criticalC = 8.0f;
  float criticalClearC = 7.5f;
  uint32_t doorTimeoutMs = 30000;
  float lightAlarmLux = 300.0f;
};

bool validConfig(const Config& config);

// La soustraction non signee reste correcte au debordement de millis().
inline uint32_t elapsed(uint32_t now, uint32_t since) {
  return now - since;
}

}  // namespace sccs
