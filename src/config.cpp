#include "config.h"

#include <math.h>

namespace sccs {

bool validConfig(const Config& c) {
  return isfinite(c.coolingOnC) && isfinite(c.coolingOffC) &&
         isfinite(c.criticalC) && isfinite(c.criticalClearC) &&
         isfinite(c.lightAlarmLux) && c.coolingOffC >= -55.0f &&
         c.coolingOffC < c.coolingOnC && c.coolingOnC < c.criticalC &&
         c.criticalC <= 125.0f && c.criticalClearC >= c.coolingOffC &&
         c.criticalClearC < c.criticalC && c.doorTimeoutMs >= 1000 &&
         c.doorTimeoutMs <= 300000 && c.lightAlarmLux >= 1.0f &&
         c.lightAlarmLux <= 100000.0f;
}

}  // namespace sccs
