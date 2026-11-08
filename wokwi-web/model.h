#pragma once

#include <stdint.h>

namespace sccs {

struct Measurements {
  float storageC = 0.0f;
  float ambientC = 0.0f;
  float humidity = 0.0f;
  float lux = 0.0f;
  bool storageSampled = false;
  bool storageValid = false;
  bool ambientValid = false;
  bool doorOpen = false;
  uint32_t storageUpdatedAt = 0;
};

enum class State : uint8_t { INIT, NORMAL, COOLING, DOOR_OPEN, ALARM };

enum Alarm : uint8_t {
  NO_ALARM = 0,
  TEMPERATURE = 1 << 0,
  DOOR_TIMEOUT = 1 << 1,
  LIGHT_ON = 1 << 2,
  STORAGE_FAULT = 1 << 3
};

struct Status {
  State state = State::INIT;
  uint8_t alarms = NO_ALARM;
  bool cooling = false;
  bool storageUsable = false;
  uint32_t doorOpenMs = 0;
};

const char* stateName(State state);
const char* stateLabel(State state);

}  // namespace sccs
