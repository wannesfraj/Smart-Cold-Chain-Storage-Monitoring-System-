"""Essais UI sur un simulateur Wokwi deja ouvert (Playwright, CDP local).

Usage de maintenance : python tools/validate_wokwi_browser.py --label platformio
Le navigateur doit ecouter sur 127.0.0.1:9223 et afficher le circuit en marche.
Ce script manipule les vrais curseurs et l'interrupteur du simulateur.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import re
import time

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
CAPTURES = ROOT / "docs/captures"


def latest(page):
    lines = re.findall(r"STATUS [^\r\n]+", page.locator("body").inner_text())
    if not lines:
        return None
    line = lines[-1]
    return {**dict(re.findall(r"(\w+)=([^ ]+)", line)), "line": line}


def wait_status(page, predicate, timeout=45):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        sample = latest(page)
        if sample and predicate(sample):
            return sample
        page.wait_for_timeout(350)
    raise AssertionError(f"Etat attendu non observe : {latest(page)}")


def slider(page, part, value):
    # Cliquer hors des composants ferme le panneau precedent.
    page.mouse.click(1785, 180)
    page.locator(f"[id={part}]").click(force=True)
    page.wait_for_timeout(150)
    if page.locator('input[type="range"]').count() == 0:
        page.locator(f"[id={part}]").click(force=True)
    control = page.locator('input[type="range"]').first
    control.wait_for()
    control.evaluate("""(el, value) => {
        Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(el, String(value));
        el.dispatchEvent(new Event('input', {bubbles: true}));
        el.dispatchEvent(new Event('change', {bubbles: true}));
    }""", math.log10(value) if part == "light" else value)
    page.mouse.click(1785, 180)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="wokwi-web")
    args = parser.parse_args()
    CAPTURES.mkdir(parents=True, exist_ok=True)
    results = {"date": "2026-11-08", "engine": "Wokwi ESP32 dans Chrome",
               "firmware": args.label, "scenarios": []}
    if "platformio" in args.label.lower():
        results["firmware_sha256"] = hashlib.sha256((ROOT / "firmware/SCCS_merged.bin").read_bytes()).hexdigest()
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        page = browser.contexts[0].pages[0]
        page.set_default_timeout(5000)
        page.set_viewport_size({"width": 1800, "height": 1300})

        def record(name, sample, capture=None):
            result = {"name": name, "result": "PASS", "observed": sample}
            if capture:
                # Laisser le rafraichissement LCD suivre la transition serie.
                initial_time = int(sample["t_ms"])
                wait_status(page, lambda s: int(s["t_ms"]) >= initial_time + 300)
                filename = capture + ".png"
                page.screenshot(path=str(CAPTURES / filename))
                # Capture LCD seule : image exacte de l'ecran simule.
                page.locator("#lcd").screenshot(path=str(CAPTURES / (capture + "_lcd.png")))
                result["capture"] = "captures/" + filename
            results["scenarios"].append(result)
            (ROOT / "docs/tests_wokwi.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print("PASS", name, sample["line"], flush=True)

        slider(page, "storage", 4)
        normal = wait_status(page, lambda s: s.get("state") == "NORMAL" and s.get("ambient") == "24.0")
        record("01 Fonctionnement normal", normal, "01_normal")

        slider(page, "storage", 9)
        hot = wait_status(page, lambda s: s.get("alarms") == "TEMP" and s.get("cooling") == "1")
        record("02 Temperature elevee", hot, "02_temperature")

        slider(page, "storage", 7.5)
        record("03a Retour sous le seuil d'alarme, froid maintenu",
               wait_status(page, lambda s: s.get("storage") == "7.50" and s.get("state") == "COOLING"))
        slider(page, "storage", 5)
        record("03b Hysteresis, maintien du froid a 5 C",
               wait_status(page, lambda s: s.get("storage") == "5.00" and s.get("cooling") == "1"))
        slider(page, "storage", 4)
        record("03c Arret du froid a 4 C",
               wait_status(page, lambda s: s.get("storage") == "4.00" and s.get("state") == "NORMAL"))
        slider(page, "storage", 5)
        record("03d Maintien arrete a 5 C",
               wait_status(page, lambda s: s.get("storage") == "5.00" and s.get("cooling") == "0"))
        slider(page, "storage", 6)
        record("03e Demarrage a 6 C",
               wait_status(page, lambda s: s.get("storage") == "6.00" and s.get("cooling") == "1"), "03_refroidissement")
        slider(page, "storage", 4)
        wait_status(page, lambda s: s.get("state") == "NORMAL")

        page.locator("#door").click(force=True)
        opened = wait_status(page, lambda s: s.get("door") == "OPEN" and s.get("state") == "DOOR_OPEN")
        record("04a Porte ouverte avant temporisation", opened)
        # Verifier que la temperature continue a etre lue pendant le compteur.
        slider(page, "storage", 9)
        record("06a Reactivite pendant ouverture",
               wait_status(page, lambda s: s.get("door") == "OPEN" and s.get("alarms") == "TEMP" and s.get("cooling") == "0"),
               "06_reactivite")
        slider(page, "storage", 4)
        wait_status(page, lambda s: s.get("storage") == "4.00" and s.get("alarms") == "NONE")
        # Le delai reste a sa vraie valeur de 30 secondes de temps simule.
        door = wait_status(page, lambda s: s.get("alarms") == "DOOR", timeout=240)
        assert int(door["door_s"]) >= 30
        record("04b Porte ouverte plus de 30 secondes", door, "04_porte")
        page.locator("#door").click(force=True)
        record("05 Retour a la normale apres fermeture",
               wait_status(page, lambda s: s.get("door") == "CLOSED" and s.get("state") == "NORMAL"), "05_retour")

        slider(page, "light", 1000)
        record("07 Innovation : lumiere oubliee",
               wait_status(page, lambda s: s.get("alarms") == "LIGHT", timeout=60), "07_lumiere")
        slider(page, "light", 10)
        record("08 Retour apres extinction de la lumiere",
               wait_status(page, lambda s: s.get("state") == "NORMAL"))

        serial = page.locator('[class*="serialControls"] input')
        serial.fill("SET DOOR 5")
        serial.press("Enter")
        page.wait_for_function("document.body.innerText.includes('OK SET')", timeout=10000)
        serial.fill("SET ON 3")
        serial.press("Enter")
        page.wait_for_function("document.body.innerText.includes('ERR seuils')", timeout=10000)
        serial.fill("RESET")
        serial.press("Enter")
        page.wait_for_function("document.body.innerText.includes('OK RESET')", timeout=10000)
        record("09 Configuration serie et restauration", latest(page))
        (ROOT / "docs/trace_wokwi.txt").write_text(page.locator("body").inner_text().split("ets Jul")[-1], encoding="utf-8")
        print("SUCCESS", len(results["scenarios"]), "observations Wokwi", flush=True)


if __name__ == "__main__":
    main()
