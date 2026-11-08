#include "controller.h"

#include <math.h>

namespace sccs {

void Controller::begin(uint32_t now) {
  startedAt_ = now;
  doorOpenedAt_ = lightStartedAt_ = now;
  doorWasOpen_ = lightPending_ = critical_ = coolingDemand_ = false;
}

Status Controller::update(const Measurements& d, const Config& c, uint32_t now) {
  Status s;
  s.storageUsable = d.storageSampled && d.storageValid && isfinite(d.storageC) &&
                    d.storageC >= -55.0f && d.storageC <= 125.0f &&
                    elapsed(now, d.storageUpdatedAt) <= timing::STORAGE_STALE_MS;
  const bool waiting = !d.storageSampled &&
                       elapsed(now, startedAt_) < timing::STARTUP_GRACE_MS;
  if (!s.storageUsable && !waiting) s.alarms |= STORAGE_FAULT;

  if (s.storageUsable) {
    if (d.storageC > c.criticalC) critical_ = true;
    if (d.storageC <= c.criticalClearC) critical_ = false;
    if (d.storageC >= c.coolingOnC) coolingDemand_ = true;
    if (d.storageC <= c.coolingOffC) coolingDemand_ = false;
  } else {
    critical_ = false;
    coolingDemand_ = false;
  }
  if (critical_) s.alarms |= TEMPERATURE;

  if (d.doorOpen) {
    if (!doorWasOpen_) doorOpenedAt_ = now;
    s.doorOpenMs = elapsed(now, doorOpenedAt_);
    if (s.doorOpenMs > c.doorTimeoutMs) s.alarms |= DOOR_TIMEOUT;
  }
  doorWasOpen_ = d.doorOpen;

  // Une lumiere forte, porte fermee, suggere un eclairage oublie.
  const bool unexpectedLight = !d.doorOpen && isfinite(d.lux) &&
                               d.lux >= c.lightAlarmLux;
  if (unexpectedLight) {
    if (!lightPending_) lightStartedAt_ = now;
    lightPending_ = true;
    if (elapsed(now, lightStartedAt_) >= timing::LIGHT_ALARM_MS) {
      s.alarms |= LIGHT_ON;
    }
  } else {
    lightPending_ = false;
  }

  // L'ouverture suspend la sortie, mais conserve la demande du thermostat.
  s.cooling = s.storageUsable && coolingDemand_ && !d.doorOpen;
  if (s.alarms != NO_ALARM) s.state = State::ALARM;
  else if (waiting) s.state = State::INIT;
  else if (d.doorOpen) s.state = State::DOOR_OPEN;
  else if (s.cooling) s.state = State::COOLING;
  else s.state = State::NORMAL;
  return s;
}

const char* stateName(State state) {
  switch (state) {
    case State::INIT: return "INIT";
    case State::NORMAL: return "NORMAL";
    case State::COOLING: return "COOLING";
    case State::DOOR_OPEN: return "DOOR_OPEN";
    case State::ALARM: return "ALARM";
  }
  return "UNKNOWN";
}

const char* stateLabel(State state) {
  switch (state) {
    case State::INIT: return "INIT";
    case State::NORMAL: return "NORMAL";
    case State::COOLING: return "FROID";
    case State::DOOR_OPEN: return "PORTE";
    case State::ALARM: return "ALARME";
  }
  return "?";
}

}  // namespace sccs
