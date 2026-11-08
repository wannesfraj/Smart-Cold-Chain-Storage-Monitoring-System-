#pragma once

#include "config.h"
#include "model.h"

namespace sccs {

void beginDisplay();
void updateDisplay(const Measurements& data, const Status& status,
                   const Config& config, uint32_t now);

}  // namespace sccs
