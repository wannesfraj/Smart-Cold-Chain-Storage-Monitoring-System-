#include <Arduino.h>

#include "alarm.h"
#include "config.h"
#include "console.h"
#include "controller.h"
#include "display.h"
#include "sensors.h"

namespace {
sccs::Config config;
sccs::Sensors sensors;
sccs::Controller controller;
sccs::Status previous;
uint32_t lastPrintedAt = 0;
bool firstPrint = true;
}  // namespace

void setup() {
  sccs::beginOutputs();
  sccs::beginConsole();
  sccs::beginDisplay();
  sensors.begin(millis());
  controller.begin(millis());
}

void loop() {
  sccs::updateConsole(config);
  sensors.update(millis());
  const uint32_t now = millis();
  const sccs::Measurements& data = sensors.data();
  const sccs::Status status = controller.update(data, config, now);
  sccs::updateOutputs(status, now);
  sccs::updateDisplay(data, status, config, now);

  if (firstPrint || status.state != previous.state ||
      status.alarms != previous.alarms || status.cooling != previous.cooling ||
      sccs::elapsed(now, lastPrintedAt) >= sccs::timing::SERIAL_PERIOD_MS) {
    sccs::printStatus(data, status, now);
    lastPrintedAt = now;
    firstPrint = false;
  }
  previous = status;
}
