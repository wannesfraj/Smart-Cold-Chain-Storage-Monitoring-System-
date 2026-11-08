"""Genere le rapport PDF illustre de 8 pages a partir des preuves du projet.

Dependance de generation uniquement : python -m pip install reportlab
Personnalisation : python tools/create_report.py --author "Nom Prenom"
"""
from pathlib import Path
import argparse
from html import escape
import json
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    Image, Preformatted, KeepTogether,
)
from reportlab.graphics.shapes import Drawing, Rect, Line, String, Polygon

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
INK = colors.HexColor("#14364A")
ACCENT = colors.HexColor("#087F8C")
PALE = colors.HexColor("#EDF6F7")
GREY = colors.HexColor("#566675")


def fonts():
    windows = Path("C:/Windows/Fonts")
    for family, regular, bold in [("Body", "segoeui.ttf", "segoeuib.ttf"),
                                  ("Code", "consola.ttf", "consolab.ttf")]:
        pdfmetrics.registerFont(TTFont(family, str(windows / regular)))
        pdfmetrics.registerFont(TTFont(family + "Bold", str(windows / bold)))
        pdfmetrics.registerFontFamily(family, normal=family, bold=family + "Bold",
                                      italic=family, boldItalic=family + "Bold")


def main():
    args = argparse.ArgumentParser()
    args.add_argument("--author", default="Wannes Fraj")
    args.add_argument("--group", default="2ème GII 3")
    options = args.parse_args()
    author = options.author
    fonts()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("TitleS", fontName="BodyBold", fontSize=30, leading=37,
                              textColor=INK, spaceAfter=15))
    styles.add(ParagraphStyle("HeadingS", fontName="BodyBold", fontSize=19, leading=25,
                              textColor=INK, spaceAfter=14))
    styles.add(ParagraphStyle("SubS", fontName="BodyBold", fontSize=11, leading=15,
                              textColor=ACCENT, spaceBefore=12, spaceAfter=6))
    styles.add(ParagraphStyle("TextS", fontName="Body", fontSize=10, leading=14.3,
                              textColor=INK, spaceAfter=9))
    styles.add(ParagraphStyle("SmallS", parent=styles["TextS"], fontSize=8.1, leading=11,
                              spaceAfter=5))
    styles.add(ParagraphStyle("CellS", parent=styles["SmallS"], fontSize=8, leading=10.5,
                              spaceAfter=0))
    styles.add(ParagraphStyle("CaptionS", parent=styles["SmallS"], textColor=GREY,
                              alignment=TA_CENTER, spaceAfter=10))
    styles.add(ParagraphStyle("CodeS", fontName="Code", fontSize=8, leading=11,
                              textColor=INK, backColor=PALE, borderPadding=10, spaceAfter=10))
    flow = []

    def p(text, style="TextS"):
        return Paragraph(text, styles[style])

    def add(text, style="TextS"):
        flow.append(p(text, style))

    def title(number, text):
        add(f"{number:02d} / {text}", "HeadingS")

    def sub(text):
        add(text, "SubS")

    def table(rows, widths):
        cells = [[p(escape(str(v)), "CellS") for v in row] for row in rows]
        t = Table(cells, colWidths=widths, repeatRows=1, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PALE),
            ("LINEBELOW", (0, 0), (-1, 0), 1, ACCENT),
            ("LINEBELOW", (0, 1), (-1, -1), .35, colors.HexColor("#D7E2E7")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        flow.append(t)
        flow.append(Spacer(1, 9))

    def image(path, width, max_height=330):
        im = Image(str(path))
        ratio = min(width / im.imageWidth, max_height / im.imageHeight)
        im.drawWidth = im.imageWidth * ratio
        im.drawHeight = im.imageHeight * ratio
        im.hAlign = "CENTER"
        return im

    def picture(name, caption, width=480, height=330):
        path = DOCS / "captures" / name
        if path.exists():
            flow.append(image(path, width, height))
            add(caption, "CaptionS")

    def new():
        flow.append(PageBreak())

    results = json.loads((DOCS / "tests_wokwi.json").read_text(encoding="utf-8"))
    observations = results["scenarios"]
    compilation = (DOCS / "compilation.txt").read_text(encoding="utf-8")
    ram = re.search(r"RAM:.*?\(used (\d+) bytes from (\d+) bytes\)", compilation)
    flash = re.search(r"Flash:.*?\(used (\d+) bytes from (\d+) bytes\)", compilation)
    local = (DOCS / "tests_locaux.txt").read_text(encoding="utf-8")
    summary = re.search(r"SUCCESS (\d+) scenarios, (\d+) assertions", local)
    link_path = DOCS / "lien_wokwi.txt"
    link = link_path.read_text(encoding="utf-8").strip() if link_path.exists() else ""
    github_path = DOCS / "lien_github.txt"
    github = github_path.read_text(encoding="utf-8").strip() if github_path.exists() else ""

    # Page 1 : contexte et contrat fonctionnel.
    add("ENET’COM · Département Informatique Industrielle", "SmallS")
    flow.append(Spacer(1, 35))
    add("S.C.C.S.", "TitleS")
    add("Smart Cold Chain &amp;<br/>Storage Monitoring System", "HeadingS")
    add("Surveillance intelligente d’une chambre froide et de stockage")
    add("Mini-projet Systèmes programmables · 2GII · 2026–2027", "SubS")
    add(f"Auteur : <b>{escape(author)}</b><br/>Groupe : {escape(options.group)}<br/>Version technique : 8 novembre 2026")
    sub("Problème et objectif")
    add("Une température inadaptée ou une porte laissée ouverte peut détériorer des produits sensibles. "
        "Le système proposé mesure les conditions de stockage, commande un refroidissement simulé "
        "et rend les anomalies immédiatement visibles sur un écran, des voyants et un buzzer.")
    sub("Cahier des charges retenu")
    table([
        ["Besoin", "Solution réalisée"],
        ["Développement et simulation", "ESP32 / Arduino, VS Code, PlatformIO, circuit Wokwi"],
        ["Entrées pertinentes", "DS18B20, DHT22, interrupteur de porte, LDR"],
        ["Sorties et affichage", "LCD 16 × 2 I2C, LED verte / bleue / rouge, buzzer"],
        ["Commande et alertes", "Thermostat avec hystérésis ; température critique ; porte > 30 s"],
        ["Réactivité et organisation", "Modules séparés ; conversion asynchrone ; temporisations millis()"],
        ["Innovations opérationnelles", "Lumière oubliée, défaut sonde, réglages série validés"],
    ], [149, 331])
    add("Les seuils sont des paramètres d’un scénario pédagogique. Cette simulation ne définit pas "
        "des limites universelles de conservation et ne constitue pas une installation de sécurité réelle.", "SmallS")

    # Page 2 : composants et circuit réel simule.
    new()
    title(2, "Matériel virtuel et câblage")
    table([
        ["Composant / signal", "GPIO", "Câblage et utilité"],
        ["DS18B20 / DQ", "4", "Stockage ; VCC 3,3 V ; pull-up 4,7 kΩ"],
        ["DHT22 / SDA", "16", "Ambiance et humidité ; 3,3 V ; pull-up 10 kΩ"],
        ["Porte / borne centrale 2", "27", "Borne 1 à GND, 3 libre ; INPUT_PULLUP"],
        ["LDR / AO", "34", "ADC1, 12 bits ; alimentation 3,3 V ; DO libre"],
        ["LCD / SDA, SCL", "21, 22", "I2C, adresse 0x27 ; LCD virtuel alimenté en 5 V"],
        ["LED verte / bleue / rouge", "25 / 26 / 33", "Une résistance série de 330 Ω par LED"],
        ["Buzzer / borne 2 (+)", "32", "Borne 1 à GND ; PWM 2 kHz"],
    ], [145, 66, 269])
    add("Toutes les masses sont reliées. À gauche, l’interrupteur connecte GPIO27 à GND : porte fermée. "
        "À droite, le pull-up place l’entrée à l’état haut : porte ouverte. Un anti-rebond logiciel de 40 ms est appliqué.", "SmallS")
    picture("01_normal.png", "Figure 1 — Circuit et fonctionnement normal réellement exécutés dans Wokwi.", height=310)
    add("La LDR représente l’éclairage intérieur. Le DHT22 mesure une information d’ambiance indépendante ; "
        "la décision de refroidissement utilise exclusivement le DS18B20. Le câblage I2C 5 V du LCD est celui "
        "du simulateur ; les niveaux électriques seraient à vérifier sur du matériel réel.", "SmallS")

    # Page 3 : architecture.
    new()
    title(3, "Architecture et machine à états")
    add("La boucle principale coordonne l’acquisition, la décision, les sorties, l’affichage et la console. "
        "Le contrôleur ne dépend pas d’Arduino : les mêmes règles C++ sont compilées pour l’ESP32 et testées sur PC.")
    table([
        ["Module", "Responsabilité"],
        ["main.cpp", "Initialisation et orchestration ; traces sur transition ou toutes les secondes"],
        ["sensors.cpp / debounce.h", "Acquisitions, conversion DS18B20 et stabilisation de la porte"],
        ["controller.cpp", "Thermostat, compteurs, masque des alarmes et état prioritaire"],
        ["alarm.cpp", "LED et buzzer ; adaptation aux API Arduino-ESP32 2.x / 3.x"],
        ["display.cpp", "Deux lignes LCD, rafraîchissement périodique, rotation des causes"],
        ["console.cpp", "Interprétation bornée des commandes et suivi des mesures"],
        ["config.cpp / config.h", "Broches, paramètres par défaut et validation atomique des changements"],
        ["model.h", "Structures Measurements, Status et types partagés"],
    ], [147, 333])
    sub("États explicites et priorité")
    drawing = Drawing(480, 112)
    states = [(0, "ALARM", "Cause active"), (98, "INIT", "Première mesure"),
              (196, "DOOR_OPEN", "Porte ouverte"), (294, "COOLING", "Froid actif"),
              (392, "NORMAL", "Repos surveillé")]
    for x, name, note in states:
        drawing.add(Rect(x, 37, 88, 51, strokeColor=ACCENT, fillColor=PALE, strokeWidth=1))
        drawing.add(String(x + 44, 66, name, fontName="BodyBold", fontSize=8.2,
                           textAnchor="middle", fillColor=INK))
        drawing.add(String(x + 44, 49, note, fontName="Body", fontSize=7.3,
                           textAnchor="middle", fillColor=GREY))
        if x < 392:
            drawing.add(Line(x + 89, 61, x + 96, 61, strokeColor=ACCENT))
    drawing.add(String(240, 13, "Évaluation de gauche à droite à chaque tour de boucle",
                       fontName="Body", fontSize=9, textAnchor="middle", fillColor=INK))
    flow.append(drawing)
    add("INIT attend la première mesure, pendant au plus 1,5 s. Une sonde absente ou invalide conduit à ALARM. "
        "Hors alarme, une porte ouverte prend la priorité sur COOLING. À la fermeture, le système retrouve "
        "COOLING ou NORMAL selon la demande mémorisée du thermostat.")
    add("Le refroidissement et les causes sont suivis séparément de l’état affiché. Une alarme de température "
        "peut donc coexister avec la LED bleue active. Les causes TEMP, DOOR, LIGHT et SENSOR sont cumulables.")

    # Page 4 : règles et temps.
    new()
    title(4, "Commande, alertes et réactivité")
    table([
        ["Règle", "Déclenchement", "Effacement / arrêt"],
        ["Refroidissement", "T ≥ 6 °C, porte fermée", "T ≤ 4 °C"],
        ["Température critique", "T > 8 °C", "T ≤ 7,5 °C"],
        ["Porte prolongée", "Ouverture continue > 30 s", "Fermeture stabilisée"],
        ["Lumière oubliée", "≥ 300 lx, 5 s, porte fermée", "< 300 lx ou ouverture"],
        ["Sonde principale", "Invalide, hors plage, ou âge > 2,5 s", "Nouvelle mesure valide"],
    ], [119, 178, 183])
    add("Les deux hystérésis évitent les commutations autour d’un seuil unique. Entre 4 et 6 °C, le thermostat "
        "conserve sa demande précédente. Entre 7,5 et 8 °C, l’alarme de température conserve son état précédent.")
    add("L’ouverture suspend la sortie bleue sans perdre la demande de froid. Une mesure DS18B20 défaillante "
        "arrête le froid et déclenche SENSOR. Les alertes s’effacent automatiquement et séparément : fermer "
        "la porte ne supprime pas une température encore critique.")
    sub("Planification sans attente longue")
    table([
        ["Tâche", "Période / délai", "Méthode"],
        ["DS18B20 12 bits", "Départ chaque 1 s ; lecture après 750 ms", "setWaitForConversion(false)"],
        ["DHT22", "2,2 s", "Lecture périodique, validité contrôlée"],
        ["LDR / LCD / série", "100 / 250 / 1000 ms", "Échéances millis() indépendantes"],
        ["Porte", "40 ms de stabilité ; alerte > 30 s", "Anti-rebond puis compteur continu"],
        ["Alarme sonore / LED", "250 ms par seconde / clignotement 500 ms", "PWM et phase calculée"],
    ], [110, 209, 161])
    flow.append(Preformatted("updateConsole(config);\nsensors.update(millis());\nstatus = controller.update(data, config, millis());\nupdateOutputs(status, now);\nupdateDisplay(data, status, config, now);", styles["CodeS"]))
    add("Aucun delay() n’apparaît dans les sources applicatives. Les courtes transactions de communication "
        "restent synchrones. Les différences de dates utilisent des entiers non signés pour supporter le "
        "débordement de millis(), vérifié par les tests du contrôleur.", "SmallS")

    # Page 5 : outils et paramètres.
    new()
    title(5, "Compilation, simulation et réglages")
    ini = (ROOT / "platformio.ini").read_text(encoding="utf-8")
    flow.append(Preformatted(ini, styles["CodeS"]))
    add("La plateforme épinglée fournit Arduino-ESP32 2.0.17. esp32dev désigne le module ESP32 générique. "
        "lib_deps installe les bibliothèques effectivement utilisées ; les versions sont fixées pour rendre "
        "la compilation reproductible. Le moniteur fonctionne à 115200 bauds.")
    if ram and flash:
        add(f"<b>Compilation PlatformIO : SUCCESS.</b> RAM : {int(ram[1]):,} / {int(ram[2]):,} octets ; "
            f"Flash applicative : {int(flash[1]):,} / {int(flash[2]):,} octets. "
            "Deux avertissements de préprocesseur proviennent de OneWire 2.3.8 ; aucun n’empêche la compilation.")
    sub("Lien entre le projet local et Wokwi")
    add("wokwi.toml référence .pio/build/esp32dev/firmware.bin et firmware.elf. Dans VS Code : compiler "
        "avec PlatformIO, puis F1 → Wokwi: Start Simulator. Le fichier diagram.json décrit le circuit. "
        "Le binaire complet firmware/SCCS_merged.bin est aussi chargeable sur le site Wokwi par le menu F1.")
    sub("Innovation : configuration série contrôlée")
    flow.append(Preformatted("HELP          CONFIG        RESET\nSET ON 6      SET OFF 4      SET HIGH 8\nSET CLEAR 7.5 SET DOOR 30    SET LUX 300", styles["CodeS"]))
    add("Les valeurs restent en RAM. Le contrôleur impose OFF &lt; ON &lt; HIGH, OFF ≤ CLEAR &lt; HIGH, "
        "un délai de porte entier de 1 à 300 s et une luminosité de 1 à 100000 lx. Les valeurs non finies, "
        "les commandes trop longues et les configurations incohérentes sont refusées. RESET rétablit les défauts.", "SmallS")

    # Page 6 : preuves et résultats.
    new()
    title(6, "Tests exécutés et résultats observés")
    add(f"Les tests PC ont validé <b>{summary[1]} scénarios et {summary[2]} assertions</b> du vrai contrôleur, "
        "plus la correspondance du câblage. La simulation Wokwi ci-dessous utilise : "
        f"<b>{escape(results['firmware'])}</b>. Les observations exactes figurent dans tests_wokwi.json et trace_wokwi.txt.")
    table([
        ["Scénario demandé", "Manipulation", "Observation réelle / verdict"],
        ["1. Normal", "4 °C, porte fermée, lumière 10 lx", "NORMAL, cooling=0, alarms=NONE : PASS"],
        ["2. Température élevée", "DS18B20 à 9 °C", "ALARM, TEMP, refroidissement actif : PASS"],
        ["3. Refroidissement", "7,5 → 5 → 4 → 5 → 6 °C", "Maintien à 5, arrêt à 4, repos à 5, départ à 6 : PASS"],
        ["4. Porte ouverte", "Interrupteur à droite ; attendre > 30 s simulées", "DOOR_OPEN puis ALARM / DOOR, sortie arrêtée : PASS"],
        ["5. Retour normal", "Refermer la porte et remettre 4 °C", "NORMAL et arrêt de l’alarme : PASS"],
        ["6. Réactivité", "Passer à 9 °C pendant le compteur de porte", "TEMP détectée avant expiration ; froid suspendu : PASS"],
        ["7. Lumière oubliée", "LDR forte, porte fermée pendant 5 s", "ALARM / LIGHT ; retour après extinction : PASS"],
        ["8. Réglages série", "SET DOOR 5 puis RESET", "OK SET et OK RESET reçus : PASS"],
    ], [100, 173, 207])
    sub("Couverture complémentaire sur PC")
    add("Les cas aux frontières distinguent exactement 8 °C de 8,1 °C et exactement 30 s de 30 s + 1 ms. "
        "Les tests vérifient les alarmes cumulées, la remise à zéro du compteur après fermeture, le défaut "
        "DS18B20, les mesures NaN ou périmées, l’anti-rebond, les réglages invalides et le débordement de millis().")
    add("Les tests du contrôleur ne valident pas, à eux seuls, le protocole électrique des composants. "
        "Les scénarios Wokwi complètent cette vérification en exécutant le firmware avec les périphériques simulés.")
    picture("02_temperature_lcd.png", "Figure 2 — Écran simulé : 9 °C, ALARME et cause TEMP CRITIQUE.", width=300, height=140)

    # Page 7 : captures, sans preuves fabriquees.
    new()
    title(7, "Captures de la démonstration")
    picture("04_porte.png", "Figure 3 — Alarme de porte après plus de 30 secondes simulées, à température normale.", height=330)
    rows = []
    for a, b in [("01_normal_lcd.png", "03_refroidissement_lcd.png"),
                 ("04_porte_lcd.png", "07_lumiere_lcd.png")]:
        rows.append([image(DOCS / "captures" / a, 215, 100),
                     image(DOCS / "captures" / b, 215, 100)])
    t = Table(rows, colWidths=[240, 240])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("TOPPADDING", (0, 0), (-1, -1), 8),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    flow.append(t)
    add("Figures 4 à 7 — NORMAL ; FROID ; alarme PORTE ; alarme LUMIÈRE. "
        "Images issues de l’écran LCD du simulateur, sans reconstruction graphique.", "CaptionS")
    add("La température et l’état restent toujours visibles sur la première ligne. La deuxième ligne indique "
        "la porte, les valeurs d’ambiance, la lumière ou la cause. Plusieurs causes alternent toutes les 2 s. "
        "La trace série conserve les mesures, la durée d’ouverture et les sorties pour expliquer chaque transition.", "SmallS")

    # Page 8 : limites, reproduction et sources.
    new()
    title(8, "Limites, reproduction et remise")
    sub("Limites connues")
    add("Le modèle ne simule pas la dynamique thermique : la LED bleue ne fait pas baisser automatiquement "
        "le DS18B20. Le démonstrateur doit donc faire évoluer le curseur pour représenter un refroidissement. "
        "La LED ne commande aucune puissance et le système ne contient pas de protection industrielle de compresseur.")
    add("La LDR fournit une estimation basée sur le modèle du simulateur, sans étalonnage matériel. Le DHT22 "
        "est secondaire ; son indisponibilité est affichée sans remplacer la sonde principale. Les réglages "
        "ne sont pas persistants, et aucun journal non volatil ni service réseau n’est annoncé comme réalisé.")
    add("Le défaut de sonde, les cas non finis et le débordement temporel sont validés sur PC. La remise exige "
        "de comprendre les choix, de vérifier l’identité portée sur ce rapport et de reproduire la démonstration.")
    sub("Améliorations possibles")
    add("Une suite matérielle pourrait ajouter un temps minimal entre deux démarrages du compresseur, un "
        "étalonnage des mesures, un historique persistant et une configuration sauvegardée. Ces pistes ne "
        "font pas partie des fonctionnalités livrées.")
    sub("Reproduire et préparer les livrables")
    add("1. Ouvrir le dossier complet dans VS Code et compiler avec PlatformIO.<br/>"
        "2. Lancer Wokwi avec F1 ; reproduire les manipulations de la page 6.<br/>"
        "3. Consulter README.md, docs/TESTS.md et les traces de validation.<br/>"
        "4. Régénérer le rapport si nécessaire : python tools/create_report.py.<br/>"
        "5. Générer l’archive : python tools/package_project.py.")
    if link:
        add(f"Simulation partagée : <link href='{escape(link)}' color='#087F8C'>{escape(link)}</link>", "SmallS")
    else:
        add("Lien de simulation : voir docs/REMISE.txt. Les fichiers Wokwi Web sont fournis pour enregistrer "
            "la version finale sur le compte de l’étudiant.", "SmallS")
    if github:
        add(f"Code source : <link href='{escape(github)}' color='#087F8C'>{escape(github)}</link>", "SmallS")
    add("D’après le sujet, la remise officielle se fait sur Google Classroom avant le 12 décembre 2026 à 23 h 59. "
        "Le projet ne réalise pas ce dépôt à la place de l’étudiant.", "SmallS")
    sub("Documentation technique utilisée")
    for name, url in [
        ("PlatformIO — carte ESP32", "https://docs.platformio.org/en/latest/boards/espressif32/esp32dev.html"),
        ("Wokwi — projet PlatformIO", "https://docs.wokwi.com/vscode/platformio"),
        ("Wokwi — DS18B20", "https://docs.wokwi.com/parts/wokwi-ds18b20"),
        ("Wokwi — DHT22", "https://docs.wokwi.com/parts/wokwi-dht22"),
        ("Wokwi — LDR et LCD", "https://docs.wokwi.com/parts/wokwi-photoresistor-sensor"),
        ("Wokwi — firmware personnalisé", "https://docs.wokwi.com/guides/esp32"),
    ]:
        add(f"<link href='{url}' color='#087F8C'>{name}</link>", "SmallS")

    def decorate(canvas, doc):
        width, height = A4
        canvas.saveState()
        canvas.setStrokeColor(ACCENT)
        canvas.setLineWidth(1)
        canvas.line(52, height - 40, width - 52, height - 40)
        canvas.setFillColor(GREY)
        canvas.setFont("Body", 8)
        canvas.drawString(52, height - 31, "S.C.C.S.  /  ESP32 · PlatformIO · Wokwi")
        canvas.drawRightString(width - 52, height - 31, "2GII  |  2026–2027")
        canvas.line(52, 39, width - 52, 39)
        canvas.drawString(52, 25, "Mini-projet Systèmes programmables — version technique du 08/11/2026")
        canvas.drawRightString(width - 52, 25, f"{doc.page} / 8")
        canvas.restoreState()

    target = DOCS / "Rapport_SCCS.pdf"
    document = SimpleDocTemplate(str(target), pagesize=A4, rightMargin=52, leftMargin=52,
                                 topMargin=62, bottomMargin=53,
                                 title="SCCS — Surveillance de chambre froide", author=author)
    document.build(flow, onFirstPage=decorate, onLaterPages=decorate)
    print("Rapport genere :", target)


if __name__ == "__main__":
    main()
