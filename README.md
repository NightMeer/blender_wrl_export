Absolut! Eine gute Projektbeschreibung ist essenziell. Sie dient als Handbuch, als Aushängeschild und als Dokumentation für die Zukunft. Hier ist eine umfassende Projektbeschreibung im Markdown-Format, die perfekt für eine `README.md`-Datei in einem GitHub-Repository oder als allgemeine Dokumentation geeignet ist.

---

# Blender-WRL-Export

Ein robuster, stabiler und für CAD-Workflows optimierter VRML 2.0 (`.wrl`) Exporteur für Blender 4.x.

## Über dieses Projekt

Dieses Blender-Add-on wurde entwickelt, um eine kritische Lücke zu füllen: den zuverlässigen Export von 3D-Modellen in das VRML 2.0-Format, insbesondere für die Verwendung in CAD-Software wie **KiCad**.

Standardmäßig fehlt modernen Blender-Versionen ein nativer, fehlerfreier WRL-Exporter. Bestehende Lösungen sind oft veraltet oder nicht für die spezifischen Anforderungen von CAD-Programmen (korrekte Skalierung, Achsen, Multi-Material-Unterstützung) ausgelegt.

Dieses Plugin wurde von Grund auf neu entwickelt und iterativ verbessert, um genau diese Probleme zu lösen. Es bietet einen stabilen, intuitiven und vorhersehbaren Workflow, um Ihre Blender-Modelle schnell und korrekt auf Ihre Leiterplatten zu bekommen.

## Features

*   **VRML 2.0 (VRML97) Konformität:** Exportiert in den modernen Standard, der von KiCad und anderen Viewern erwartet wird.
*   **Stabiler Multi-Material-Export:** Weisen Sie einem Objekt mehrere Materialien (Farben) zu. Das Plugin teilt das Objekt beim Export intelligent in separate, korrekt gefärbte Teile auf, ohne Blender zum Absturz zu bringen.
*   **Optimiert für den KiCad-Workflow:**
    *   **Automatische Einheiten-Korrektur:** Eine Ein-Klick-Option (`Blender-Einheitenfehler korrigieren`) behebt ein tiefgreifendes Skalierungsproblem in Blender und sorgt für eine perfekte 1:1-Größe in KiCad.
    *   **Automatische Achsen-Konvertierung:** Konvertiert Blenders Z-Up-Koordinatensystem in das Y-Up-System von KiCad, sodass Ihre Modelle aufrecht stehen und nicht liegen.
*   **Intuitive Farberkennung:** Liest Farben direkt aus den **`Viewport Display`**-Einstellungen des Materials – genau dort, wo man es für einfache CAD-Modelle erwartet.
*   **Intelligente Objektauswahl:** Exportiert wahlweise nur die ausgewählten Objekte oder, falls nichts ausgewählt ist, alle sichtbaren Objekte der Szene.
*   **Professionelle Add-on-Struktur:** Wird als einfach zu installierende `.zip`-Datei bereitgestellt und folgt den Best Practices für Blender-Add-ons.
*   **Keine Abhängigkeiten:** Läuft eigenständig ohne die Notwendigkeit, andere Add-ons zu installieren.

## Installation

1.  Laden Sie die neueste Version als `blender_wrl_export.zip`-Datei herunter.
2.  Öffnen Sie Blender und gehen Sie zu `Edit > Preferences > Add-ons`.
3.  **WICHTIG:** Falls eine ältere Version dieses Add-ons installiert ist, entfernen Sie diese zuerst und starten Sie Blender neu.
4.  Klicken Sie auf `Install...` und wählen Sie die heruntergeladene `blender_wrl_export.zip`-Datei aus.
5.  Aktivieren Sie das Add-on, indem Sie das Kästchen neben "Import-Export: Blender-WRL-Export" anklicken.

Das Add-on ist nun unter `Datei > Export > Blender WRL Export (.wrl)` verfügbar.

## Der "Goldene Workflow" für perfekte KiCad-Modelle

