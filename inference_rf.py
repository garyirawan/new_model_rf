
import json
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import joblib

@dataclass
class Thresholds:
    # === TOTAL COLIFORM (3 Tingkat) ===
    # Aman: ≤0.70 | Waspada: 0.71-0.99 | Bahaya: ≥1.0
    total_coliform_safe_mpn_100ml: float = 0.70      # Batas atas AMAN (≤0.70)
    total_coliform_danger_mpn_100ml: float = 1.0     # Batas bawah BAHAYA (≥1.0)
    # WASPADA = antara 0.70 dan 1.0 (0.71-0.99)
    
    # === SUHU (3 Tingkat) ===
    # Aman: 10-35°C | Waspada: 36-44°C (zona E. coli) | Aman tapi panas: ≥45°C
    temp_safe_min_c: float = 10.0                     # Suhu minimum aman
    temp_safe_max_c: float = 35.0                     # Suhu maksimum aman (nyaman)
    temp_warning_min_c: float = 36.0                  # Zona waspada mulai (E. coli optimal)
    temp_warning_max_c: float = 44.0                  # Zona waspada akhir
    temp_hot_safe_c: float = 45.0                     # Suhu panas tapi E. coli mati
    
    # === pH (Permenkes 2023) ===
    ph_min: float = 6.5
    ph_max: float = 8.5
    
    # === KONDUKTIVITAS (EPA Amerika) ===
    conductivity_max_uscm: float = 1000.0             # Optimal <1000 µS/cm
    
    # === DO (3 Tingkat) ===
    # Aman: ≥6 mg/L | Rendah: 5-6 mg/L | Waspada: <5 mg/L
    do_optimal_mgl: float = 6.0                       # Optimal untuk konsumsi
    do_low_mgl: float = 5.0                           # Di bawah ini = waspada
    # do < 5.0 = Waspada, kurang layak konsumsi

@dataclass
class InferenceOutput:
    used_input: Dict[str, float]
    pred_total_coliform_mpn_100ml: float
    pred_ci90_low: float
    pred_ci90_high: float

