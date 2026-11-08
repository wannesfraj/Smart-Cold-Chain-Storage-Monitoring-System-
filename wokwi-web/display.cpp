#include "display.h"

#include <Arduino.h>
#include <LiquidCrystal_I2C.h>
#include <Wire.h>
#include <stdio.h>
#include <string.h>

namespace sccs {
namespace {
LiquidCrystal_I2C lcd(0x27, 16, 2);
uint32_t refreshedAt = 0;
bool firstRefresh = true;

void writeLine(uint8_t row, const char* text) {
  char padded[17];
  memset(padded, ' ', 16);
  padded[16] = '\0';
  const size_t length = strlen(text);
  memcpy(padded, text, length < 16 ? length : 16);
  lcd.setCursor(0, row);
  lcd.print(padded);
}

uint8_t visibleAlarm(uint8_t alarms, uint32_t page) {
  uint8_t count = 0;
  for (uint8_t bit = 1; bit <= STORAGE_FAULT; bit <<= 1) {
    if (alarms & bit) ++count;
  }
  if (count == 0) return NO_ALARM;
  uint8_t target = page % count;
  for (uint8_t bit = 1; bit <= STORAGE_FAULT; bit <<= 1) {
    if ((alarms & bit) && target-- == 0) return bit;
  }
  return NO_ALARM;
}
}  // namespace

void beginDisplay() {
  Wire.begin(pins::LCD_SDA, pins::LCD_SCL);
  lcd.init();
  lcd.backlight();
}

void updateDisplay(const Measurements& d, const Status& s,
                   const Config& c, uint32_t now) {
  if (!firstRefresh && elapsed(now, refreshedAt) < timing::DISPLAY_PERIOD_MS) return;
  firstRefresh = false;
  refreshedAt = now;
  char line[40];
  if (s.storageUsable) {
    snprintf(line, sizeof(line), "T:%5.1fC %-6s", d.storageC, stateLabel(s.state));
  } else {
    snprintf(line, sizeof(line), "T: --.-C %-6s", stateLabel(s.state));
  }
  writeLine(0, line);

  if (s.alarms != NO_ALARM) {
    switch (visibleAlarm(s.alarms, now / 2000)) {
      case TEMPERATURE: snprintf(line, sizeof(line), "TEMP CRITIQUE"); break;
      case DOOR_TIMEOUT:
        snprintf(line, sizeof(line), "PORTE > %lus", static_cast<unsigned long>(c.doorTimeoutMs / 1000));
        break;
      case LIGHT_ON: snprintf(line, sizeof(line), "LUMIERE ALLUMEE"); break;
      case STORAGE_FAULT: snprintf(line, sizeof(line), "DEFAUT SONDE"); break;
      default: line[0] = '\0'; break;
    }
  } else if (d.doorOpen) {
    snprintf(line, sizeof(line), "OUVERTE %lus F:%u",
             static_cast<unsigned long>(s.doorOpenMs / 1000), s.cooling ? 1 : 0);
  } else if ((now / 3000) % 3 == 1) {
    if (d.ambientValid) {
      snprintf(line, sizeof(line), "A:%.1fC H:%.0f%%", d.ambientC, d.humidity);
    } else {
      snprintf(line, sizeof(line), "DHT:INDISPONIBLE");
    }
  } else if ((now / 3000) % 3 == 2) {
    snprintf(line, sizeof(line), "L:%.0flx F:%u", d.lux, s.cooling ? 1 : 0);
  } else {
    snprintf(line, sizeof(line), "PORTE FERMEE F:%u", s.cooling ? 1 : 0);
  }
  writeLine(1, line);
}

}  // namespace sccs
