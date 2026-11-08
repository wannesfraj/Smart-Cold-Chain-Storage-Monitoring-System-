#include "sensors.h"

#include <Arduino.h>
#include <DHTesp.h>
#include <DallasTemperature.h>
#include <OneWire.h>
#include <math.h>

#include "config.h"
#include "debounce.h"

namespace sccs {
namespace {
OneWire oneWire(pins::STORAGE);
DallasTemperature storage(&oneWire);
DHTesp ambient;
DebouncedInput door;

float readLux() {
  // Pont LDR / 10 kohms de Wokwi, alimente en 3,3 V, ADC 12 bits.
  // rl10 = 50 kohms et gamma = 0,7 (attributs du composant).
  const int raw = analogRead(pins::LIGHT);
  if (raw <= 0) return 100000.0f;
  if (raw >= 4095) return 0.0f;
  const float resistance = 10000.0f * raw / (4095.0f - raw);
  const float lux = powf(50000.0f * powf(10.0f, 0.7f) / resistance,
                         1.0f / 0.7f);
  return fminf(lux, 100000.0f);
}
}  // namespace

void Sensors::begin(uint32_t now) {
  pinMode(pins::DOOR, INPUT_PULLUP);
  pinMode(pins::LIGHT, INPUT);
  analogReadResolution(12);
  analogSetPinAttenuation(pins::LIGHT, ADC_11db);
  data_.doorOpen = digitalRead(pins::DOOR) == HIGH;
  door.begin(data_.doorOpen, now);
  data_.lux = readLux();
  ambient.setup(pins::AMBIENT, DHTesp::DHT22);
  storage.begin();
  storage.setResolution(12);
  storage.setWaitForConversion(false);
  storage.requestTemperatures();
  conversionStartedAt_ = millis();
  converting_ = true;
  ambientReadAt_ = lightReadAt_ = now;
}

void Sensors::update(uint32_t now) {
  data_.doorOpen = door.update(digitalRead(pins::DOOR) == HIGH, now);

  if (converting_ && elapsed(now, conversionStartedAt_) >=
                         timing::STORAGE_CONVERSION_MS) {
    const float value = storage.getTempCByIndex(0);
    data_.storageSampled = true;
    data_.storageValid = isfinite(value) && value != DEVICE_DISCONNECTED_C &&
                         value >= -55.0f && value <= 125.0f;
    data_.storageC = value;
    data_.storageUpdatedAt = now;
    converting_ = false;
  }
  if (!converting_ && elapsed(now, conversionStartedAt_) >=
                          timing::STORAGE_PERIOD_MS) {
    storage.requestTemperatures();
    conversionStartedAt_ = now;
    converting_ = true;
  }

  if (elapsed(now, ambientReadAt_) >= timing::AMBIENT_PERIOD_MS) {
    ambientReadAt_ = now;
    const TempAndHumidity value = ambient.getTempAndHumidity();
    data_.ambientValid = isfinite(value.temperature) && isfinite(value.humidity) &&
                         value.temperature >= -40.0f && value.temperature <= 80.0f &&
                         value.humidity >= 0.0f && value.humidity <= 100.0f;
    data_.ambientC = value.temperature;
    data_.humidity = value.humidity;
  }
  if (elapsed(now, lightReadAt_) >= timing::LIGHT_PERIOD_MS) {
    lightReadAt_ = now;
    data_.lux = readLux();
  }
}

}  // namespace sccs
