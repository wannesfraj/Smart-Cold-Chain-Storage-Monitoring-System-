"""Exporte les sources modulaires dans le dossier plat attendu par Wokwi Web."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def export():
    target = ROOT / "wokwi-web"
    target.mkdir(exist_ok=True)
    for folder, pattern in [("src", "*.cpp"), ("include", "*.h")]:
        for source in sorted((ROOT / folder).glob(pattern)):
            shutil.copy2(source, target / source.name)
    shutil.copy2(ROOT / "diagram.json", target / "diagram.json")
    (target / "sketch.ino").write_text(
        "// SCCS - ESP32 / Arduino\n"
        "// Programme modulaire : main.cpp et modules .cpp / .h.\n"
        "// Sources de reference : dossier local src/ et include/.\n", encoding="utf-8")
    (target / "libraries.txt").write_text(
        "OneWire@2.3.8\nDallasTemperature@4.0.6\n"
        "DHT sensor library for ESPx@1.19.0\nLiquidCrystal I2C@1.1.2\n", encoding="utf-8")
    print("Export Wokwi Web genere dans wokwi-web/")
    return target


if __name__ == "__main__":
    export()
