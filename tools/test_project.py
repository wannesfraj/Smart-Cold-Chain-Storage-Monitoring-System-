"""Compile et teste le vrai controleur C++ sur PC, puis verifie le cablage."""
from pathlib import Path
import json
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    compiler = shutil.which("g++") or shutil.which("clang++")
    if not compiler:
        raise SystemExit("Installer g++ (MinGW sous Windows) ou clang++ pour les tests PC.")
    out = ROOT / ".tools" / "tests"
    out.mkdir(parents=True, exist_ok=True)
    executable = out / ("controller_test.exe" if sys.platform == "win32" else "controller_test")
    command = [compiler, "-std=c++11", "-Wall", "-Wextra", "-Werror", "-pedantic",
               "-I", str(ROOT / "include"), str(ROOT / "src/config.cpp"),
               str(ROOT / "src/controller.cpp"), str(ROOT / "tests/controller_test.cpp"),
               "-o", str(executable)]
    subprocess.run(command, check=True, cwd=ROOT)
    result = subprocess.run([str(executable)], capture_output=True, text=True, check=True)
    print(result.stdout, end="")

    diagram = json.loads((ROOT / "diagram.json").read_text(encoding="utf-8"))
    parts = {p["id"]: p for p in diagram["parts"]}
    assert len(parts) == len(diagram["parts"]), "Identifiants Wokwi dupliques"
    connections = {frozenset(c[:2]) for c in diagram["connections"]}
    config = (ROOT / "include/config.h").read_text(encoding="utf-8")
    expected = {"STORAGE": "storage:DQ", "AMBIENT": "ambient:SDA",
                "DOOR": "door:2", "LIGHT": "light:AO", "LCD_SDA": "lcd:SDA",
                "LCD_SCL": "lcd:SCL", "LED_NORMAL": "rNormal:1",
                "COOLING": "rCooling:1", "LED_ALARM": "rAlarm:1", "BUZZER": "buzzer:2"}
    for constant, pin in expected.items():
        number = re.search(rf"constexpr uint8_t {constant} = (\d+);", config).group(1)
        assert frozenset([f"esp:{number}", pin]) in connections, f"GPIO incoherent : {constant}"
    required = [("storage:VCC", "esp:3V3"), ("storage:GND", "esp:GND.1"),
                ("pullup:1", "esp:3V3"), ("pullup:2", "storage:DQ"),
                ("ambient:VCC", "esp:3V3"), ("ambient:GND", "esp:GND.1"),
                ("dhtPullup:1", "esp:3V3"), ("dhtPullup:2", "ambient:SDA"),
                ("light:VCC", "esp:3V3"), ("light:GND", "esp:GND.1"),
                ("lcd:VCC", "esp:5V"), ("lcd:GND", "esp:GND.1"),
                ("door:1", "esp:GND.1"), ("buzzer:1", "esp:GND.2")]
    for a, b in required:
        assert frozenset([a, b]) in connections, f"Connexion manquante : {a} -> {b}"
    for resistor, led in [("rNormal", "normal"), ("rCooling", "cooling"), ("rAlarm", "alarm")]:
        assert parts[resistor]["attrs"]["value"] == "330"
        assert frozenset([f"{resistor}:2", f"{led}:A"]) in connections
        assert frozenset([f"{led}:C", "esp:GND.2"]) in connections
    for connection in diagram["connections"]:
        for endpoint in connection[:2]:
            assert endpoint.split(":")[0] in parts or endpoint.startswith("$serialMonitor:")
    for source in (ROOT / "src").glob("*.cpp"):
        assert not re.search(r"\bdelay\s*\(", source.read_text(encoding="utf-8")), f"delay() dans {source}"
    print("PASS cablage : 10 GPIO, alimentations, pull-up et 3 LED avec resistance")
    print("PASS aucune temporisation delay() dans les sources applicatives")
    log = result.stdout + "PASS cablage et absence de delay()\n"
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs/tests_locaux.txt").write_text(log, encoding="utf-8")


if __name__ == "__main__":
    main()
