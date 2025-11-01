import { useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  AreaChart,
  Area,
  RadialBarChart,
  RadialBar,
} from "recharts";

// ---- CONFIG ----
const API_BASE = import.meta.env.VITE_API_BASE || "https://water-quality-ai-ejw2.onrender.com";

// Utility kecil
const fmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });
const badgeStyle = (kind: string) => {
  switch (kind) {
    case "optimal":
    case "good":
    case "normal":
      return "bg-green-100 text-green-700";
    case "low":
    case "warning":
      return "bg-amber-100 text-amber-700";
    case "high":
      return "bg-red-100 text-red-700";
    default:
      return "bg-gray-100 text-gray-600";
  }
};

export default function WaterQualityDashboard() {
  // ---- Form state ----
  const [temp, setTemp] = useState<number>(27.8);
  const [doMgl, setDoMgl] = useState<number>(6.2);
  const [ph, setPh] = useState<number>(7.2);
  const [cond, setCond] = useState<number>(620);

  const [useMeasuredColiform, setUseMeasuredColiform] = useState<boolean>(true);
  const [coliform, setColiform] = useState<number>(0);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ---- API response state ----
  const [prediction, setPrediction] = useState<
    | null
    | {
        total_coliform_mpn_100ml: number;
        ci90_low: number;
        ci90_high: number;
      }
  >(null);
  const [badges, setBadges] = useState<any>(null);
  const [decision, setDecision] = useState<
    | null
    | {
        potable: boolean;
        reasons: string[];
        recommendations: string[];
        alternative_use: string[];
      }
  >(null);

  // history untuk chart (simulasi live)
  const [history, setHistory] = useState<
    { t: string; pred: number; low: number; high: number }[]
  >([]);

  async function handlePredict() {
    setError(null);
    setLoading(true);
    try {
      const body: any = {
        temp_c: Number(temp),
        do_mgl: Number(doMgl),
        ph: Number(ph),
        conductivity_uscm: Number(cond),
      };
      if (useMeasuredColiform) {
        body.totalcoliform_mpn_100ml = Number(coliform);
      }

      const res = await fetch(`${API_BASE}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      setPrediction({
        total_coliform_mpn_100ml: data.prediction.total_coliform_mpn_100ml,
        ci90_low: data.prediction.ci90_low,
        ci90_high: data.prediction.ci90_high,
      });
      setBadges(data.status_badges);
      setDecision({
        potable: data.ai_detection.potable,
        reasons: data.ai_detection.reasons,
        recommendations: data.ai_detection.recommendations,
        alternative_use: data.ai_detection.alternative_use,
      });

      const t = new Date();
      setHistory((h) => [
        ...h.slice(-49), // keep last 49 points (max 50)
        {
          t: t.toLocaleTimeString([], { hour12: false }),
          pred: data.prediction.total_coliform_mpn_100ml,
          low: data.prediction.ci90_low,
          high: data.prediction.ci90_high,
        },
      ]);
    } catch (e: any) {
      setError(e.message || String(e));
    } finally {
      setLoading(false);
    }
  }

  const gaugeValue = decision ? (decision.potable ? 100 : 0) : 0;

  const card = (
    title: string,
    value: string,
    unit: string,
    badge?: [string, string]
  ) => (
    <div className="rounded-2xl shadow-sm p-4 bg-white border border-gray-100">
      <div className="text-gray-500 text-sm mb-1">{title}</div>
      <div className="text-2xl font-semibold">{value} <span className="text-base text-gray-500">{unit}</span></div>
      {badge && (
        <span className={`inline-block mt-2 px-2 py-1 text-xs rounded-full ${badgeStyle(badge[0])}`}>
          {badge[1]}
        </span>
      )}
    </div>
  );

  const bPH = badges?.ph as [string, string] | undefined;
  const bDO = badges?.do_mgl as [string, string] | undefined;
  const bCond = badges?.conductivity_uscm as [string, string] | undefined;

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <div className="max-w-7xl mx-auto p-4 sm:p-6">
        <header className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">Dashboard Kualitas Air</h1>
          <div className="text-sm text-gray-500">Water Quality AI • Demo</div>
        </header>

        {/* Input Form */}
        <div className="grid md:grid-cols-5 gap-4 mb-4">
          <div className="bg-white border border-gray-100 rounded-2xl p-4">
            <label className="block text-xs text-gray-500 mb-1">Suhu (°C)</label>
            <input type="number" step="0.1" value={temp} onChange={(e)=>setTemp(parseFloat(e.target.value))} className="w-full rounded-xl border-gray-200"/>
          </div>
          <div className="bg-white border border-gray-100 rounded-2xl p-4">
            <label className="block text-xs text-gray-500 mb-1">Dissolved Oxygen (mg/L)</label>
            <input type="number" step="0.1" value={doMgl} onChange={(e)=>setDoMgl(parseFloat(e.target.value))} className="w-full rounded-xl border-gray-200"/>
          </div>
          <div className="bg-white border border-gray-100 rounded-2xl p-4">
            <label className="block text-xs text-gray-500 mb-1">pH</label>
            <input type="number" step="0.01" value={ph} onChange={(e)=>setPh(parseFloat(e.target.value))} className="w-full rounded-xl border-gray-200"/>
          </div>
          <div className="bg-white border border-gray-100 rounded-2xl p-4">
            <label className="block text-xs text-gray-500 mb-1">Konduktivitas (µS/cm)</label>
            <input type="number" step="1" value={cond} onChange={(e)=>setCond(parseFloat(e.target.value))} className="w-full rounded-xl border-gray-200"/>
          </div>
          <div className="bg-white border border-gray-100 rounded-2xl p-4">
            <label className="flex items-center gap-2 text-xs text-gray-500 mb-1">
              <input type="checkbox" checked={useMeasuredColiform} onChange={(e)=>setUseMeasuredColiform(e.target.checked)}/>
              Masukkan Total Coliform terukur (opsional)
            </label>
            <input type="number" step="0.1" value={coliform} onChange={(e)=>setColiform(parseFloat(e.target.value))} className="w-full rounded-xl border-gray-200" disabled={!useMeasuredColiform}/>
          </div>
        </div>
        <div className="flex items-center gap-3 mb-6">
          <button onClick={handlePredict} disabled={loading} className="px-4 py-2 rounded-xl bg-indigo-600 text-white shadow hover:bg-indigo-700 disabled:opacity-50">{loading ? "Memproses..." : "Prediksi & Evaluasi"}</button>
          {error && <span className="text-red-600 text-sm">{error}</span>}
        </div>

        {/* Status Kelayakan Air - Banner Besar */}
        {decision && (
          <div className={`mb-6 p-6 rounded-2xl shadow-lg ${decision.potable ? "bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-300" : "bg-gradient-to-r from-red-50 to-rose-50 border-2 border-red-300"}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className={`w-20 h-20 rounded-full flex items-center justify-center ${decision.potable ? "bg-green-500" : "bg-red-500"}`}>
                  <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    {decision.potable ? (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    ) : (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    )}
                  </svg>
                </div>
                <div>
                  <h2 className={`text-3xl font-bold ${decision.potable ? "text-green-700" : "text-red-700"}`}>
                    {decision.potable ? "AIR LAYAK MINUM" : "AIR TIDAK LAYAK MINUM"}
                  </h2>
                  <p className={`text-lg mt-1 ${decision.potable ? "text-green-600" : "text-red-600"}`}>
                    {decision.potable ? "✓ Aman untuk dikonsumsi" : "⚠ Perlu pengolahan lebih lanjut"}
                  </p>
                  {prediction && (
                    <p className="text-sm mt-2 text-gray-600">
                      Prediksi Total Coliform: <span className="font-semibold">{fmt.format(prediction.total_coliform_mpn_100ml)} MPN/100mL</span>
                      {" "}(Batas aman: 0 MPN/100mL)
                    </p>
                  )}
                </div>
              </div>
              <div className={`text-6xl font-bold ${decision.potable ? "text-green-400" : "text-red-400"}`}>
                {decision.potable ? "✓" : "✗"}
              </div>
            </div>
          </div>
        )}

        {/* KPI Cards */}
        <div className="grid md:grid-cols-5 gap-4 mb-6">
          {card("Konduktivitas", fmt.format(cond), "µS/cm", bCond)}
          {card("Suhu", fmt.format(temp), "°C")}
          {card("Dissolved Oxygen (DO)", fmt.format(doMgl), "mg/L", bDO)}
          {card("pH", fmt.format(ph), "", bPH)}
          <div className="rounded-2xl shadow-sm p-4 bg-white border border-gray-100">
            <div className="text-gray-500 text-sm mb-2">Status Kelayakan</div>
            <div className="h-36">
              <ResponsiveContainer width="100%" height="100%">
                <RadialBarChart innerRadius="70%" outerRadius="100%" data={[{ name: "score", value: gaugeValue }]} startAngle={180} endAngle={0}>
                  <RadialBar background dataKey="value" fill={gaugeValue===100?"#22c55e":"#ef4444"} />
                </RadialBarChart>
              </ResponsiveContainer>
            </div>
            <div className={`text-center text-lg font-bold ${gaugeValue===100?"text-green-600":"text-red-600"}`}>
              {gaugeValue===100?"LAYAK MINUM":"TIDAK LAYAK"}
            </div>
          </div>
        </div>

        {/* Charts & Panels */}
        <div className="grid md:grid-cols-3 gap-6">
          <div className="md:col-span-2 rounded-2xl shadow-sm p-4 bg-white border border-gray-100">
            <div className="flex items-center justify-between mb-2">
              <div>
                <div className="text-gray-700 font-semibold">Prediksi Mikroba (proxy)</div>
                <div className="text-xs text-gray-500">Total Coliform (MPN/100 mL) — estimasi AI dari 4 parameter</div>
              </div>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={history} margin={{ top: 10, right: 20, bottom: 0, left: 0 }}>
                  <defs>
                    <linearGradient id="ci" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.25}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="t" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Area type="monotone" dataKey="pred" stroke="#3b82f6" fill="url(#ci)" strokeWidth={2} />
                  {/* CI as band (render as two lines for simplicity) */}
                  <Line type="monotone" dataKey="low" stroke="#9ca3af" dot={false} strokeDasharray="4 4" />
                  <Line type="monotone" dataKey="high" stroke="#9ca3af" dot={false} strokeDasharray="4 4" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="rounded-2xl shadow-sm p-4 bg-white border border-gray-100">
            <div className="text-gray-700 font-semibold mb-2">AI Detection — Rangkuman</div>
            {decision ? (
              <div className="space-y-4 text-sm">
                <div>
                  <div className="text-gray-500 mb-1">Alasan/Temuan</div>
                  {decision.reasons.length === 0 ? (
                    <div className="text-green-600">Tidak ada pelanggaran ambang terdeteksi.</div>
                  ) : (
                    <ul className="list-disc ml-5 space-y-1">
                      {decision.reasons.map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  )}
                </div>
                <div>
                  <div className="text-gray-500 mb-1">Rekomendasi</div>
                  {decision.recommendations.length === 0 ? (
                    <div className="text-gray-500">–</div>
                  ) : (
                    <ul className="list-disc ml-5 space-y-1">
                      {decision.recommendations.map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  )}
                </div>
                <div>
                  <div className="text-gray-500 mb-1">Alternatif Penggunaan</div>
                  <ul className="list-disc ml-5 space-y-1">
                    {decision.alternative_use.map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                </div>
                <div className="text-xs text-gray-400">*Prediksi mikroba adalah estimasi AI, bukan hasil uji lab.</div>
              </div>
            ) : (
              <div className="text-gray-500 text-sm">Belum ada hasil. Masukkan data dan klik "Prediksi & Evaluasi".</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
