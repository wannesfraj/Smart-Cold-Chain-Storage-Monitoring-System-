#pragma once

#include "model.h"

namespace sccs {

void beginOutputs();
void updateOutputs(const Status& status, uint32_t now);

}  // namespace sccs
