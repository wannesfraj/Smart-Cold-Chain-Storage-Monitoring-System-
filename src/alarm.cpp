#include "alarm.h"

#include <Arduino.h>
#include <esp_arduino_version.h>

#include "config.h"

namespace sccs {
namespace {
constexpr uint8_t BUZZER_CHANNEL = 0;
bool buzzing = false;

void setBuzzer(bool active) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWriteTone(pins::BUZZER, active ? 2000 : 0);
#else
  ledcWriteTone(BUZZER_CHANNEL, active ? 2000 : 0);
#endif
}
}  // namespace

void beginOutputs() {
  for (uint8_t pin : {pins::LED_NORMAL, pins::COOLING, pins::LED_ALARM}) {
    pinMode(pin, OUTPUT);
    digitalWrite(pin, LOW);
  }
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcAttach(pins::BUZZER, 2000, 8);
#else
  ledcSetup(BUZZER_CHANNEL, 2000, 8);
  ledcAttachPin(pins::BUZZER, BUZZER_CHANNEL);
#endif
  setBuzzer(false);
}

void updateOutputs(const Status& status, uint32_t now) {
  const bool alarm = status.alarms != NO_ALARM;
  digitalWrite(pins::COOLING, status.cooling ? HIGH : LOW);
  digitalWrite(pins::LED_NORMAL, status.state == State::NORMAL ? HIGH : LOW);
  digitalWrite(pins::LED_ALARM, alarm && (now % 500 < 250) ? HIGH : LOW);
  const bool shouldBuzz = alarm && (now % 1000 < 250);
  if (shouldBuzz != buzzing) {
    setBuzzer(shouldBuzz);
    buzzing = shouldBuzz;
  }
}

}  // namespace sccs
