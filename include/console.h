#pragma once

#include "config.h"
#include "model.h"

namespace sccs {

void beginConsole();
void updateConsole(Config& config);
void printStatus(const Measurements& data, const Status& status, uint32_t now);

}  // namespace sccs
