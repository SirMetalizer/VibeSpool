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
- [x] **☁️ Bambu Cloud API & Smart-Match:** Vollständige Cloud-Integration (90-Tage Auto-Login, 2FA-Support). VibeSpool rät automatisch, welche Spule in welchem AMS-Slot für den Cloud-Druck genutzt wurde.
- [x] **💰 Druckkosten-Rechner & Finanzen:** Reale Druckkosten-Berechnung inklusive lokaler Stromkosten (Wattzahl + kWh-Preis) und exakten Materialkosten (basierend auf dem Kaufpreis der Spule).
- [x] **📊 Unified Analytics Dashboard:** Neues, vereintes Finanz- und Statistik-Dashboard mit "Ø Preis/kg" Auswertung und 7-Tage-Verbrauchs-Balkendiagramm.
- [x] **📖 Spulen-Logbuch:** Jede Spule hat nun ihren eigenen "Lebenslauf" mit einem detaillierten Kontoauszug (Druckauftrag, Datum, Gramm-Abzug, Materialkosten).
- [x] **📥 System-Tray & Hintergrund-Modus:** App kann nun in den Windows-Tray (neben die Uhr) minimiert werden und lauscht unsichtbar im Hintergrund weiter auf den Drucker.
- [x] **🔔 Windows Toast Notifications:** Elegante, dunkle Pop-up-Benachrichtigungen bei automatischen Abzügen und Sync-Events.
- [x] **📘 In-App HowTo (Mini-Wiki):** Integriertes, scrollbares Handbuch direkt im Programm, das alle Features erklärt.
- [x] **Alphanumerische IDs:** Support für Text-IDs (A134, PLA-01).
- [x] **Hersteller-Barcode Scanner:** Handy-Scanner liest jetzt auch 1D-Strichcodes auf Originalverpackungen und lernt diese.

## 🐛 Hotfixes & UX-Polish (v2.0.1)
- [X] **BUGFIX:** Nozzle- und Bed-Temp Felder verdoppeln ihre Werte beim Laden, da die Insert-Befehle im Code versehentlich doppelt ausgeführt werden.
- [x] **UX-FIX:** Systematische Prüfung aller Pop-up-Fenster: Buttons müssen hart an den unteren Rand gekoppelt werden (`side="bottom"`), damit sie bei hoher Windows-Skalierung nicht mehr abgeschnitten werden.
- [ ] **UX-EVALUATION:** Prüfung, ob wir Dialoge/Untermenüs künftig als "Klappmenüs" (Accordions) direkt ins Hauptfenster integrieren können, um die "Pop-up-Flut" zu reduzieren.

## 🚀 Priorität 1: Next Steps (v2.1.0)
- [ ] **📝 Auftrags-Planer (Print Queue & MES):** Neues Planungs-Tool für kommende Drucke. Zuweisung von Kunde/Titel, Modell-Links, Spulen (inkl. Multi-Color ID 1 + ID 2) und Notizen ("Marble für Body, Grün für Schrift"). Später direkt mit Cloud-Abzug verknüpfbar.
- [ ] **🎨 Custom Label Designer:** Baukasten zum freien Gestalten von Etiketten (Logos hinzufügen, Schriftarten ändern).

## 🔮 Langzeit-Vision (v3.0)
- [ ] **📂 3MF Deep-Dive FTP Parsing:** Automatisches Auslesen der Gewichte pro Slot direkt vom Drucker-Speicher, noch bevor die Cloud es meldet.