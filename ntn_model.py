"""Model parameters and closed-form sizing relations for an automotive NTN UE.

The study answers one question: how large does a patch array become at 1.6 GHz
and 2.7 GHz, and is that size realistic on a vehicle?

Everything is analytic (no full-wave run).  The relations are:

* rectangular microstrip patch (Hammerstad)
* lambda/2 lattice, aperture directivity D = 4*pi*A/lambda^2
* scan loss from aperture projection plus element roll-off
* free-space path loss, G/T, C/N0 for a LEO downlink

Units: SI unless a name says otherwise (mm, GHz, dB, dBi).
"""

from __future__ import annotations

import math

C0 = 299_792_458.0
R_EARTH = 6_371_000.0
H_SAT = 630_000.0          # Amazon Leo upper shell (m)
K_BOLTZ_DBW = 228.6        # 10*log10(k) in dBW/K/Hz


# ---------------------------------------------------------------------------
# bands and substrates
# ---------------------------------------------------------------------------

class Band:
    """One NTN band; the array is sized for the downlink (UE receive)."""

    def __init__(self, key: str, label: str, f_lo_mhz: float, f_hi_mhz: float,
                 h_mm: float, eps_r: float = 3.55, tan_d: float = 0.0027,
                 ul_lo_mhz: float | None = None,
                 ul_hi_mhz: float | None = None):
        self.key = key
        self.label = label
        self.f_lo_mhz = f_lo_mhz
        self.f_hi_mhz = f_hi_mhz
        self.f0_mhz = 0.5 * (f_lo_mhz + f_hi_mhz)
        self.f_hz = self.f0_mhz * 1e6
        self.f_ghz = self.f0_mhz / 1000.0
        self.h_mm = h_mm
        self.eps_r = eps_r
        self.tan_d = tan_d
        self.bw_mhz = f_hi_mhz - f_lo_mhz
        self.ul_lo_mhz = ul_lo_mhz
        self.ul_hi_mhz = ul_hi_mhz

    @property
    def lam_mm(self) -> float:
        return C0 / self.f_hz * 1e3

    @property
    def lam_hi_mm(self) -> float:
        """Wavelength at the upper band edge (governs grating lobes)."""
        return C0 / (self.f_hi_mhz * 1e6) * 1e3

    @property
    def lattice_mm(self) -> float:
        """lambda/2 lattice at the highest frequency of the band."""
        return self.lam_hi_mm / 2.0

    @property
    def duplex_mhz(self) -> float | None:
        if self.ul_lo_mhz is None:
            return None
        return self.ul_lo_mhz - self.f_hi_mhz


BANDS = [
    Band("n255", "n255 L-band (Rx 1525-1559 MHz)", 1525, 1559, h_mm=3.048,
         ul_lo_mhz=1626.5, ul_hi_mhz=1660.5),
    Band("n256", "n256 S-band (Rx 2170-2200 MHz)", 2170, 2200, h_mm=1.524,
         ul_lo_mhz=1980.0, ul_hi_mhz=2010.0),
]

#: substrate used for both bands (low-loss PTFE/ceramic laminate)
SUBSTRATE = "Rogers RO4003C (eps_r 3.55, tan_d 0.0027)"

#: array orders considered in the study
ORDERS = [2, 3, 4, 5, 6, 8]

#: available installation areas on a vehicle (width, depth) in metres
PLATFORMS = [
    ("Shark fin", 0.15, 0.10),
    ("Roof pod", 0.25, 0.25),
    ("Car roof, centre", 0.40, 0.40),
    ("Van roof", 0.60, 0.40),
]


# ---------------------------------------------------------------------------
# patch element
# ---------------------------------------------------------------------------

def patch_dims(band: Band) -> dict:
    """Hammerstad rectangular patch (width chosen for good radiation)."""
    f0 = band.f_hz
    eps_r = band.eps_r
    h = band.h_mm * 1e-3

    w = C0 / (2.0 * f0) * math.sqrt(2.0 / (eps_r + 1.0))
    eps_eff = ((eps_r + 1.0) / 2.0
               + (eps_r - 1.0) / 2.0 * (1.0 + 12.0 * h / w) ** -0.5)
    dl = (0.412 * h
          * (eps_eff + 0.3) * (w / h + 0.264)
          / ((eps_eff - 0.258) * (w / h + 0.8)))
    length = C0 / (2.0 * f0 * math.sqrt(eps_eff)) - 2.0 * dl

    return {
        "w_mm": w * 1e3,
        "l_mm": length * 1e3,
        "h_mm": band.h_mm,
        "eps_eff": eps_eff,
        "q_rad": None,
    }


