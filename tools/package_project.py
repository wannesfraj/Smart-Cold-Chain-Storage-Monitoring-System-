"""Prepare une archive source et livrables, sans caches ni cles personnelles."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
import json

from export_wokwi import export

ROOT = Path(__file__).resolve().parents[1]


def main():
    export()
    for required in ["docs/Rapport_SCCS.pdf", "docs/tests_locaux.txt", "docs/compilation.txt",
                     "docs/tests_wokwi.json", "firmware/SCCS_merged.bin"]:
        if not (ROOT / required).is_file():
            raise SystemExit(f"Livrable manquant : {required}")
    results = json.loads((ROOT / "docs/tests_wokwi.json").read_text(encoding="utf-8"))
    if len(results.get("scenarios", [])) < 14 or any(s.get("result") != "PASS" for s in results["scenarios"]):
        raise SystemExit("La suite de simulation Wokwi n'est pas entierement validee.")
    excluded = {".pio", ".tools", ".git", "dist", "__pycache__"}
    files = [p for p in ROOT.rglob("*") if p.is_file() and not excluded.intersection(p.relative_to(ROOT).parts)
             and p.name != "manifest.sha256.json" and p.suffix != ".pyc"]
    manifest = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(files)}
    (ROOT / "docs/manifest.sha256.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    files.append(ROOT / "docs/manifest.sha256.json")
    target = ROOT / "dist"
    target.mkdir(exist_ok=True)
    archive = target / "SCCS_projet_complet.zip"
    with ZipFile(archive, "w", compression=ZIP_DEFLATED) as bundle:
        for path in sorted(files):
            bundle.write(path, "SCCS/" + path.relative_to(ROOT).as_posix())
    print(f"Archive creee : {archive} ({archive.stat().st_size / 1024 / 1024:.2f} Mo)")


if __name__ == "__main__":
    main()
