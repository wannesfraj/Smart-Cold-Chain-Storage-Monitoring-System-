"""Retrouve PlatformIO, compile l'ESP32 et conserve la trace de compilation."""
from pathlib import Path
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def find_pio():
    name = shutil.which("pio") or shutil.which("platformio")
    if name:
        return name
    core = Path(os.environ.get("PLATFORMIO_CORE_DIR", Path.home() / ".platformio"))
    for relative in ["penv/Scripts/platformio.exe", "penv/Scripts/pio.exe", "penv/bin/platformio"]:
        candidate = core / relative
        if candidate.is_file():
            return str(candidate)
    raise SystemExit("PlatformIO introuvable. Installer l'extension PlatformIO IDE dans VS Code.")


def main():
    command = [find_pio(), "run"]
    process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    lines = []
    for line in process.stdout:
        print(line, end="")
        lines.append(line)
    code = process.wait()
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs/compilation.txt").write_text("".join(lines), encoding="utf-8")
    if code:
        raise SystemExit(code)
    # Image complete pour le chargement manuel sur le site Wokwi.
    build = ROOT / ".pio/build/esp32dev"
    pio_python = Path(command[0]).with_name("python.exe" if os.name == "nt" else "python")
    if not pio_python.exists():
        pio_python = Path(sys.executable)
    core = Path(os.environ.get("PLATFORMIO_CORE_DIR", Path.home() / ".platformio"))
    esptool = core / "packages/tool-esptoolpy/esptool.py"
    firmware = ROOT / "firmware"
    firmware.mkdir(exist_ok=True)
    for filename in ["firmware.bin", "firmware.elf", "bootloader.bin", "partitions.bin"]:
        shutil.copy2(build / filename, firmware / filename)
    subprocess.run([str(pio_python), str(esptool), "--chip", "esp32", "merge_bin", "-o",
                    str(firmware / "SCCS_merged.bin"), "--flash_mode", "dio", "--flash_size", "4MB",
                    "0x1000", str(build / "bootloader.bin"), "0x8000", str(build / "partitions.bin"),
                    "0x10000", str(build / "firmware.bin")], check=True, cwd=ROOT)
    print("Firmware complet : firmware/SCCS_merged.bin")


if __name__ == "__main__":
    main()