# ---------------------------------------------------------------------------
# array metrics
# ---------------------------------------------------------------------------

def array_metrics(band: Band, n: int, margin_lambda: float = 0.20,
                  feed_loss_db: float = 1.5) -> dict:
    """Aperture, footprint, directivity and broadside gain of an n x n array."""
    d = band.lattice_mm
    aperture_mm = n * d
    margin_mm = margin_lambda * band.lam_mm
    module_mm = aperture_mm + 2.0 * margin_mm

    area = (aperture_mm * 1e-3) ** 2
    lam = band.lam_mm * 1e-3
    d_ap = 4.0 * math.pi * area / lam ** 2
    d_dbi = 10.0 * math.log10(d_ap)

    return {
        "n": n,
        "elements": n * n,
        "lattice_mm": d,
        "aperture_mm": aperture_mm,
        "module_mm": module_mm,
        "area_m2": area,
        "d_dbi": d_dbi,
        "gain_broad_dbi": d_dbi - feed_loss_db,
    }


def scan_loss_db(theta_deg: float, element_exp: float = 0.5) -> float:
    """Aperture projection plus a simple element roll-off.

    ``element_exp`` = 0 gives the pure aperture projection (10*log10(cos)),
    0.5 adds a patch-like roll-off (5*log10(cos)).
    """
    c = max(math.cos(math.radians(theta_deg)), 1e-3)
    return (10.0 + 10.0 * element_exp) * math.log10(c)


# ---------------------------------------------------------------------------
# link budget (LEO downlink)
# ---------------------------------------------------------------------------

def slant_range_m(elev_deg: float, h_sat: float = H_SAT) -> float:
    e = math.radians(elev_deg)
    r = R_EARTH
    return math.sqrt((r + h_sat) ** 2 - (r * math.cos(e)) ** 2) - r * math.sin(e)


def fspl_db(f_hz: float, d_m: float) -> float:
    return 20.0 * math.log10(4.0 * math.pi * d_m * f_hz / C0)


def antenna_temp_k(elev_deg: float) -> float:
    """Sky + ground pick-up, elevation dependent (assumption)."""
    s = math.sin(math.radians(max(elev_deg, 5.0)))
    return 50.0 + 150.0 * (1.0 - s)


def system_temp_k(elev_deg: float, nf_db: float = 1.5) -> float:
    return antenna_temp_k(elev_deg) + 290.0 * (10.0 ** (nf_db / 10.0) - 1.0)


def g_over_t(gain_dbi: float, elev_deg: float, nf_db: float = 1.5) -> float:
    return gain_dbi - 10.0 * math.log10(system_temp_k(elev_deg, nf_db))


def cn0_db_hz(eirp_dbw: float, gain_dbi: float, band: Band,
              elev_deg: float, misc_loss_db: float = 1.0,
              nf_db: float = 1.5) -> float:
    d = slant_range_m(elev_deg)
    return (eirp_dbw + gain_dbi - fspl_db(band.f_hz, d) - misc_loss_db
            + K_BOLTZ_DBW - 10.0 * math.log10(system_temp_k(elev_deg, nf_db)))


# ---------------------------------------------------------------------------
# link assumptions (placeholders, to be replaced by operator data)
# ---------------------------------------------------------------------------

LINK = {
    "eirp_dbw": 30.0,          # satellite EIRP per beam (assumption)
    "misc_loss_db": 1.0,       # polarisation, atmosphere, pointing
    "nf_db": 1.5,              # UE receiver noise figure
    "target_cn0_db_hz": 70.0,  # primary design target (assumption)
    "targets_db_hz": {"NB-NTN low rate": 55.0,
                      "moderate rate": 70.0,
                      "broadband class": 85.0},
    "elevations_deg": [90.0, 60.0, 45.0, 30.0, 20.0],
}
