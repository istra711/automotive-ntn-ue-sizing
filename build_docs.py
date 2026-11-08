"""Build the English and German ODT reports of the NTN UE sizing study.

Usage::

    python build_docs.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "tools"))
sys.path.insert(0, str(HERE))

from odt_builder import Report          # noqa: E402
import ntn_model as nm                  # noqa: E402

DOCS = HERE / "docs"
FIG = DOCS / "figures"
RES = json.loads((DOCS / "results.json").read_text(encoding="utf-8"))


def export_pdf(odt: Path) -> Path | None:
    exe = shutil.which("soffice") or shutil.which("libreoffice")
    if exe is None:
        for cand in (r"C:\Program Files\LibreOffice\program\soffice.exe",
                     r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"):
            if Path(cand).is_file():
                exe = cand
                break
    if exe is None:
        return None
    subprocess.run([exe, "--headless", "--convert-to", "pdf",
                    "--outdir", str(odt.parent), str(odt)],
                   check=False, capture_output=True)
    pdf = odt.with_suffix(".pdf")
    return pdf if pdf.is_file() else None


def build(lang: str) -> Path:
    de = lang == "de"

    def T(a: str, b: str) -> str:
        return b if de else a

    def N(v: float, d: int = 1) -> str:
        s = f"{v:.{d}f}"
        return s.replace(".", ",") if de else s

    bands = RES["bands"]
    arrays = RES["arrays"]
    patch = RES["patch"]
    link = RES["link"]
    rec = RES["recommendation_roof_pod"]

    b255, b256 = "n255", "n256"
    a255 = {a["n"]: a for a in arrays[b255]}
    a256 = {a["n"]: a for a in arrays[b256]}

    r = Report(
        title="Automotive NTN UE Antenna Sizing Study",
        author="VisualopenEMS · openEMS workflow",
        subject=T("Sizing of a 3GPP n255 / n256 patch array for a vehicle",
                  "Dimensionierung eines 3GPP-n255/n256-Patch-Arrays für ein "
                  "Fahrzeug"),
        header=T("Automotive NTN UE sizing study · n255 (L-band) / n256 "
                 "(S-band)",
                 "Automotive-NTN-UE-Sizing-Studie · n255 (L-Band) / n256 "
                 "(S-Band)"),
        toc_title=T("Contents", "Inhalt"),
    )
    r.figure_word = T("Figure", "Bild")
    r.table_word = T("Table", "Tabelle")

    # ------------------------------------------------------------- cover
    r.p("Automotive NTN UE Antenna Sizing Study", style="Title")
    r.p(T("How large does a 3GPP n255 / n256 patch array become on a vehicle – "
          "and is that size realistic?",
          "Wie groß wird ein 3GPP-n255/n256-Patch-Array auf einem Fahrzeug – "
          "und ist diese Größe realistisch?"), style="Subtitle")
    r.p("", style="Rule")
    r.p(T("Closed-form sizing study (aperture, scan, link budget)",
          "Geschlossene Dimensionierungsstudie (Apertur, Scan, Link-Budget)"),
        style="CoverMeta")
    r.p(T("Bands: n255 L-band 1525–1559 MHz (Rx) / n256 S-band "
          "2170–2200 MHz (Rx)",
          "Bänder: n255 L-Band 1525–1559 MHz (Rx) / n256 S-Band "
          "2170–2200 MHz (Rx)"), style="CoverMeta")
    r.p(f"RO4003C · h = {N(nm.BANDS[0].h_mm, 2)} / "
        f"{N(nm.BANDS[1].h_mm, 2)} mm", style="CoverMeta")
    r.p(date.today().isoformat(), style="CoverMeta")

    r.start_main()
    r.toc()
    r.page_break()

    # ------------------------------------------------------------- 1
    r.h1("1", T("Executive summary", "Zusammenfassung"))
    r.p(T(
        "This study answers a packaging question, not a full-wave question: "
        "how much roof area does an electronically steered patch array need "
        "for a 3GPP NTN user terminal in the n255 (L-band) and n256 (S-band) "
        "bands, and does that fit on a passenger car?  The answer is obtained "
        "analytically from the lambda/2 lattice, the aperture directivity, a "
        "scan-loss model and a downlink link budget – no FDTD run is required "
        "to make the packaging decision.",
        "Diese Studie beantwortet keine Vollwellen-, sondern eine "
        "Packaging-Frage: Wie viel Dachfläche braucht ein elektronisch "
        "geschwenktes Patch-Array für ein 3GPP-NTN-Endgerät in den Bändern "
        "n255 (L-Band) und n256 (S-Band) – und passt das auf einen Pkw?  Die "
        "Antwort folgt analytisch aus λ/2-Raster, Apertur-Richtfaktor, einem "
        "Scan-Verlustmodell und einem Downlink-Link-Budget; für die "
        "Packaging-Entscheidung ist kein FDTD-Lauf nötig."))
    r.bullets([
        T(f"The element is large: {N(patch[b255]['l_mm'])} × "
          f"{N(patch[b255]['w_mm'])} mm at n255 and {N(patch[b256]['l_mm'])} × "
          f"{N(patch[b256]['w_mm'])} mm at n256, on a λ/2 lattice of "
          f"{N(bands[b255]['lattice_mm'])} mm and "
          f"{N(bands[b256]['lattice_mm'])} mm.",
          f"Das Element ist groß: {N(patch[b255]['l_mm'])} × "
          f"{N(patch[b255]['w_mm'])} mm bei n255 und {N(patch[b256]['l_mm'])} × "
          f"{N(patch[b256]['w_mm'])} mm bei n256, auf einem λ/2-Raster von "
          f"{N(bands[b255]['lattice_mm'])} mm bzw. "
          f"{N(bands[b256]['lattice_mm'])} mm."),
        T(f"A 2×2 array already needs {N(a255[2]['module_mm']/10, 0)} cm "
          f"(n255) and {N(a256[2]['module_mm']/10, 0)} cm (n256) of module "
          f"edge length; 4×4 needs {N(a255[4]['module_mm']/10, 0)} cm and "
          f"{N(a256[4]['module_mm']/10, 0)} cm.",
          f"Ein 2×2-Array benötigt bereits {N(a255[2]['module_mm']/10, 0)} cm "
          f"(n255) bzw. {N(a256[2]['module_mm']/10, 0)} cm (n256) "
          f"Modulkantenlänge; 4×4 braucht {N(a255[4]['module_mm']/10, 0)} cm "
          f"bzw. {N(a256[4]['module_mm']/10, 0)} cm."),
        T("n256 is feasible on a car roof: 2×2 fits a roof pod, 5×5 fits the "
          "roof centre.  n255 is tight: 2×2 needs 27 cm, i.e. more than a "
          "25 cm roof pod; 3×3 fits the roof centre.",
          "n256 ist auf dem Pkw-Dach machbar: 2×2 passt in ein Dachmodul, "
          "5×5 in die Dachmitte.  n255 ist eng: 2×2 braucht 27 cm, also mehr "
          "als ein 25-cm-Dachmodul; 3×3 passt in die Dachmitte."),
        T("From the link budget, 2×2 closes a low-rate NB-NTN link with large "
          "margin; even the 85 dBHz broadband-class target is reached with "
          "2×2 (n255) and 3×3 (n256) at the assumed EIRP.  The packaging "
          "size, not the link, is the binding constraint.",
          "Link-Budget-seitig schließt bereits 2×2 einen schmalbandigen "
          "NB-NTN-Link mit großer Reserve; selbst das 85-dBHz-Ziel der "
          "Broadband-Klasse wird beim angenommenen EIRP mit 2×2 (n255) und "
          "3×3 (n256) erreicht.  Die begrenzende Größe ist das Packaging, "
          "nicht der Link."),
        T("n255 and n256 cannot share one aperture: the n255 patch is larger "
          "than the n256 lattice cell.  Two separate modules (or a broadband "
          "shared aperture) are required.",
          "n255 und n256 können sich keine Apertur teilen: Das n255-Patch ist "
          "größer als die n256-Rasterzelle.  Zwei getrennte Module (oder eine "
          "breitbandige gemeinsame Apertur) sind nötig."),
    ])

    # ------------------------------------------------------------- 2
    r.h1("2", T("Scope, method and assumptions", "Umfang, Methode und Annahmen"))
    r.p(T(
        "All numbers are closed-form.  The chain is: substrate and band → "
        "patch dimensions (Hammerstad) → λ/2 lattice at the upper band edge → "
        "aperture directivity D = 4πA/λ² → feed and scan losses → downlink "
        "C/N₀.  The model is deliberately conservative where a full-wave "
        "result would be needed: the feed loss is a flat 1.5 dB and the scan "
        "loss adds a patch-like element roll-off on top of the aperture "
        "projection.",
        "Alle Zahlen sind geschlossen berechnet.  Die Kette ist: Substrat und "
        "Band → Patchabmessungen (Hammerstad) → λ/2-Raster an der oberen "
        "Bandkante → Apertur-Richtfaktor D = 4πA/λ² → Speise- und "
        "Scan-Verluste → Downlink-C/N₀.  Wo ein Vollwellenergebnis nötig "
        "wäre, ist das Modell bewusst konservativ: 1,5 dB pauschaler "
        "Speiseverlust, und der Scan-Verlust enthält zusätzlich zur "
        "Aperturprojektion einen patchtypischen Elementabfall."))
    r.table(
        T("Assumptions used throughout the study.",
          "Durchgängig verwendete Annahmen."),
        [T("Item", "Größe"), T("Value", "Wert"), T("Comment", "Kommentar")],
        [
            [T("Substrate", "Substrat"), "Rogers RO4003C",
             "εr = 3.55, tan δ = 0.0027"],
            [T("Lattice", "Raster"),
             T("λ/2 at band edge", "λ/2 an der Bandkante"),
             T("no grating lobes up to 90°", "keine Grating Lobes bis 90°")],
            [T("Feed loss", "Speiseverlust"), f"{N(1.5)} dB",
             T("corporate feed + radome", "Corporate-Speisung + Radom")],
            [T("Scan loss model", "Scan-Verlustmodell"),
             "15·log10(cos θ₀)",
             T("aperture + element roll-off", "Apertur + Elementabfall")],
            [T("Satellite altitude", "Satellitenhöhe"),
             f"{N(nm.H_SAT/1e3, 0)} km",
             T("Amazon Leo upper shell", "obere Amazon-Leo-Schale")],
            [T("Satellite EIRP", "Satelliten-EIRP"),
             f"{N(link['eirp_dbw'], 0)} dBW",
             T("placeholder – replace with operator data",
               "Platzhalter – durch Betreiberdaten ersetzen")],
            [T("Receiver NF", "Empfänger-NF"), f"{N(link['nf_db'])} dB",
             T("automotive-grade LNA", "Automotive-LNA")],
            [T("Targets", "Ziele"),
             "55 / 70 / 85 dBHz",
             T("NB-NTN / moderate / broadband class",
               "NB-NTN / mittel / Broadband-Klasse")],
        ],
        widths=[3.6, 3.4, 5.6])

    # ------------------------------------------------------------- 3
    r.h1("3", T("Bands and element", "Bänder und Element"))
    r.p(T(
        "3GPP defines the NTN bands n255 (L-band, Rx 1525–1559 MHz, Tx "
        "1626.5–1660.5 MHz) and n256 (S-band, Rx 2170–2200 MHz, Tx "
        "1980–2010 MHz).  The array is sized for the receive direction, which "
        "is the G/T-critical one; the transmit direction uses the same "
        "aperture with a diplexer.",
        "3GPP definiert die NTN-Bänder n255 (L-Band, Rx 1525–1559 MHz, Tx "
        "1626,5–1660,5 MHz) und n256 (S-Band, Rx 2170–2200 MHz, Tx "
        "1980–2010 MHz).  Dimensioniert wird für die Empfangsrichtung, die "
        "für G/T kritisch ist; die Senderichtung nutzt dieselbe Apertur über "
        "einen Diplexer."))
    r.table(
        T("Band parameters and resulting element geometry.",
          "Bandparameter und resultierende Elementgeometrie."),
        [T("Quantity", "Größe"), "n255", "n256"],
        [
            [T("Receive band", "Empfangsband"),
             "1525–1559 MHz", "2170–2200 MHz"],
            [T("Transmit band", "Sende band"),
             "1626.5–1660.5 MHz", "1980–2010 MHz"],
            [T("Centre frequency", "Mittenfrequenz"),
             f"{N(bands[b255]['f_ghz'], 3)} GHz",
             f"{N(bands[b256]['f_ghz'], 3)} GHz"],
            [T("λ₀ at centre", "λ₀ bei Mittenfrequenz"),
             f"{N(bands[b255]['lam_mm'], 0)} mm",
             f"{N(bands[b256]['lam_mm'], 0)} mm"],
            [T("Lattice λ/2 (band edge)", "Raster λ/2 (Bandkante)"),
             f"{N(bands[b255]['lattice_mm'], 1)} mm",
             f"{N(bands[b256]['lattice_mm'], 1)} mm"],
            [T("Substrate height", "Substrathöhe"),
             f"{N(bands[b255]['h_mm'], 2)} mm",
             f"{N(bands[b256]['h_mm'], 2)} mm"],
            [T("Patch length L", "Patchlänge L"),
             f"{N(patch[b255]['l_mm'], 1)} mm",
             f"{N(patch[b256]['l_mm'], 1)} mm"],
            [T("Patch width W", "Patchbreite W"),
             f"{N(patch[b255]['w_mm'], 1)} mm",
             f"{N(patch[b256]['w_mm'], 1)} mm"],
        ],
        widths=[5.2, 4.6, 4.6])
    r.p(T(
        "The element is a single-layer rectangular patch on RO4003C, "
        "dimensioned with the Hammerstad relations at the band centre.  The "
        "lattice is set by the upper band edge so that no grating lobe can "
        "appear even at large scan angles.  Figure 1 shows both elements to "
        "scale together with their lattice cells.",
        "Das Element ist ein einlagiges Rechteck-Patch auf RO4003C, mit den "
        "Hammerstad-Beziehungen bei Bandmitte dimensioniert.  Das Raster "
        "richtet sich nach der oberen Bandkante, damit auch bei großen "
        "Scanwinkeln kein Grating Lobe entstehen kann.  Bild 1 zeigt beide "
        "Elemente maßstäblich mit ihren Rasterzellen."))
    r.figure(str(FIG / "fig01_geometry.png"),
             T("Element and lattice geometry at both bands (to scale).",
               "Element- und Rastergeometrie beider Bänder (maßstäblich)."),
             16.0)

    # ------------------------------------------------------------- 4
    r.h1("4", T("Array size versus gain", "Arraygröße und Gewinn"))
    r.p(T(
        "For an N×N array on a λ/2 lattice the aperture is (N·λ/2)², so "
        "D = 4πA/λ² collapses to D = π·N² (linear), i.e. 10·log10(πN²) dBi. "
        "Every doubling of N therefore adds 6.02 dB – independent of the "
        "band, because the lattice scales with the wavelength.",
        "Für ein N×N-Array auf λ/2-Raster ist die Apertur (N·λ/2)², damit "
        "vereinfacht sich D = 4πA/λ² zu D = π·N² (linear), also "
        "10·log10(πN²) dBi.  Jede Verdopplung von N bringt daher 6,02 dB – "
        "unabhängig vom Band, weil das Raster mit der Wellenlänge skaliert."))
    r.p(T(
        "Table 3 lists aperture, module size, directivity, realised broadside "
        "gain (1.5 dB feed loss) and the gain at 60° scan for both bands.  "
        "Figure 2 shows gain versus module edge length – the gain itself "
        "depends only on N, but the same gain needs a smaller module at n256.  "
        "Section 5 then compares those module sizes with the areas available "
        "on a vehicle (Figure 4).",
        "Tabelle 3 listet Apertur, Modulgröße, Richtfaktor, realisierten "
        "Broadside-Gewinn (1,5 dB Speiseverlust) und den Gewinn bei 60°-Scan "
        "für beide Bänder.  Bild 2 zeigt den Gewinn über der "
        "Modulkantenlänge – der Gewinn selbst hängt nur von N ab, aber "
        "derselbe Gewinn braucht bei n256 ein kleineres Modul.  Abschnitt 5 "
        "vergleicht diese Modulgrößen dann mit den am Fahrzeug verfügbaren "
        "Flächen (Bild 4)."))
    r.table(
        T("Array metrics for both bands (Rx).",
          "Array-Kennzahlen beider Bänder (Rx)."),
        [T("N×N", "N×N"), T("Elements", "Elemente"),
         T("Aperture", "Apertur"), T("Module", "Modul"),
         T("D", "D"), T("G", "G"), T("G at 60°", "G bei 60°")],
        [
            [f"{key} {a['n']}×{a['n']}", str(a["elements"]),
             f"{N(a['aperture_mm']/10, 0)} cm",
             f"{N(a['module_mm']/10, 0)} cm",
             f"{N(a['d_dbi'], 1)} dBi", f"{N(a['gain_broad_dbi'], 1)} dBi",
             f"{N(a['gain_scan60_dbi'], 1)} dBi"]
            for key in (b255, b256)
            for a in sorted(arrays[key], key=lambda x: x["n"])
        ],
        widths=[2.0, 2.2, 2.4, 2.4, 2.2, 2.2, 2.6],
        source=T("First block n255, second block n256; module = aperture + "
                 "2 × 0.2 λ₀ for housing and ground-plane margin.",
                 "Erster Block n255, zweiter Block n256; Modul = Apertur + "
                 "2 × 0,2 λ₀ für Gehäuse und Groundplane-Rand."))
    r.figure(str(FIG / "fig03_gain_vs_size.png"),
             T("Realised gain versus module edge length, broadside and at "
               "60° scan.", "Realisierter Gewinn über der Modulkantenlänge, "
               "Broadside und bei 60°-Scan."), 15.0)

    # ------------------------------------------------------------- 5
    r.h1("5", T("Scan and packaging", "Scan und Packaging"))
    r.p(T(
        "Electronic steering costs gain in two ways: the projected aperture "
        "shrinks with cos θ₀ and the patch element itself rolls off.  The "
        "model uses 15·log10(cos θ₀), which gives "
        f"{N(RES['scan']['scan_loss_45_deg_db'])} dB at 45° and "
        f"{N(RES['scan']['scan_loss_60_deg_db'])} dB at 60° (Figure 3).",
        "Elektronisches Schwenken kostet Gewinn auf zwei Wegen: Die "
        "projizierte Apertur sinkt mit cos θ₀, und das Patch-Element fällt "
        "selbst ab.  Das Modell nutzt 15·log10(cos θ₀), also "
        f"{N(RES['scan']['scan_loss_45_deg_db'])} dB bei 45° und "
        f"{N(RES['scan']['scan_loss_60_deg_db'])} dB bei 60° (Bild 3)."))
    r.figure(str(FIG / "fig04_scan_loss.png"),
             T("Scan loss model: aperture projection and additional element "
               "roll-off.", "Scan-Verlustmodell: Aperturprojektion und "
               "zusätzlicher Elementabfall."), 13.0)
    r.p(T(
        "Figure 4 compares the module edge length with four installation "
        "areas; Table 4 lists the largest array that fits each area.",
        "Bild 4 vergleicht die Modulkantenlänge mit vier Einbauflächen; "
        "Tabelle 4 listet das größte Array, das in jede Fläche passt."))
    r.figure(str(FIG / "fig02_footprints.png"),
             T("Module edge length versus the installation areas available on "
               "a vehicle.", "Modulkantenlänge im Vergleich zu den am Fahrzeug "
               "verfügbaren Einbauflächen."), 15.0)
    r.table(
        T("Largest array that fits a given installation area.",
          "Größtes Array, das in eine gegebene Einbaufläche passt."),
        [T("Area", "Fläche"), T("Size", "Größe"), "n255", "n256"],
        [
            [T("Shark fin", "Shark-Fin"), "15 × 10 cm",
             T("none", "keins"), T("none", "keins")],
            [T("Roof pod", "Dachmodul"), "25 × 25 cm",
             T("none (needs 27 cm)", "keins (27 cm nötig)"), "2×2"],
            [T("Car roof centre", "Dachmitte Pkw"), "40 × 40 cm", "3×3", "5×5"],
            [T("Van roof", "Van-Dach"), "60 × 40 cm", "3×3", "5×5"],
        ],
        widths=[4.4, 3.4, 4.4, 3.0],
        source=T("Module = aperture + 2 × 0.2 λ₀; the 40 cm depth of the van "
                 "roof limits the size more than its width.",
                 "Modul = Apertur + 2 × 0,2 λ₀; die 40 cm Tiefe des Van-Dachs "
                 "begrenzt stärker als die Breite."))

    # ------------------------------------------------------------- 6
    r.h1("6", T("Link budget", "Link-Budget"))
    r.p(T(
        "The downlink C/N₀ follows from C/N₀ = EIRP − FSPL + G/T + 228.6 − "
        "L_misc, with G/T = G − 10·log10(T_sys).  T_sys combines an "
        "elevation-dependent antenna temperature (sky + ground pick-up) with "
        "a 1.5 dB receiver noise figure.  The slant range is computed for a "
        f"{N(nm.H_SAT/1e3, 0)} km LEO.",
        "Das Downlink-C/N₀ folgt aus C/N₀ = EIRP − FSPL + G/T + 228,6 − "
        "L_misc, mit G/T = G − 10·log10(T_sys).  T_sys kombiniert eine "
        "elevationsabhängige Antennentemperatur (Himmel + Bodenaufnahme) mit "
        "1,5 dB Rauschzahl.  Die Schrägentfernung wird für einen "
        f"{N(nm.H_SAT/1e3, 0)} km-LEO berechnet."))
    r.p(T(
        f"With the placeholder EIRP of {N(link['eirp_dbw'], 0)} dBW the link "
        f"closes comfortably: a 2×2 reaches "
        f"{N(a255[2]['cn0_30_db_hz'])} dBHz at n255 and "
        f"{N(a256[2]['cn0_30_db_hz'])} dBHz at n256 at 30° elevation "
        f"(Figure 5).  Even the 85 dBHz broadband-class target is met by 2×2 "
        f"at n255 and by 3×3 at n256.  The packaging size, not the link, is "
        f"therefore the binding constraint – a conclusion that holds as long "
        f"as the real EIRP is not far below the placeholder.",
        f"Mit dem Platzhalter-EIRP von {N(link['eirp_dbw'], 0)} dBW schließt "
        f"der Link komfortabel: Ein 2×2 erreicht bei 30° Elevation "
        f"{N(a255[2]['cn0_30_db_hz'])} dBHz bei n255 und "
        f"{N(a256[2]['cn0_30_db_hz'])} dBHz bei n256 (Bild 5).  Selbst das "
        f"85-dBHz-Broadband-Ziel wird bei n255 von 2×2 und bei n256 von 3×3 "
        f"erreicht.  Damit ist die Packing-Größe und nicht der Link die "
        f"begrenzende Randbedingung – solange das reale EIRP nicht deutlich "
        f"unter dem Platzhalter liegt."))
    r.figure(str(FIG / "fig05_link_elevation.png"),
             T("Downlink C/N₀ over elevation for 2×2, 4×4 and 8×8 at both "
               "bands (placeholder EIRP).",
               "Downlink-C/N₀ über der Elevation für 2×2, 4×4 und 8×8 in "
               "beiden Bändern (Platzhalter-EIRP)."), 16.0)
    r.p(T(
        "Figure 6 inverts the question: it shows the minimum array order "
        "needed at 30° elevation as a function of the satellite EIRP, for the "
        "70 dBHz and 85 dBHz targets.  This is the curve to re-read once the "
        "operator EIRP is known.",
        "Bild 6 kehrt die Frage um: Es zeigt die bei 30° Elevation "
        "mindestens nötige Arrayordnung als Funktion des Satelliten-EIRP, für "
        "die Ziele 70 dBHz und 85 dBHz.  Diese Kurve ist maßgeblich, sobald "
        "das Betreiber-EIRP bekannt ist."))
    r.figure(str(FIG / "fig06_required_n.png"),
             T("Required array order at 30° elevation versus satellite EIRP.",
               "Nötige Arrayordnung bei 30° Elevation über dem "
               "Satelliten-EIRP."), 15.0)

    # ------------------------------------------------------------- 7
    r.h1("7", T("Dual-band and duplex constraints",
                "Dualband- und Duplex-Randbedingungen"))
    r.p(T(
        "Two independent constraints prevent a single shared aperture for "
        "n255 and n256.  First, the frequency ratio is about 1.42, so the "
        "n256 λ/2 cell is far smaller than the n255 patch (Figure 7).  "
        "Second, each band is FDD: together, Tx and Rx span 8.5 % (n255) and "
        "10.5 % (n256) of the band centre, while a single-layer patch "
        "delivers 3–5 % impedance bandwidth.  Even the Tx/Rx pair within one "
        "band therefore needs a broadband (stacked) element or separate "
        "apertures.",
        "Zwei unabhängige Randbedingungen verhindern eine gemeinsame Apertur "
        "für n255 und n256.  Erstens ist das Frequenzverhältnis etwa 1,42, "
        "die n256-Rasterzelle also deutlich kleiner als das n255-Patch "
        "(Bild 7).  Zweitens ist jedes Band FDD: Tx und Rx spannen zusammen "
        "8,5 % (n255) bzw. 10,5 % (n256) der Bandmitte, während ein "
        "einlagiges Patch nur 3–5 % Impedanzbandbreite liefert.  Selbst das "
        "Tx/Rx-Paar eines Bandes benötigt daher ein breitbandiges "
        "(gestapeltes) Element oder getrennte Aperturen."))
    r.figure(str(FIG / "fig07_dualband.png"),
             T("Dual-band conflict: the n255 patch is larger than the n256 "
               "lattice cell.", "Dualband-Konflikt: Das n255-Patch ist größer "
               "als die n256-Rasterzelle."), 13.5)
    r.bullets([
        T("Two separate modules (n255 + n256) are the simplest and most "
          "robust solution.",
          "Zwei getrennte Module (n255 + n256) sind die einfachste und "
          "robusteste Lösung."),
        T("A broadband stacked element can cover Tx+Rx of one band but not "
          "both bands in one lattice.",
          "Ein breitbandiges gestapeltes Element deckt Tx+Rx eines Bandes ab, "
          "aber nicht beide Bänder in einem Raster."),
        T("An interleaved shared aperture is possible in principle but doubles "
          "the feed complexity and the coupling.",
          "Eine verschachtelte gemeinsame Apertur ist prinzipiell möglich, "
          "verdoppelt aber Speisekomplexität und Kopplung."),
    ])

    # ------------------------------------------------------------- 8
    r.h1("8", T("Recommendation", "Empfehlung"))
    r.p(T(
        "For a passenger car the following configuration is the best "
        "compromise between gain, roof area and effort:",
        "Für einen Pkw ist die folgende Konfiguration der beste Kompromiss "
        "aus Gewinn, Dachfläche und Aufwand:"))
    r.bullets([
        T(f"n256: 5×5 array, module {N(a256[5]['module_mm']/10, 0)} cm, "
          f"{N(a256[5]['gain_broad_dbi'], 1)} dBi broadside, "
          f"{N(a256[5]['gain_scan60_dbi'], 1)} dBi at 60° scan – fits the "
          f"40 cm roof centre.  In a 25 cm roof pod only the 2×2 "
          f"({N(a256[2]['module_mm']/10, 0)} cm, "
          f"{N(a256[2]['gain_broad_dbi'], 1)} dBi) fits.",
          f"n256: 5×5-Array, Modul {N(a256[5]['module_mm']/10, 0)} cm, "
          f"{N(a256[5]['gain_broad_dbi'], 1)} dBi Broadside, "
          f"{N(a256[5]['gain_scan60_dbi'], 1)} dBi bei 60°-Scan – passt in "
          f"die 40-cm-Dachmitte.  In ein 25-cm-Dachmodul passt nur das 2×2 "
          f"({N(a256[2]['module_mm']/10, 0)} cm, "
          f"{N(a256[2]['gain_broad_dbi'], 1)} dBi)."),
        T(f"n255: 3×3 array, module {N(a255[3]['module_mm']/10, 0)} cm, "
          f"{N(a255[3]['gain_broad_dbi'], 1)} dBi – the practical roof-centre "
          f"limit.  The 2×2 ({N(a255[2]['module_mm']/10, 0)} cm, "
          f"{N(a255[2]['gain_broad_dbi'], 1)} dBi) needs a pod larger than "
          f"25 cm.",
          f"n255: 3×3-Array, Modul {N(a255[3]['module_mm']/10, 0)} cm, "
          f"{N(a255[3]['gain_broad_dbi'], 1)} dBi – das praktische Limit der "
          f"Dachmitte.  Das 2×2 ({N(a255[2]['module_mm']/10, 0)} cm, "
          f"{N(a255[2]['gain_broad_dbi'], 1)} dBi) braucht ein Modul größer "
          f"als 25 cm."),
        T("If both bands are mandatory, plan two modules side by side rather "
          "than one shared aperture: "
          f"{N(a255[3]['module_mm']/10, 0)} cm (n255) + "
          f"{N(a256[5]['module_mm']/10, 0)} cm (n256).",
          "Wenn beide Bänder zwingend sind, zwei Module nebeneinander planen "
          "statt einer gemeinsamen Apertur: "
          f"{N(a255[3]['module_mm']/10, 0)} cm (n255) + "
          f"{N(a256[5]['module_mm']/10, 0)} cm (n256)."),
        T("A mechanical azimuth rotator plus electronic elevation scan "
          "reduces the aperture needed for the same link margin and is a "
          "valid fallback for a van or truck.",
          "Ein mechanischer Azimutdrehteller plus elektronischer "
          "Elevationsscan reduziert die für dieselbe Link-Reserve nötige "
          "Apertur und ist ein valider Fallback für Van oder Lkw."),
    ])

    # ------------------------------------------------------------- 9
    r.h1("9", T("Limitations and next steps", "Grenzen und nächste Schritte"))
    r.bullets([
        T("The link budget uses a placeholder EIRP; the required-N curve in "
          "Figure 6 must be re-read with operator data.",
          "Das Link-Budget nutzt ein Platzhalter-EIRP; die Kurve in Bild 6 "
          "muss mit Betreiberdaten neu gelesen werden."),
        T("The gain is an aperture estimate; mutual coupling, feed-network "
          "losses and radome losses need a full-wave run.",
          "Der Gewinn ist eine Aperturschätzung; Kopplung, Speisenetz- und "
          "Radomverluste benötigen einen Vollwellenlauf."),
        T("Circular polarisation (RHCP/LHCP) is not modelled; it changes the "
          "element design and adds ~0.5 dB.",
          "Zirkulare Polarisation (RHCP/LHCP) ist nicht modelliert; sie ändert "
          "das Elementdesign und kostet ca. 0,5 dB."),
        T("The vehicle body acts as a large ground plane; a finite-roof model "
          "should quantify pattern and back-lobe changes.",
          "Die Fahrzeugkarosserie wirkt als große Groundplane; ein "
          "endliches-Dach-Modell sollte Diagramm und Rückkeule quantifizieren."),
        T("Next step: full-wave design of the n256 4×4 element→subarray→array "
          "chain in the same openEMS workflow as the 77 GHz study.",
          "Nächster Schritt: Vollwellenentwurf der n256-4×4-Kette "
          "Element→Subarray→Array im gleichen openEMS-Workflow wie die "
          "77-GHz-Studie."),
    ])

    # ------------------------------------------------------------ 10
    r.h1("10", T("Reproduction", "Reproduktion"))
    r.p(T("All results are generated by two scripts:",
          "Alle Ergebnisse entstehen aus zwei Skripten:"))
    r.code("python sizing.py       # figures 01..07 + docs/results.json\n"
           "python build_docs.py   # this report (EN + DE) + PDF")
    r.p(T(
        "sizing.py contains the model chain and writes every number used in "
        "this document to docs/results.json; build_docs.py only formats that "
        "file.  The model constants (bands, platforms, link assumptions) are "
        "in ntn_model.py.",
        "sizing.py enthält die Modellkette und schreibt jede in diesem "
        "Dokument verwendete Zahl nach docs/results.json; build_docs.py "
        "formatiert diese Datei nur.  Die Modellkonstanten (Bänder, "
        "Plattformen, Link-Annahmen) stehen in ntn_model.py."))

    out = DOCS / f"ntn_ue_sizing_{lang}.odt"
    r.save(str(out))
    print(f"wrote {out}")
    pdf = export_pdf(out)
    if pdf:
        print(f"wrote {pdf}")
    return out


def main() -> int:
    build("en")
    build("de")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