Folgen Sie diesen Schritten exakt, um konsistente und fehlerfreie Ergebnisse zu erzielen.

### Teil 1: Vorbereitung in Blender

1.  **Modellieren in Millimetern:** Stellen Sie Ihre Szenen-Einheiten korrekt ein (`Scene Properties > Units`).
    *   `Unit System`: `Metric`
    *   `Unit Scale`: `0.001`
    *   `Length`: `Millimeters`
    Modellieren Sie nun so, dass die angezeigten Dimensionen den echten Millimeter-Werten entsprechen (z.B. ein Würfel mit `10mm` Kantenlänge).

2.  **Materialien und Farben zuweisen:**
    *   Erstellen Sie im `Material Properties`-Tab für jede gewünschte Farbe ein Material.
    *   Stellen Sie die Farbe für jedes Material im Abschnitt **`Viewport Display`** ein.
    *   Weisen Sie die Materialien im `Edit Mode` den entsprechenden Flächen Ihres Objekts über den `Assign`-Button zu.

3.  **Ursprung (Origin) korrekt platzieren:**
    *   Der Ursprung des Objekts ist der Einfügepunkt in KiCad. Er sollte meistens mittig auf der Unterseite des Modells liegen.
    *   *Tipp:* Wählen Sie im `Edit Mode` die unterste Fläche aus, drücken Sie `Shift + S` → `Cursor to Selected`. Zurück im `Object Mode`: `Object > Set Origin > Origin to 3D Cursor`.

4.  **Transformationen anwenden (KRITISCH):**
    *   Wählen Sie Ihr fertiges Objekt im `Object Mode` aus.
    *   Drücken Sie `Ctrl + A` und wählen Sie **`All Transforms`**. Der `Scale` im `Item`-Tab muss danach auf `(1.0, 1.0, 1.0)` stehen.

### Teil 2: Export-Einstellungen

1.  Wählen Sie Ihr Objekt aus und gehen Sie zu `Datei > Export > Blender WRL Export (.wrl)`.
2.  Verwenden Sie diese idealen Einstellungen für KiCad:
    *   **Nur Auswahl:** `An`
    *   **Blender-Einheitenfehler korrigieren:** `An` (Dies ist der wichtigste Schalter!)
    *   **Manueller Skalierungsfaktor:** `1.0`
    *   **Achsen für KiCad konvertieren:** `An`
    *   **Materialien exportieren:** `An`

### Teil 3: Integration in KiCad

1.  **Speicherort:** Speichern Sie die `.wrl`-Datei in einen `3dmodels`-Ordner innerhalb Ihres KiCad-Projektverzeichnisses.
2.  **Verknüpfung:** Verknüpfen Sie das Modell im Footprint-Editor mit dem Pfad `"${KIPRJMOD}/3dmodels/ihr_modell.wrl"`.
3.  Das Modell sollte nun perfekt skaliert, rotiert und gefärbt auf Ihrem Footprint erscheinen.

## Fehlerbehebung (Troubleshooting)

*   **Mein Modell ist in KiCad unsichtbar:**
    *   Prüfen Sie den Pfad im Footprint-Editor. Er muss die Variable `${KIPRJMOD}` verwenden.
    *   Haben Sie den Ursprung in Blender korrekt gesetzt? Ist er weit vom Modell entfernt?
*   **Mein Modell ist falsch skaliert oder liegt flach:**
    *   Haben Sie `Ctrl + A -> All Transforms` in Blender angewendet?
    *   Sind die Optionen `Einheitenfehler korrigieren` und `Achsen konvertieren` im Exporter aktiviert?
*   **Die Farben sind falsch oder fehlen:**
    *   Haben Sie die Farbe im `Viewport Display`-Bereich des Materials eingestellt (nicht im Shader)?
    *   Haben Sie im `Edit Mode` die Materialien korrekt den Flächen zugewiesen (`Assign`-Button)?
    *   Ist die Option `Materialien exportieren` im Exporter aktiviert?

---
**Lizenz:** Dieses Projekt steht unter der [MIT-Lizenz](LICENSE).