#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>

#include "config.h"
#include "controller.h"
#include "debounce.h"

using namespace sccs;
namespace {
int assertions = 0;
int scenarios = 0;

void check(bool condition, const char* description) {
  ++assertions;
  if (!condition) {
    std::cerr << "FAIL: " << description << '\n';
    std::exit(1);
  }
}

void pass(const char* name) {
  ++scenarios;
  std::cout << "PASS " << name << '\n';
}

struct Fixture {
  Controller controller;
  Config config;
  Measurements data;

  explicit Fixture(uint32_t start = 0) {
    controller.begin(start);
    data.storageSampled = data.storageValid = data.ambientValid = true;
    data.storageC = 4.0f;
    data.ambientC = 24.0f;
    data.humidity = 45.0f;
    data.lux = 10.0f;
  }

  Status at(uint32_t now, float temperature = 4.0f) {
    data.storageC = temperature;
    data.storageUpdatedAt = now;
    return controller.update(data, config, now);
  }
};
}  // namespace

int main() {
  {
    Fixture f;
    const Status s = f.at(1000);
    check(s.state == State::NORMAL && !s.cooling && !s.alarms, "normal");
    pass("01 normal, porte fermee");
  }
  {
    Fixture f;
    check(!f.at(0, 8).alarms, "8 C exactement sans alarme");
    Status s = f.at(1000, 8.1f);
    check(s.state == State::ALARM && s.cooling && (s.alarms & TEMPERATURE), "temperature critique");
    pass("02 temperature critique strictement superieure a 8 C");
  }
  {
    Fixture f;
    check(!f.at(0, 5.9f).cooling, "avant seuil haut");
    check(f.at(100, 6).cooling, "demarrage a 6 C");
    check(f.at(200, 5).cooling, "maintien dans hysteresis");
    check(!f.at(300, 4).cooling, "arret a 4 C");
    check(!f.at(400, 5).cooling, "maintien arrete dans hysteresis");
    pass("03 hysteresis du thermostat 4 / 6 C");
  }
  {
    Fixture f;
    f.at(0, 9);
    check(f.at(100, 7.6f).alarms & TEMPERATURE, "maintien alarme a 7.6");
    check(!(f.at(200, 7.5f).alarms & TEMPERATURE), "effacement a 7.5");
    pass("04 hysteresis de l'alarme 7.5 / 8 C");
  }
  {
    Fixture f;
    f.data.doorOpen = true;
    check(f.at(100).state == State::DOOR_OPEN, "porte ouverte immediate");
    check(!(f.at(30100).alarms & DOOR_TIMEOUT), "pas d'alarme a exactement 30 s");
    check(f.at(30101).alarms & DOOR_TIMEOUT, "alarme apres 30 s");
    pass("05 porte ouverte, frontiere 30 secondes");
  }
  {
    Fixture f;
    f.data.doorOpen = true;
    f.at(0, 9);
    check(f.at(30001, 9).alarms == (TEMPERATURE | DOOR_TIMEOUT), "deux causes simultanees");
    f.data.doorOpen = false;
    check(f.at(30100, 9).alarms == TEMPERATURE, "fermeture ne masque pas temperature");
    check(f.at(30200, 4).state == State::NORMAL, "retour normal");
    pass("06 cumul et effacement independant des alarmes");
  }
  {
    Fixture f;
    f.data.doorOpen = true;
    f.at(0);
    f.data.doorOpen = false;
    f.at(29000);
    f.data.doorOpen = true;
    check(!f.at(30000).alarms && f.at(30000).doorOpenMs == 0, "nouvelle ouverture");
    check(!f.at(59000).alarms, "temporisation remise a zero");
    pass("07 reinitialisation du compteur de porte");
  }
  {
    Fixture f;
    check(f.at(0, 7).cooling, "demande de froid");
    f.data.doorOpen = true;
    check(!f.at(10, 5).cooling, "suspension porte ouverte");
    f.data.doorOpen = false;
    check(f.at(20, 5).cooling, "reprise de la demande conservee");
    pass("08 suspension et reprise du refroidissement par la porte");
  }
  {
    Fixture f;
    f.data.lux = 300;
    check(!f.at(0).alarms, "lumiere commence");
    check(!f.at(4999).alarms, "lumiere avant 5 s");
    check(f.at(5000).alarms & LIGHT_ON, "lumiere 5 s");
    f.data.lux = 10;
    check(!f.at(5001).alarms, "lumiere eteinte");
    pass("09 lumiere forte porte fermee pendant 5 secondes");
  }
  {
    Fixture f;
    f.data.lux = 1000;
    f.data.doorOpen = true;
    f.at(0);
    check(!(f.at(10000).alarms & LIGHT_ON), "lumiere normale porte ouverte");
    f.data.doorOpen = false;
    check(!(f.at(10001).alarms & LIGHT_ON), "nouveau compteur a fermeture");
    check(f.at(15001).alarms & LIGHT_ON, "alarme apres fermeture et 5 s");
    pass("10 lumiere ignoree porte ouverte, compteur a fermeture");
  }
  {
    Fixture f;
    f.data.storageSampled = f.data.storageValid = false;
    check(f.controller.update(f.data, f.config, 1499).state == State::INIT, "grace demarrage");
    check(f.controller.update(f.data, f.config, 1500).alarms & STORAGE_FAULT, "absence au demarrage");
    check(f.at(1600).alarms & STORAGE_FAULT, "absence persistante");
    f.data.storageSampled = f.data.storageValid = true;
    check(f.at(1700).state == State::NORMAL, "recuperation sonde");
    pass("11 demarrage, sonde absente et recuperation");
  }
  {
    Fixture f;
    f.at(0, 9);
    f.data.storageValid = false;
    const Status s = f.at(100, -127);
    check(s.alarms == STORAGE_FAULT && !s.cooling, "sonde debranchee");
    f.data.storageValid = true;
    check(f.at(200, std::numeric_limits<float>::quiet_NaN()).alarms & STORAGE_FAULT, "NaN");
    check(f.at(300, 126).alarms & STORAGE_FAULT, "mesure hors plage");
    pass("12 sonde invalide : alarme et sortie de froid arretee");
  }
  {
    Fixture f;
    f.at(0, 7);
    check(f.controller.update(f.data, f.config, 2500).storageUsable, "mesure agee de 2500 ms");
    const Status s = f.controller.update(f.data, f.config, 2501);
    check((s.alarms & STORAGE_FAULT) && !s.cooling, "mesure perimee");
    pass("13 surveillance de la fraicheur de la mesure");
  }
  {
    Fixture f;
    f.data.ambientValid = false;
    check(f.at(0).state == State::NORMAL, "DHT secondaire indisponible");
    pass("14 le DHT ne remplace pas la sonde principale");
  }
  {
    const uint32_t start = UINT32_MAX - 10000;
    Fixture f(start);
    f.data.doorOpen = true;
    f.at(start);
    check(!(f.at(start + uint32_t{30000}).alarms & DOOR_TIMEOUT), "rollover 30 s");
    check(f.at(start + uint32_t{30001}).alarms & DOOR_TIMEOUT, "rollover plus de 30 s");
    pass("15 debordement de millis pendant une ouverture");
  }
  {
    DebouncedInput d;
    d.begin(false, 0);
    check(!d.update(true, 10), "front en attente");
    check(!d.update(false, 20), "rebond");
    check(!d.update(true, 25), "nouveau front");
    check(!d.update(true, 64), "39 ms");
    check(d.update(true, 65), "40 ms stabilise");
    check(d.update(false, 70), "fermeture en attente");
    check(!d.update(false, 110), "fermeture stabilisee");
    pass("16 anti-rebond dans les deux sens");
  }
  {
    DebouncedInput d;
    d.begin(false, UINT32_MAX - 30);
    check(!d.update(true, UINT32_MAX - 20), "front avant rollover");
    check(d.update(true, 20), "anti-rebond apres rollover");
    pass("17 anti-rebond au debordement de millis");
  }
  {
    Config c;
    check(validConfig(c), "configuration initiale");
    c.coolingOffC = c.coolingOnC;
    check(!validConfig(c), "hysteresis vide refusee");
    c = Config{}; c.criticalC = c.coolingOnC;
    check(!validConfig(c), "seuil critique incoherent refuse");
    c = Config{}; c.criticalClearC = c.criticalC;
    check(!validConfig(c), "seuil effacement incoherent refuse");
    c = Config{}; c.doorTimeoutMs = 0;
    check(!validConfig(c), "delai nul refuse");
    c = Config{}; c.lightAlarmLux = std::numeric_limits<float>::infinity();
    check(!validConfig(c), "infini refuse");
    pass("18 validation des parametres");
  }
  {
    Fixture f;
    f.config.doorTimeoutMs = 1000;
    f.data.doorOpen = true;
    f.at(0);
    check(!f.at(1000).alarms && (f.at(1001).alarms & DOOR_TIMEOUT), "seuil modifie");
    pass("19 configuration de la temporisation");
  }
  {
    Fixture f;
    f.data.doorOpen = true;
    f.at(0);
    check(f.at(10000, 9).alarms & TEMPERATURE, "temperature lue pendant temporisation porte");
    check(!(f.at(10000, 9).alarms & DOOR_TIMEOUT), "delai porte encore en cours");
    check(!f.at(11000, 4).alarms, "retour temperature avant fin temporisation");
    pass("20 reactivite pendant la temporisation de porte");
  }
  std::cout << "SUCCESS " << scenarios << " scenarios, " << assertions << " assertions\n";
}
