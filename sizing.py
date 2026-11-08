"""Run the automotive NTN UE sizing study and write figures + results.json.

Usage::

    python sizing.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

import ntn_model as nm

HERE = Path(__file__).resolve().parent
FIG = HERE / "docs" / "figures"
DOCS = HERE / "docs"

C_BLUE = "#1f5fa8"
C_ORANGE = "#e67e22"
C_RED = "#c0392b"
C_GREEN = "#27ae60"
C_GRAY = "#7f8c8d"
C_GOLD = "#b8860b"
C_SUB = "#cfe0f2"


def hline_text(ax, y, text, color=C_GRAY, ls=":"):
    ax.axhline(y, color=color, lw=1.0, ls=ls)
    ax.text(ax.get_xlim()[1], y, f" {text}", color=color, fontsize=8,
            va="bottom", ha="right")


# ---------------------------------------------------------------------------
# fig 01 - element and lattice geometry, to scale
# ---------------------------------------------------------------------------

def fig_geometry(bands) -> dict:
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.4), dpi=150)
    out = {}
    for ax, b in zip(axes, bands):
        p = nm.patch_dims(b)
        d = b.lattice_mm
        # lattice cell
        ax.add_patch(Rectangle((-d / 2, -d / 2), d, d, fill=False,
                               edgecolor=C_GRAY, lw=1.0, ls="--"))
        ax.add_patch(Rectangle((-p["l_mm"] / 2, -p["w_mm"] / 2),
                               p["l_mm"], p["w_mm"], facecolor=C_GOLD,
                               edgecolor="#5a3a08", lw=1.0))
        ax.annotate("", xy=(-p["l_mm"] / 2, p["w_mm"] / 2 + 6),
                    xytext=(p["l_mm"] / 2, p["w_mm"] / 2 + 6),
                    arrowprops=dict(arrowstyle="<->", lw=0.9))
        ax.text(0, p["w_mm"] / 2 + 8, f"L = {p['l_mm']:.1f} mm",
                ha="center", fontsize=8.5)
        ax.annotate("", xy=(p["l_mm"] / 2 + 7, -p["w_mm"] / 2),
                    xytext=(p["l_mm"] / 2 + 7, p["w_mm"] / 2),
                    arrowprops=dict(arrowstyle="<->", lw=0.9))
        ax.text(p["l_mm"] / 2 + 10, 0, f"W = {p['w_mm']:.1f} mm",
                rotation=90, va="center", fontsize=8.5)
        ax.text(0, -d / 2 - 9, f"lattice d = λ₀/2 = {d:.1f} mm",
                ha="center", fontsize=8.5, color=C_GRAY)
        ax.set_xlim(-max(d, 80) * 0.75, max(d, 80) * 0.75)
        ax.set_ylim(-d * 0.85, d * 0.85)
        ax.set_aspect("equal")
        ax.set_xlabel("x (mm)")
        ax.set_ylabel("y (mm)")
        ax.set_title(f"{b.label}: λ₀ = {b.lam_mm:.0f} mm, "
                     f"h = {b.h_mm:.2f} mm", fontsize=10)
        ax.grid(True, alpha=0.3)
        out[b.key] = {"l_mm": p["l_mm"], "w_mm": p["w_mm"],
                      "lattice_mm": d, "lam_mm": b.lam_mm,
                      "eps_eff": p["eps_eff"]}

    fig.suptitle("Element and lattice geometry (to scale)", fontsize=11)
    fig.tight_layout()
    path = FIG / "fig01_geometry.png"
    fig.savefig(path)
    plt.close(fig)
    print(f"wrote {path}")
    return out


# ---------------------------------------------------------------------------
# fig 02 - module footprints vs vehicle platforms
# ---------------------------------------------------------------------------

def fig_footprints(bands, arrays) -> None:
    fig, ax = plt.subplots(figsize=(9.0, 4.6), dpi=150)
    n_orders = [a["n"] for a in arrays[bands[0].key]]
    x = np.arange(len(n_orders))
    w = 0.38
    for k, (b, col) in enumerate(zip(bands, (C_BLUE, C_ORANGE))):
        sizes = [a["module_mm"] / 10.0 for a in arrays[b.key]]
        ax.bar(x + (k - 0.5) * w, sizes, w, color=col, label=b.label)
    for name, width_m, depth_m in nm.PLATFORMS:
        h = max(width_m, depth_m) * 100.0
        ax.axhline(h, color=C_GRAY, lw=0.9, ls="--")
        ax.text(len(n_orders) - 0.5, h + 0.6, f"{name} ({width_m*100:.0f} cm)",
                fontsize=7.5, color=C_GRAY, ha="right")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{n}×{n}" for n in n_orders])
    ax.set_xlabel("array order")
    ax.set_ylabel("module edge length (cm)")
    ax.set_ylim(0, 90)
    ax.set_title("Array footprint versus available vehicle areas "
                 "(module = aperture + 2 x 0.2 λ₀)")
    ax.grid(True, axis="y", alpha=0.4)
    ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    path = FIG / "fig02_footprints.png"
    fig.savefig(path)
    plt.close(fig)
    print(f"wrote {path}")


# ---------------------------------------------------------------------------
# fig 03 - gain versus array order
# ---------------------------------------------------------------------------

def fig_gain_vs_n(bands, arrays) -> None:
    """Gain versus module edge length (the band-independent gain vs N curve
    would be degenerate, so the packaging axis is used)."""
    fig, ax = plt.subplots(figsize=(8.6, 4.8), dpi=150)
    for b, col, mk in zip(bands, (C_BLUE, C_ORANGE), ("o", "s")):
        size = [a["module_mm"] / 10.0 for a in arrays[b.key]]
        g0 = [a["gain_broad_dbi"] for a in arrays[b.key]]
        g60 = [a["gain_broad_dbi"] + nm.scan_loss_db(60.0)
               for a in arrays[b.key]]
        ax.plot(size, g0, marker=mk, color=col, lw=1.8,
                label=f"{b.label}, broadside")
        ax.plot(size, g60, marker=mk, color=col, lw=1.2, ls="--", alpha=0.75,
                label=f"{b.label}, 60° scan")
        for a in arrays[b.key]:
            ax.annotate(f"{a['n']}×{a['n']}",
                        (a["module_mm"] / 10.0, a["gain_broad_dbi"]),
                        xytext=(4, -10), textcoords="offset points",
                        fontsize=7, color=col)
    for name, w, d in nm.PLATFORMS:
        x = max(w, d) * 100.0
        ax.axvline(x, color=C_GRAY, lw=0.8, ls=":")
        ax.text(x + 0.8, ax.get_ylim()[1] if ax.get_ylim()[1] else 22.0,
                name, rotation=90, fontsize=7, color=C_GRAY, va="top")
    ax.set_xlabel("module edge length (cm)")
    ax.set_ylabel("realised gain (dBi)")
    ax.set_title("Gain versus roof area: the same gain needs a smaller module "
                 "at n256")
    ax.grid(True, alpha=0.4)
    ax.legend(fontsize=7.5, ncol=2)
    fig.tight_layout()
    path = FIG / "fig03_gain_vs_size.png"
    fig.savefig(path)
    plt.close(fig)
    print(f"wrote {path}")


# ---------------------------------------------------------------------------
# fig 04 - scan loss
# ---------------------------------------------------------------------------

def fig_scan_loss() -> dict:
    th = np.linspace(0, 70, 141)
    ap = np.array([nm.scan_loss_db(t, 0.0) for t in th])
    tot = np.array([nm.scan_loss_db(t, 0.5) for t in th])
    fig, ax = plt.subplots(figsize=(7.4, 4.2), dpi=150)
    ax.plot(th, ap, color=C_BLUE, lw=1.8, label="aperture projection only")
    ax.plot(th, tot, color=C_RED, lw=1.8,
            label="aperture + patch roll-off (model)")
    for t in (30, 45, 60):
        ax.axvline(t, color=C_GRAY, lw=0.7, ls=":")
        ax.text(t + 0.7, ax.get_ylim()[0] if ax.get_ylim()[0] else -6,
                f"{t}°", color=C_GRAY, fontsize=8, va="bottom")
    ax.set_xlabel("scan angle θ₀ (deg)")
    ax.set_ylabel("scan loss (dB)")
    ax.set_title("Scan loss used in the sizing model")
    ax.grid(True, alpha=0.4)
    ax.legend(fontsize=8)
    fig.tight_layout()
    path = FIG / "fig04_scan_loss.png"
    fig.savefig(path)
    plt.close(fig)
    print(f"wrote {path}")
    return {"scan_loss_60_deg_db": float(nm.scan_loss_db(60.0)),
            "scan_loss_45_deg_db": float(nm.scan_loss_db(45.0))}


# ---------------------------------------------------------------------------
# fig 05 - link budget versus elevation
# ---------------------------------------------------------------------------

def fig_link(bands, arrays) -> dict:
    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.5), dpi=150, sharey=True)
    elev = np.linspace(15, 90, 76)
    out = {}
    for ax, b in zip(axes, bands):
        for a in arrays[b.key]:
            if a["n"] not in (2, 4, 8):
                continue
            cn0 = [nm.cn0_db_hz(nm.LINK["eirp_dbw"], a["gain_broad_dbi"], b, e,
                                nm.LINK["misc_loss_db"], nm.LINK["nf_db"])
                   for e in elev]
            ax.plot(elev, cn0, lw=1.8,
                    label=f"{a['n']}×{a['n']} ({a['gain_broad_dbi']:.0f} dBi)")
            out[f"{b.key}_n{a['n']}_cn0_30"] = float(
                nm.cn0_db_hz(nm.LINK["eirp_dbw"], a["gain_broad_dbi"], b, 30.0,
                             nm.LINK["misc_loss_db"], nm.LINK["nf_db"]))
        ax.axhline(nm.LINK["targets_db_hz"]["NB-NTN low rate"], color=C_GRAY,
                   lw=1.0, ls=":")
        ax.text(89, nm.LINK["targets_db_hz"]["NB-NTN low rate"] + 0.8,
                "NB-NTN 55 dBHz", color=C_GRAY, fontsize=7.5, ha="right")
        ax.axhline(nm.LINK["targets_db_hz"]["broadband class"], color=C_RED,
                   lw=1.0, ls="--")
        ax.text(89, nm.LINK["targets_db_hz"]["broadband class"] + 0.8,
                "broadband 85 dBHz", color=C_RED, fontsize=7.5, ha="right")
        ax.set_xlabel("elevation (deg)")
        ax.set_title(f"{b.label}, EIRP {nm.LINK['eirp_dbw']:.0f} dBW",
                     fontsize=10)
        ax.grid(True, alpha=0.4)
        ax.legend(fontsize=8, title="array", title_fontsize=8)
    axes[0].set_ylabel("C/N₀ (dBHz)")
    fig.suptitle("Downlink C/N₀ over elevation for a 630 km LEO "
                 "(assumed EIRP)", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    path = FIG / "fig05_link_elevation.png"
    fig.savefig(path)
    plt.close(fig)
    print(f"wrote {path}")
    return out


# ---------------------------------------------------------------------------
# fig 06 - required array size versus satellite EIRP
# ---------------------------------------------------------------------------

def fig_required_n(bands, arrays) -> dict:
    eirp = np.arange(20, 51, 1.0)
    fig, ax = plt.subplots(figsize=(8.2, 4.6), dpi=150)
    need = {}
    for b, col in zip(bands, (C_BLUE, C_ORANGE)):
        for tgt, ls in ((nm.LINK["target_cn0_db_hz"], "-"),
                        (nm.LINK["targets_db_hz"]["broadband class"], "--")):
            nneed = []
            for e_dbw in eirp:
                ok = None
                for a in arrays[b.key]:
                    cn0 = nm.cn0_db_hz(e_dbw, a["gain_broad_dbi"], b, 30.0,
                                       nm.LINK["misc_loss_db"],
                                       nm.LINK["nf_db"])
                    if cn0 >= tgt:
                        ok = a["n"]
                        break
                nneed.append(ok if ok is not None else np.nan)
            ax.step(eirp, nneed, where="post", color=col, lw=1.8, ls=ls,
                    label=f"{b.label}, {tgt:.0f} dBHz")
            need[f"{b.key}_{int(tgt)}"] = [
                None if (isinstance(v, float) and np.isnan(v)) else v
                for v in nneed]
    ax.axvline(nm.LINK["eirp_dbw"], color=C_GRAY, lw=0.9, ls=":")
    ax.text(nm.LINK["eirp_dbw"] + 0.5, ax.get_ylim()[1] - 0.4,
            "assumed EIRP", color=C_GRAY, fontsize=8, va="top")
    ax.set_xlabel("satellite EIRP per beam (dBW)")
    ax.set_ylabel("minimum array order N")
    ax.set_title("Array size needed at 30° elevation "
                 "(solid: 70 dBHz, dashed: 85 dBHz)")
    ax.set_yticks([2, 3, 4, 5, 6, 8])
    ax.grid(True, alpha=0.4)
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    path = FIG / "fig06_required_n.png"
    fig.savefig(path)
    plt.close(fig)
    print(f"wrote {path}")
    return need


# ---------------------------------------------------------------------------
# fig 07 - dual-band conflict
# ---------------------------------------------------------------------------

def fig_dualband(bands, geom) -> dict:
    b16, b27 = bands
    p16 = geom[b16.key]
    cell27 = geom[b27.key]["lattice_mm"]
    fig, ax = plt.subplots(figsize=(7.6, 4.0), dpi=150)
    ax.barh([1], [p16["l_mm"]], color=C_GOLD, edgecolor="#5a3a08",
            height=0.4, label="n255 patch length L")
    ax.barh([0.4], [p16["w_mm"]], color="#d9b44a", edgecolor="#5a3a08",
            height=0.4, label="n255 patch width W")
    ax.axvline(cell27, color=C_RED, lw=2.0, ls="--")
    ax.text(cell27 + 1, 1.45, f"n256 lattice d = {cell27:.1f} mm",
            color=C_RED, fontsize=8.5, rotation=90, va="top")
    ax.set_yticks([1, 0.4])
    ax.set_yticklabels(["L", "W"])
    ax.set_xlabel("dimension (mm)")
    ax.set_xlim(0, max(p16["w_mm"], cell27) * 1.35)
    ax.set_title("Dual-band conflict: the n255 patch does not fit the "
                 "n256 lattice")
    ax.grid(True, axis="x", alpha=0.4)
    ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    path = FIG / "fig07_dualband.png"
    fig.savefig(path)
    plt.close(fig)
    print(f"wrote {path}")
    return {"patch16_l_mm": p16["l_mm"], "patch16_w_mm": p16["w_mm"],
            "cell27_mm": cell27,
            "ratio_w_to_cell": p16["w_mm"] / cell27}


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    FIG.mkdir(parents=True, exist_ok=True)
    bands = nm.BANDS

    geom = fig_geometry(bands)

    arrays = {}
    rows = []
    for b in bands:
        arrays[b.key] = []
        for n in nm.ORDERS:
            a = nm.array_metrics(b, n)
            a["gain_scan60_dbi"] = a["gain_broad_dbi"] + nm.scan_loss_db(60.0)
            a["cn0_30_db_hz"] = nm.cn0_db_hz(
                nm.LINK["eirp_dbw"], a["gain_broad_dbi"], b, 30.0,
                nm.LINK["misc_loss_db"], nm.LINK["nf_db"])
            a["cn0_90_db_hz"] = nm.cn0_db_hz(
                nm.LINK["eirp_dbw"], a["gain_broad_dbi"], b, 90.0,
                nm.LINK["misc_loss_db"], nm.LINK["nf_db"])
            a["fit"] = [name for name, w, hgt in nm.PLATFORMS
                        if a["module_mm"] / 1000.0 <= w
                        and a["module_mm"] / 1000.0 <= hgt]
            arrays[b.key].append(a)
            rows.append((b.label, n, a))

    fig_footprints(bands, arrays)
    fig_gain_vs_n(bands, arrays)
    scan = fig_scan_loss()
    link = fig_link(bands, arrays)
    need = fig_required_n(bands, arrays)
    dual = fig_dualband(bands, geom)

    # recommended configuration: largest array that fits a roof pod (25 cm)
    rec = {}
    for b in bands:
        cands = [a for a in arrays[b.key]
                 if a["module_mm"] / 1000.0 <= 0.25]
        best = max(cands, key=lambda a: a["n"]) if cands else None
        rec[b.key] = None if best is None else {
            "n": best["n"], "module_mm": best["module_mm"],
            "gain_dbi": best["gain_broad_dbi"],
            "cn0_30": best["cn0_30_db_hz"]}

    results = {
        "study": {
            "title": "Automotive NTN UE sizing study, 1.6 GHz and 2.7 GHz",
            "substrate": nm.SUBSTRATE,
            "satellite_altitude_km": nm.H_SAT / 1e3,
        },
        "bands": {
            b.key: {"label": b.label, "f_ghz": b.f_ghz,
                    "lam_mm": b.lam_mm, "lattice_mm": b.lattice_mm,
                    "h_mm": b.h_mm, "eps_r": b.eps_r, "tan_d": b.tan_d,
                    "bw_mhz": b.bw_mhz}
            for b in bands
        },
        "patch": geom,
        "arrays": {k: v for k, v in arrays.items()},
        "platforms": [{"name": n, "w_m": w, "d_m": d}
                      for n, w, d in nm.PLATFORMS],
        "link": dict(nm.LINK),
        "scan": scan,
        "link_results": link,
        "required_n": need,
        "dualband": dual,
        "recommendation_roof_pod": rec,
    }

    out = DOCS / "results.json"
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(f"wrote {out}")

    print("\narray table")
    print("band            N  elements  aperture  module   D_ap    G    G@60  C/N0@30")
    for label, n, a in rows:
        print(f"{label:14s} {n:2d} {a['elements']:8d} "
              f"{a['aperture_mm']/10:7.1f}cm {a['module_mm']/10:6.1f}cm "
              f"{a['d_dbi']:6.1f} {a['gain_broad_dbi']:5.1f} "
              f"{a['gain_scan60_dbi']:5.1f} {a['cn0_30_db_hz']:7.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
