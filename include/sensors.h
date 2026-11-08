#pragma once

#include "model.h"

namespace sccs {

class Sensors {
 public:
  void begin(uint32_t now);
  void update(uint32_t now);
  const Measurements& data() const { return data_; }

 private:
  Measurements data_;
  uint32_t conversionStartedAt_ = 0;
  uint32_t ambientReadAt_ = 0;
  uint32_t lightReadAt_ = 0;
  bool converting_ = false;
};

}  // namespace sccs
