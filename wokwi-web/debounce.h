#pragma once

#include "config.h"

namespace sccs {

class DebouncedInput {
 public:
  void begin(bool value, uint32_t now) {
    stable_ = candidate_ = value;
    changedAt_ = now;
  }

  bool update(bool value, uint32_t now) {
    if (value != candidate_) {
      candidate_ = value;
      changedAt_ = now;
    }
    if (elapsed(now, changedAt_) >= timing::DEBOUNCE_MS) {
      stable_ = candidate_;
    }
    return stable_;
  }

 private:
  bool stable_ = false;
  bool candidate_ = false;
  uint32_t changedAt_ = 0;
};

}  // namespace sccs
