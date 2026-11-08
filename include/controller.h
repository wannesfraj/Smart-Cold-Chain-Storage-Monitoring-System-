#pragma once

#include "config.h"
#include "model.h"

namespace sccs {

class Controller {
 public:
  void begin(uint32_t now);
  Status update(const Measurements& data, const Config& config, uint32_t now);

 private:
  uint32_t startedAt_ = 0;
  uint32_t doorOpenedAt_ = 0;
  uint32_t lightStartedAt_ = 0;
  bool doorWasOpen_ = false;
  bool lightPending_ = false;
  bool critical_ = false;
  bool coolingDemand_ = false;
};

}  // namespace sccs
