# 📋 VibeSpool Development Backlog

## ✅ Abgeschlossen (v2.0.0 - "The Cost Center & Enterprise Update")
- [x] **Globales Cost Center:** Vollständige Historie aller Drucke (manuell & Cloud) über alle Spulen hinweg im Finanz-Dashboard.
- [x] **Gewerbe-Kalkulation (Marge & Verschleiß):** Berechnung von Maschinenabnutzung (pro Stunde) und automatischer Aufschlag einer Gewinnmarge für den Verkaufspreis.
- [x] **Auto-Heal & Retro-Fit:** Einträge in der Historie können nachträglich bearbeitet werden. VibeSpool korrigiert magisch das Spulengewicht und das 7-Tage-Diagramm. Eigene Kalkulator-Buttons berechnen fehlende alte Kosten rückwirkend auf Knopfdruck.
- [x] **Individuelles Leergewicht (Einweg-Spulen):** Spulen können nun ein eigenes, einmaliges Leergewicht abspeichern, ohne dass dafür eine globale Vorlage angelegt werden muss.
- [x] **Omni-Live-Suche:** Neues, mächtiges Suchfeld im Hauptfenster, das in Echtzeit über alle Daten (ID, Name, Farbe, Notiz, etc.) filtert.
- [x] **🧮 Quick-Cost Rechner:** Standalone-Werkzeug in der Seitenleiste, um schnell Kundenangebote zu berechnen, ohne eine Spule zu belasten.
- [x] **UX/UI Polish:** Fenster binden sich nun korrekt ans Hauptfenster (Transient), Skalierungsprobleme in Windows wurden behoben, und alle Dropdown-Listen sortieren sich automatisch alphabetisch.

## ✅ Abgeschlossen (v1.10.0 - "The Smart Pro Update")
- [x] **☁️ Bambu Cloud API & Smart-Match:** Vollständige Cloud-Integration (90-Tage Auto-Login, 2FA-Support).
- [x] **💰 Druckkosten-Rechner & Finanzen:** Lokale Stromkosten (Wattzahl + kWh-Preis) und Materialkosten.
- [x] **📊 Unified Analytics Dashboard:** Finanz- und Statistik-Dashboard mit 7-Tage-Verbrauchs-Balkendiagramm.
- [x] **📖 Spulen-Logbuch:** Detaillierter Kontoauszug für jede Spule.
- [x] **📥 System-Tray & Hintergrund-Modus:** App minimiert in die Taskleiste.
- [x] **Alphanumerische IDs:** Support für Text-IDs (A134, PLA-01).

## 🚀 Priorität 1: Next Steps (v2.1.0)
- [ ] **🎨 Custom Label Designer:** Baukasten zum freien Gestalten von Etiketten (Logos hinzufügen, Schriftarten ändern).
- [ ] **🤖 Auto-Deduction ohne Dialog:** Option hinzufügen, damit Single-Color Cloud-Drucke komplett unsichtbar im Hintergrund abgezogen werden.

## 🔮 Langzeit-Vision (v3.0)
- [ ] **🗄️ SQLite Migration:** Wechsel von JSON auf eine echte, relationale Datenbank für noch mehr Performance bei hunderten Spulen.
- [ ] **📂 3MF Deep-Dive FTP Parsing:** Automatisches Auslesen der Gewichte pro Slot direkt vom Drucker-Speicher, noch bevor die Cloud es meldet.