@dataclass
class DetectionDecision:
    potable: bool
    severity: str
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

    # PENTING: Prioritas keputusan potabilitas
    # 1. Jika SENSOR Total Coliform ada nilai terukur (> 0) → PRIORITAS SENSOR
    # 2. Jika sensor = 0 atau None → Pakai PREDIKSI AI
    # Alasan: Jika sensor mendeteksi coliform aktual, itu data real-time yang harus diprioritaskan
    sensor_coliform = readings.get("totalcoliform_mpn_100ml", None)
    
    if sensor_coliform is not None and sensor_coliform > 0:
        # SENSOR ADA NILAI TERUKUR → Pakai sensor (data real)
        col_for_decision = sensor_coliform
    else:
        # SENSOR 0 atau None → Pakai PREDIKSI AI (lebih reliable dari sensor mV)
        col_for_decision = predicted_coliform_mpn_100ml

    # --- Aturan potabilitas dengan sistem 3 tingkatan ---
    
    # 1. Total Coliform (3 Tingkat: Aman ≤0.70 | Waspada 0.71-0.99 | Bahaya ≥1.0)
    if col_for_decision is None:
        reasons.append("Tidak ada nilai coliform (terukur/prediksi). Keputusan potabilitas tidak pasti.")
    else:
        if col_for_decision >= thresholds.total_coliform_danger_mpn_100ml:
            # BAHAYA: ≥1.0 MPN/100mL
            reasons.append(f"Total Coliform {col_for_decision:.2f} MPN/100mL - BAHAYA (≥1.0), tidak boleh dikonsumsi")
        elif col_for_decision > thresholds.total_coliform_safe_mpn_100ml:
            # WASPADA: 0.71-0.99 MPN/100mL
            reasons.append(f"Total Coliform {col_for_decision:.2f} MPN/100mL - WASPADA (0.71-0.99), perlu treatment sebelum konsumsi")
        # AMAN: ≤0.70 (tidak masuk reasons)

    # 2. Suhu (3 Tingkat: Aman 10-35°C | Waspada 36-44°C | Aman tapi panas ≥45°C)
    temp = readings.get("temp_c", None)
    if temp is not None:
        if temp < thresholds.temp_safe_min_c:
            reasons.append(f"Suhu {temp:.1f}°C terlalu rendah (< {thresholds.temp_safe_min_c:.0f}°C)")
        elif thresholds.temp_warning_min_c <= temp <= thresholds.temp_warning_max_c:
            # WASPADA: 36-44°C (zona E. coli)
            reasons.append(f"Suhu {temp:.1f}°C - WASPADA zona pertumbuhan E. coli ({thresholds.temp_warning_min_c:.0f}-{thresholds.temp_warning_max_c:.0f}°C)")
        elif temp >= thresholds.temp_hot_safe_c:
            # Aman dari bakteri tapi panas
            reasons.append(f"Suhu {temp:.1f}°C - Aman dari bakteri (E. coli mati di ≥{thresholds.temp_hot_safe_c:.0f}°C) tapi terlalu panas untuk konsumsi langsung")
        elif temp > thresholds.temp_safe_max_c and temp < thresholds.temp_warning_min_c:
            # 35-36°C: transisi nyaman ke waspada
            reasons.append(f"Suhu {temp:.1f}°C sedikit tinggi (optimal {thresholds.temp_safe_min_c:.0f}-{thresholds.temp_safe_max_c:.0f}°C)")

    # 3. pH (Permenkes 2023)
    ph = readings.get("ph", None)
    if ph is not None and (ph < thresholds.ph_min or ph > thresholds.ph_max):
        reasons.append(f"pH {ph:.2f} di luar kisaran aman [{thresholds.ph_min}-{thresholds.ph_max}] (Permenkes 2023)")

    # 4. Konduktivitas (EPA Amerika)
    cond = readings.get("conductivity_uscm", None)
    if cond is not None and cond > thresholds.conductivity_max_uscm:
        reasons.append(f"Konduktivitas {cond:.0f} µS/cm > {thresholds.conductivity_max_uscm:.0f} µS/cm (EPA Amerika)")

    # 5. Dissolved Oxygen (3 Tingkat: Aman ≥6 | Rendah 5-6 | Waspada <5)
    do = readings.get("do_mgl", None)
    if do is not None:
        if do < thresholds.do_low_mgl:
            # WASPADA: <5 mg/L
            reasons.append(f"DO {do:.1f} mg/L - BAHAYA (< {thresholds.do_low_mgl:.0f} mg/L), kurang layak untuk dikonsumsi")
        elif do < thresholds.do_optimal_mgl:
            # RENDAH: 5-6 mg/L
            reasons.append(f"DO {do:.1f} mg/L - Rendah (< {thresholds.do_optimal_mgl:.0f} mg/L), di bawah optimal")

    # Keputusan akhir
    potable = len(reasons) == 0

    # --- Rekomendasi tindakan berbasis penyebab ---
    if not potable:
        # Total Coliform
        if col_for_decision is not None:
            if col_for_decision >= thresholds.total_coliform_danger_mpn_100ml:
                # BAHAYA: ≥1.0
                recs += [
                    "TIDAK BOLEH DIKONSUMSI - Total Coliform ≥1.0 MPN/100mL",
                    "Desinfeksi wajib: klorinasi, UV, atau ozonisasi",
                    "Boiling (pendidihan 100°C minimum 1 menit) jika darurat",
                    "Telusuri sumber kontaminasi (sanitasi, pipa bocor, intrusi)"
                ]
            elif col_for_decision > thresholds.total_coliform_safe_mpn_100ml:
                # WASPADA: 0.71-0.99
                recs += [
                    "PERLU TREATMENT - Total Coliform 0.71-0.99 MPN/100mL",
                    "Boiling (pendidihan 100°C) sebelum konsumsi",
                    "Atau gunakan filter bersertifikat NSF untuk bakteri",
                    "Monitor kualitas air secara berkala"
                ]
        
        # Suhu
        if temp is not None:
            if temp < thresholds.temp_safe_min_c:
                recs.append(f"Suhu terlalu rendah ({temp:.1f}°C): biarkan mencapai suhu ruang sebelum konsumsi")
            elif thresholds.temp_warning_min_c <= temp <= thresholds.temp_warning_max_c:
                # WASPADA: 36-44°C
                recs.append(f"ZONA BAHAYA ({temp:.1f}°C): Dinginkan segera ke <35°C atau panaskan ke >45°C untuk membunuh E. coli")
            elif temp >= thresholds.temp_hot_safe_c:
                recs.append(f"Air terlalu panas ({temp:.1f}°C): Dinginkan ke 10-35°C sebelum konsumsi (bakteri sudah mati)")
        
        # pH
        if ph is not None:
            if ph < thresholds.ph_min:
                recs.append("pH terlalu rendah: penambahan alkalinitas (kapur/NaHCO₃) atau blending dengan air pH lebih tinggi")
            if ph > thresholds.ph_max:
                recs.append("pH terlalu tinggi: injeksi CO₂/asam lemah terkontrol atau blending dengan air pH lebih rendah")
        
        # Konduktivitas
        if cond is not None and cond > thresholds.conductivity_max_uscm:
            recs.append(f"Konduktivitas tinggi ({cond:.0f} µS/cm): Reverse Osmosis atau blending untuk menurunkan TDS")
        
        # Dissolved Oxygen
        if do is not None:
            if do < thresholds.do_low_mgl:
                # WASPADA: <5
                recs.append(f"DO sangat rendah ({do:.1f} mg/L): Aerasi intensif atau oksigenasi untuk meningkatkan ke >6 mg/L")
            elif do < thresholds.do_optimal_mgl:
                # RENDAH: 5-6
                recs.append(f"DO rendah ({do:.1f} mg/L): Aerasi ringan untuk meningkatkan ke ≥6 mg/L")

    # --- Tentukan severity level berdasarkan SEMUA PARAMETER ---
    severity = "safe"  # Default: aman
    
    if not potable:
        # PRIORITAS 1: Cek Total Coliform (PREDIKSI AI) - paling kritis
        coliform_severity = None
        if col_for_decision is not None:
            if col_for_decision >= thresholds.total_coliform_danger_mpn_100ml:
                coliform_severity = "danger"  # ≥1.0 MPN/100mL
            elif col_for_decision > thresholds.total_coliform_safe_mpn_100ml:
                coliform_severity = "warning"  # 0.71-0.99 MPN/100mL
        
        # PRIORITAS 2: Cek DO (parameter kedua paling kritis)
        do_severity = None
        if do is not None and do < thresholds.do_low_mgl:
            do_severity = "danger"  # DO <5 mg/L = bahaya
        
        # PRIORITAS 3: Cek parameter lain (temp, pH, conductivity)
        other_severity = None
        # Suhu zona E. coli = warning
        if temp is not None and (thresholds.temp_warning_min_c <= temp <= thresholds.temp_warning_max_c):
            other_severity = "warning"
        # pH di luar range = warning
        if ph is not None and (ph < thresholds.ph_min or ph > thresholds.ph_max):
            other_severity = "warning"
        # Conductivity tinggi = warning
        if cond is not None and cond > thresholds.conductivity_max_uscm:
            other_severity = "warning"
        
        # GABUNGKAN: Ambil severity tertinggi dari semua parameter
        # Hierarchy: danger > warning > safe
        if coliform_severity == "danger" or do_severity == "danger":
            severity = "danger"  # Ada parameter bahaya
        elif coliform_severity == "warning" or other_severity == "warning":
            severity = "warning"  # Ada parameter waspada
        else:
            severity = "warning"  # Default untuk not potable
    
    # --- Alternative use suggestion (jika tidak potable untuk konsumsi) ---
    if not potable:
        # Jika masalah utama adalah coliform tinggi (≥1.0), hanya untuk non-konsumsi
        if col_for_decision is not None and col_for_decision >= thresholds.total_coliform_danger_mpn_100ml:
            alt.append("Irigasi tanaman non-pangan (bukan untuk sayuran/buah)")
            alt.append("Pembersihan/pencucian umum (bukan untuk mencuci pangan)")
        else:
            # Jika masalah bukan coliform parah, bisa untuk berbagai kegunaan
            if (ph is None or 6.0 <= ph <= 9.0) and (cond is None or cond < 2000):
                alt.append("Irigasi pertanian (cek salinitas untuk tanaman sensitif)")
            if (do is not None and do >= 5.0) and (ph is None or 6.5 <= ph <= 8.5):
                alt.append("Perikanan (dengan monitoring DO & pH)")
    # Proses/utility
    alt.append("Penggunaan proses/utility (cuci/koagulasi) dengan pretreatment sesuai parameter dominan")

    return DetectionDecision(potable=potable, severity=severity, reasons=reasons, recommendations=recs, alternative_use=alt)

