# 📋 VibeSpool Development Backlog

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

## 🚀 Priorität 1: Next Steps (v1.11.0 - "The Creative Update")
- [ ] **🎨 Custom Label Designer:** Baukasten zum freien Gestalten von Etiketten (Logos hinzufügen, Schriftarten ändern).
- [ ] **🤖 Auto-Deduction ohne Dialog:** Option hinzufügen, damit Single-Color Cloud-Drucke komplett unsichtbar im Hintergrund abgezogen werden.
- [ ] **📈 Maschinen-Verschleiß:** Den Druckkosten-Rechner um eine Pauschale für Maschinenabnutzung (Cent pro Stunde) erweitern.

## 🔮 Langzeit-Vision (v2.0)
- [ ] **🗄️ SQLite Migration:** Wechsel von JSON auf eine echte, relationale Datenbank für noch mehr Performance bei hunderten Spulen.
- [ ] **📂 3MF Deep-Dive FTP Parsing:** Automatisches Auslesen der Gewichte pro Slot direkt vom Drucker-Speicher, noch bevor die Cloud es meldet.