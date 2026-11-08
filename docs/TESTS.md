# Protocole de validation S.C.C.S.

Le système possède deux niveaux de validation : les règles C++ sur PC et l'exécution du firmware dans le simulateur Wokwi. Une compilation seule ne remplace pas la simulation.

## 1. Compilation ESP32

Exécuter `python tools/build_project.py` ou le bouton Build de PlatformIO.

La trace est enregistrée dans `docs/compilation.txt`. Le programme produit `firmware.bin`, `firmware.elf` et `firmware/SCCS_merged.bin`. Ce dernier contient aussi le bootloader et la table des partitions ; il est utilisable par le chargement manuel du site Wokwi.

Deux avertissements `extra tokens at end of #undef directive` apparaissent dans la bibliothèque tierce OneWire 2.3.8 lors de la première compilation complète. Ils n'empêchent pas la construction du firmware ; les sources applicatives compilent sans erreur.

## 2. Tests des règles sur PC

Exécuter `python tools/test_project.py`. Le script compile **les véritables fichiers** `src/controller.cpp` et `src/config.cpp`, puis les exécute avec les mesures de test. Il ne recopie pas l'algorithme dans un simulateur séparé.

Les 20 scénarios couvrent 59 assertions :

1. Température normale et porte fermée.
2. Différence entre exactement 8 °C et une température supérieure à 8 °C.
3. Hystérésis du refroidissement à 4 et 6 °C.
4. Hystérésis d'effacement de l'alarme à 7,5 °C.
5. Différence entre exactement 30 secondes et plus de 30 secondes.
6. Alarmes simultanées et effacement indépendant.
7. Fermeture et réouverture de la porte : compteur remis à zéro.
8. Suspension du refroidissement et reprise de la demande mémorisée.
9. Lumière forte porte fermée pendant 5 secondes.
10. Lumière normale pendant une ouverture et nouvelle temporisation à la fermeture.
11. Initialisation, sonde absente et récupération.
12. Sonde invalide, NaN et mesure hors plage.
13. Dernière mesure trop ancienne.
14. DHT22 secondaire indisponible.
15. Débordement de `millis()` pendant une ouverture.
16. Anti-rebond dans les deux sens.
17. Anti-rebond au débordement de `millis()`.
18. Rejet des configurations incohérentes ou non finies.
19. Modification du délai de porte.
20. Mise à jour de la température pendant la temporisation de porte.

Le même script vérifie ensuite les dix correspondances entre GPIO et `diagram.json`, les alimentations, les résistances des LED et les pull-up. Il contrôle l'absence de `delay()` dans les sources applicatives. Le résultat est enregistré dans `docs/tests_locaux.txt`.

## 3. Simulation Wokwi à reproduire

Valeurs initiales : DS18B20 à 4 °C, DHT22 à 24 °C et 45 %, porte à gauche, LDR à 10 lx. Les durées ci-dessous sont des **secondes simulées**, visibles sur le chronomètre Wokwi ou dans `t_ms`. Sur un PC lent, elles prennent davantage de temps réel.

| Scénario | Manipulation | Observation à vérifier |
|---|---|---|
| Normal | Lancer avec les valeurs initiales ; attendre la première acquisition DHT22 | LCD : 4 °C / NORMAL ; LED verte ; `cooling=0 alarms=NONE` |
| Température critique | Cliquer sur le DS18B20 et choisir 9 °C | LCD : ALARME / TEMP CRITIQUE ; LED bleue ; rouge clignotante et buzzer ; `alarms=TEMP` |
| Hystérésis | Après 9 °C : choisir 7,5, puis 5, 4, 5 et 6 °C ; attendre chaque acquisition | À 7,5 : alarme effacée ; à 5 : froid maintenu ; à 4 : arrêt ; à 5 : repos maintenu ; à 6 : redémarrage |
| Porte | Remettre 4 °C ; basculer l'interrupteur à droite ; laisser ouvert plus de 30 s | Avant le délai : PORTE ; après : ALARME / PORTE ; `alarms=DOOR` |
| Retour à la normale | Refermer la porte, conserver 4 °C et une faible lumière | Retour NORMAL ; aucun bip ; rouge éteinte |
| Réactivité | Pendant les 30 s d'ouverture, passer le DS18B20 à 9 °C puis à 4 °C | TEMP apparaît puis disparaît avant la fin du compteur ; froid suspendu ; les mesures continuent |
| Lumière oubliée | Porte fermée, choisir 1000 lx sur la LDR pendant au moins 5 s | `alarms=LIGHT`, message LUMIERE ALLUMEE ; retour normal à 10 lx |
| Réglages | Entrer `SET DOOR 5`, puis `RESET` avec un saut de ligne | `OK SET`, délai affiché à 5 s ; `OK RESET`, retour à 30 s |

La simulation ne calcule pas un refroidissement physique : déplacer le curseur du DS18B20 représente volontairement cette évolution.

Les observations réellement collectées sont consignées dans `docs/tests_wokwi.json`, avec l'identification du firmware utilisé. Les captures correspondantes sont dans `docs/captures/`. Le journal série est dans `docs/trace_wokwi.txt`. La validation finale charge le binaire produit par PlatformIO dans le simulateur Web, au moyen de **Upload Firmware and Start Simulation**, pour tester le même programme que celui chargé par `wokwi.toml` dans VS Code.

L'utilitaire de maintenance `tools/validate_wokwi_browser.py` rejoue ces manipulations dans un navigateur Chrome de test exposant CDP sur `127.0.0.1:9223` ; il nécessite Playwright. Il n'est pas nécessaire pour la démonstration manuelle, ne contourne aucune connexion et ne contient aucune clé.

## 4. Ce que les résultats ne démontrent pas

Le défaut de sonde, les rebonds aux frontières temporelles et le débordement de `millis()` sont testés sur PC. Aucune panne matérielle réelle n'est revendiquée comme testée. Les captures montrent un simulateur, sans essai de chambre froide physique, d'alimentation de puissance ou de système de sécurité industriel.