def status_badges(readings: Dict[str, float], thresholds: Thresholds = Thresholds()):
    """
    Status untuk dashboard per-parameter dengan sistem 3 tingkatan.
    Badge format: (level, label)
    - level: "optimal" (hijau), "warning" (kuning/oranye), "danger" (merah), "unknown" (abu)
    """
    badges = {}

    # === SUHU (3 Tingkat) ===
    temp = readings.get("temp_c", None)
    if temp is None:
        badges["temp_c"] = ("unknown", "–")
    elif thresholds.temp_safe_min_c <= temp <= thresholds.temp_safe_max_c:
        # AMAN: 10-35°C (hijau)
        badges["temp_c"] = ("optimal", f"Aman {temp:.1f}°C")
    elif thresholds.temp_warning_min_c <= temp <= thresholds.temp_warning_max_c:
        # WASPADA: 36-44°C (oranye) - zona E. coli
        badges["temp_c"] = ("warning", f"⚠️ Waspada {temp:.1f}°C")
    elif temp >= thresholds.temp_hot_safe_c:
        # WASPADA: ≥45°C (oranye) - panas, perlu dinginkan
        badges["temp_c"] = ("warning", f"⚠️ Terlalu panas {temp:.1f}°C")
    elif temp < thresholds.temp_safe_min_c:
        # WASPADA: Terlalu dingin
        badges["temp_c"] = ("warning", f"⚠️ Terlalu dingin {temp:.1f}°C")
    else:
        # 35-36°C: transisi
        badges["temp_c"] = ("warning", f"⚠️ Sedikit tinggi {temp:.1f}°C")

    # === pH (Permenkes 2023) ===
    ph = readings.get("ph", None)
    if ph is None:
        badges["ph"] = ("unknown", "–")
    elif thresholds.ph_min <= ph <= thresholds.ph_max:
        badges["ph"] = ("optimal", f"Aman {ph:.1f}")
    else:
        badges["ph"] = ("warning", f"Di luar 6.5-8.5")

    # === DO (4 Tingkat) ===
    # Aman ≥6.0 | Waspada 5.0-5.9 | Bahaya 0-4.99
    do = readings.get("do_mgl", None)
    if do is None:
        badges["do_mgl"] = ("unknown", "–")
    elif do >= thresholds.do_optimal_mgl:
        # AMAN: ≥6 mg/L (hijau)
        badges["do_mgl"] = ("optimal", f"Aman {do:.1f} mg/L")
    elif do >= thresholds.do_low_mgl:
        # WASPADA: 5.0-5.9 mg/L (kuning/oranye)
        badges["do_mgl"] = ("warning", f"⚠️ Waspada {do:.1f} mg/L")
    else:
        # BAHAYA: 0-4.99 mg/L (merah)
        badges["do_mgl"] = ("danger", f"🔴 Bahaya {do:.1f} mg/L")

    # === KONDUKTIVITAS (EPA) ===
    cond = readings.get("conductivity_uscm", None)
    if cond is None:
        badges["conductivity_uscm"] = ("unknown", "–")
    elif cond <= thresholds.conductivity_max_uscm:
        badges["conductivity_uscm"] = ("optimal", f"Aman {cond:.0f} µS/cm")
    else:
        badges["conductivity_uscm"] = ("warning", f"Tinggi {cond:.0f} µS/cm")

    # === TOTAL COLIFORM (3 Tingkat) ===
    # Aman ≤0.70 | Waspada 0.71-0.99 | Bahaya ≥1.0
    # Note: Ambil dari readings jika ada, atau None
    coliform = readings.get("totalcoliform_mpn_100ml", None)
    if coliform is None:
        badges["totalcoliform_mpn_100ml"] = ("unknown", "–")
    elif coliform <= thresholds.total_coliform_safe_mpn_100ml:
        # AMAN: ≤0.70 MPN/100mL (hijau)
        badges["totalcoliform_mpn_100ml"] = ("optimal", f"Aman {coliform:.2f} MPN/100mL")
    elif coliform < thresholds.total_coliform_danger_mpn_100ml:
        # WASPADA: 0.71-0.99 MPN/100mL (kuning/oranye)
        badges["totalcoliform_mpn_100ml"] = ("warning", f"⚠️ Waspada {coliform:.2f} MPN/100mL")
    else:
        # BAHAYA: ≥1.0 MPN/100mL (merah)
        badges["totalcoliform_mpn_100ml"] = ("danger", f"🔴 Bahaya {coliform:.2f} MPN/100mL")

    return badges
