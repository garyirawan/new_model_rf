
import json
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import joblib

@dataclass
class Thresholds:
    # Konfigurasi default (bisa diedit di runtime)
    total_coliform_max_mpn_100ml: float = 0.0   # potabilitas ideal: 0 per 100 mL
    ph_min: float = 6.5
    ph_max: float = 8.5
    conductivity_max_uscm: float = 1500.0       # kira-kira ~TDS 750-1000 mg/L (aproksimasi), ubah sesuai site
    # DO tidak jadi syarat potabilitas baku, tapi indikatif kualitas; biarkan None agar tidak memblok potabilitas
    do_min_info_mgl: float = 5.0                # info label untuk perikanan/biologi

@dataclass
class InferenceOutput:
    used_input: Dict[str, float]
    pred_total_coliform_mpn_100ml: float
    pred_ci90_low: float
    pred_ci90_high: float

@dataclass
class DetectionDecision:
    potable: bool
    reasons: List[str]
    recommendations: List[str]
    alternative_use: List[str]

class RFRegressorWrapper:
    def __init__(self, model_path: str, features_order_path: str):
        import warnings
        warnings.filterwarnings('ignore', category=UserWarning)
        
        self.model = joblib.load(model_path)
        
        with open(features_order_path, "r") as f:
            self.features_order = [line.strip() for line in f if line.strip()]
        # guard
        if not self.features_order:
            raise ValueError("Fitur kosong pada features_order.")

    def _to_feature_array(self, features: Dict[str, Any]) -> np.ndarray:
        vals = []
        for k in self.features_order:
            if k not in features:
                raise KeyError(f"Missing feature '{k}'")
            v = float(features[k])
            vals.append(v)
        return np.array(vals, dtype=np.float32).reshape(1, -1)

    def predict_with_interval(self, features: Dict[str, Any]) -> InferenceOutput:
        X = self._to_feature_array(features)
        # prediksi di skala log1p
        y_log = self.model.predict(X)[0]
        # interval via sebaran antar-tree
        est_preds = np.array([estimator.predict(X)[0] for estimator in self.model.estimators_], dtype=np.float32)
        low_log = np.quantile(est_preds, 0.10)
        high_log = np.quantile(est_preds, 0.90)
        # balik ke skala asli
        y = float(np.expm1(y_log))
        low = float(np.expm1(low_log))
        high = float(np.expm1(high_log))
        return InferenceOutput(used_input={k: float(features[k]) for k in self.features_order},
                               pred_total_coliform_mpn_100ml=y,
                               pred_ci90_low=low,
                               pred_ci90_high=high)

def decide_potability(readings: Dict[str, float],
                      predicted_coliform_mpn_100ml: Optional[float],
                      thresholds: Thresholds = Thresholds()) -> DetectionDecision:
    reasons = []
    recs = []
    alt = []

    # Pilih coliform yang digunakan untuk keputusan: prioritas nilai terukur jika ada
    coliform = readings.get("totalcoliform_mpn_100ml", None)
    col_for_decision = coliform if coliform is not None else predicted_coliform_mpn_100ml

    # --- Aturan potabilitas (konfigurabel) ---
    if col_for_decision is None:
        reasons.append("Tidak ada nilai coliform (terukur/prediksi). Keputusan potabilitas tidak pasti.")
    else:
        if col_for_decision > thresholds.total_coliform_max_mpn_100ml:
            reasons.append(f"Total Coliform {col_for_decision:.1f} > {thresholds.total_coliform_max_mpn_100ml} MPN/100mL")

    ph = readings.get("ph", None)
    if ph is not None and (ph < thresholds.ph_min or ph > thresholds.ph_max):
        reasons.append(f"pH {ph:.2f} di luar [{thresholds.ph_min}, {thresholds.ph_max}]")

    cond = readings.get("conductivity_uscm", None)
    if cond is not None and cond > thresholds.conductivity_max_uscm:
        reasons.append(f"Konduktivitas {cond:.0f} µS/cm > {thresholds.conductivity_max_uscm:.0f} µS/cm (indikasi TDS tinggi)")

    # Keputusan akhir
    potable = len(reasons) == 0

    # --- Rekomendasi tindakan berbasis penyebab ---
    if not potable:
        # mikrob
        if col_for_decision is not None and col_for_decision > thresholds.total_coliform_max_mpn_100ml:
            recs += [
                "Desinfeksi: klorinasi atau UV, verifikasi dosis & kontak waktu",
                "Boiling (pendidihan) untuk konsumsi rumah tangga (solusi sementara)",
                "Telusuri sumber kontaminasi (pipa bocor, intrusi, residu klorin)"
            ]
        # pH
        if ph is not None and ph < thresholds.ph_min:
            recs.append("Naikkan pH: penambahan alkalinitas (kapur/NaHCO₃) atau blending")
        if ph is not None and ph > thresholds.ph_max:
            recs.append("Turunkan pH: injeksi CO₂/asam lemah terkontrol atau blending")
        # konduktivitas
        if cond is not None and cond > thresholds.conductivity_max_uscm:
            recs.append("Kurangi salinitas/TDS: Reverse Osmosis atau ion exchange; pertimbangkan blending")

    # --- Alternative use suggestion (informasi, bukan izin) ---
    # Irigasi (toleran pH/DO, cek salinitas)
    if (ph is None or 6.0 <= ph <= 9.0) and (cond is None or cond < 2000):
        alt.append("Irigasi non-sensitif (cek salinitas tanaman spesifik)")
    # Perikanan (butuh DO memadai & pH moderat & salinitas rendah)
    do = readings.get("do_mgl", None)
    if (do is not None and do >= thresholds.do_min_info_mgl) and (ph is None or 6.5 <= ph <= 8.5) and (cond is None or cond < 1000):
        alt.append("Perikanan (DO ≥ 5 mg/L, pH 6.5–8.5, salinitas rendah)")
    # Proses/utility
    alt.append("Penggunaan proses/utility (cuci/koagulasi) dengan pretreatment sesuai parameter dominan")

    return DetectionDecision(potable=potable, reasons=reasons, recommendations=recs, alternative_use=alt)

def status_badges(readings: Dict[str, float], thresholds: Thresholds = Thresholds()):
    """Status untuk dashboard per-parameter (sederhana, bisa diubah di FE)."""
    badges = {}

    ph = readings.get("ph", None)
    if ph is None:
        badges["ph"] = ("unknown", "–")
    elif thresholds.ph_min <= ph <= thresholds.ph_max:
        badges["ph"] = ("optimal", "Optimal")
    else:
        badges["ph"] = ("warning", "Di luar kisaran")

    do = readings.get("do_mgl", None)
    if do is None:
        badges["do_mgl"] = ("unknown", "–")
    elif do >= thresholds.do_min_info_mgl:
        badges["do_mgl"] = ("good", "Aman (biologi)")
    else:
        badges["do_mgl"] = ("low", "Rendah")

    cond = readings.get("conductivity_uscm", None)
    if cond is None:
        badges["conductivity_uscm"] = ("unknown", "–")
    elif cond <= thresholds.conductivity_max_uscm:
        badges["conductivity_uscm"] = ("normal", "Normal")
    else:
        badges["conductivity_uscm"] = ("high", "Tinggi")

    return badges
