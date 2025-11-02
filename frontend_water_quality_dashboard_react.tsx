import { useState, useEffect } from "react";
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

// ---- Animations CSS ----
const styles = `
  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }
  
  @keyframes scaleIn {
    from { 
      opacity: 0;
      transform: scale(0.9);
    }
    to { 
      opacity: 1;
      transform: scale(1);
    }
  }
  
  .animate-fadeIn {
    animation: fadeIn 0.2s ease-out;
  }
  
  .animate-scaleIn {
    animation: scaleIn 0.3s ease-out;
  }
`;

// Inject styles
if (typeof document !== 'undefined') {
  const styleSheet = document.createElement("style");
  styleSheet.textContent = styles;
  document.head.appendChild(styleSheet);
}

// ---- CONFIG ----
const API_BASE = import.meta.env.VITE_API_BASE || "https://water-quality-ai-ejw2.onrender.com";
const REFRESH_INTERVAL = 3600000; // Auto-refresh setiap 1 jam

// Utility kecil
const fmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });

// Format tanggal dengan timezone WIB (Jakarta) - UTC+7
const formatDateWIB = (dateString: string) => {
  const date = new Date(dateString);
  // Timestamp server dalam UTC, tambahkan 7 jam untuk WIB
  const wibTime = new Date(date.getTime() + (7 * 60 * 60 * 1000));
  
  return wibTime.toLocaleString('id-ID', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  });
};
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
  // ---- Sensor data state (dari IoT) ----
  const [temp, setTemp] = useState<number>(0);
  const [doMgl, setDoMgl] = useState<number>(0);
  const [ph, setPh] = useState<number>(0);
  const [cond, setCond] = useState<number>(0);
  const [coliform, setColiform] = useState<number>(0);
  const [lastUpdate, setLastUpdate] = useState<string>("");

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

  // ---- IoT History state ----
  const [iotHistory, setIotHistory] = useState<any[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  // ---- Modal state ----
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");

  // Fungsi untuk fetch data terbaru dari IoT
  async function fetchLatestIoTData() {
    setError(null);
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/iot/latest`);
      if (!res.ok) {
        if (res.status === 404) {
          throw new Error("Belum ada data IoT. Pastikan ESP32 sudah mengirim data.");
        }
        throw new Error(`HTTP ${res.status}`);
      }
      const response = await res.json();
      const iotData = response.data; // Extract data dari response wrapper
      
      // Update sensor readings
      setTemp(iotData.temp_c);
      setDoMgl(iotData.do_mgl);
      setPh(iotData.ph);
      setCond(iotData.conductivity_uscm);
      setColiform(iotData.totalcoliform_mv);
      setLastUpdate(formatDateWIB(iotData.timestamp));
      
      // Auto-predict dengan data IoT terbaru
      await handlePredict(iotData);
      
    } catch (e: any) {
      setError(e.message || String(e));
    } finally {
      setLoading(false);
    }
  }

  async function handlePredict(iotData?: any) {
    try {
      const body: any = {
        temp_c: iotData ? iotData.temp_c : Number(temp),
        do_mgl: iotData ? iotData.do_mgl : Number(doMgl),
        ph: iotData ? iotData.ph : Number(ph),
        conductivity_uscm: iotData ? iotData.conductivity_uscm : Number(cond),
      };

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
    }
  }

  // Fungsi untuk fetch history data dari IoT
  async function fetchIoTHistory() {
    setHistoryLoading(true);
    try {
      const res = await fetch(`${API_BASE}/iot/history?limit=50`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const response = await res.json();
      
      // Predict untuk setiap data history
      const historyWithPredictions = await Promise.all(
        response.data.map(async (item: any) => {
          try {
            const predictBody = {
              temp_c: item.temp_c,
              do_mgl: item.do_mgl,
              ph: item.ph,
              conductivity_uscm: item.conductivity_uscm,
            };
            const predictRes = await fetch(`${API_BASE}/predict`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(predictBody),
            });
            const predictData = await predictRes.json();
            
            return {
              ...item,
              prediction: predictData.prediction.total_coliform_mpn_100ml,
              potable: predictData.ai_detection.potable,
            };
          } catch (e) {
            return {
              ...item,
              prediction: null,
              potable: null,
            };
          }
        })
      );
      
      setIotHistory(historyWithPredictions);
    } catch (e: any) {
      console.error("Error fetching history:", e);
    } finally {
      setHistoryLoading(false);
    }
  }

  // Fungsi untuk hapus semua history
  async function confirmClearHistory() {
    const recordCount = iotHistory.length;
    setShowDeleteModal(false);
    setHistoryLoading(true);
    
    try {
      const res = await fetch(`${API_BASE}/iot/clear`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const response = await res.json();
      
      // Clear local state
      setIotHistory([]);
      
      // Refresh latest data (akan error 404 karena data kosong, tapi tidak masalah)
      setTemp(0);
      setDoMgl(0);
      setPh(0);
      setCond(0);
      setColiform(0);
      setLastUpdate("");
      setPrediction(null);
      setDecision(null);
      
      // Show success modal
      setSuccessMessage(`Berhasil menghapus ${recordCount} data history!`);
      setShowSuccessModal(true);
    } catch (e: any) {
      setSuccessMessage(`Gagal menghapus history: ${e.message}`);
      setShowSuccessModal(true);
    } finally {
      setHistoryLoading(false);
    }
  }

  // Fungsi untuk refresh semua data (latest + history)
  async function refreshAllData() {
    await fetchLatestIoTData();
    await fetchIoTHistory();
  }

  // Auto-refresh setiap interval
  useEffect(() => {
    // Fetch pertama kali saat component mount
    refreshAllData();
    
    // Set interval untuk auto-refresh
    const intervalId = setInterval(() => {
      refreshAllData();
    }, REFRESH_INTERVAL);
    
    // Cleanup interval saat component unmount
    return () => clearInterval(intervalId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
          <div>
            <h1 className="text-2xl font-bold">Dashboard Monitoring Kualitas Air Real-Time</h1>
            <p className="text-sm text-gray-500 mt-1">Data dari IoT Sensor • Auto-refresh setiap 1 jam</p>
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-500">Update Terakhir</div>
            <div className="text-sm font-semibold text-indigo-600">{lastUpdate || "Memuat..."}</div>
            {loading && <div className="text-xs text-blue-500 mt-1">⟳ Memperbarui...</div>}
            <button 
              onClick={refreshAllData} 
              disabled={loading || historyLoading}
              className="mt-2 px-3 py-1 text-xs rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              🔄 Refresh Manual
            </button>
          </div>
        </header>

        {/* Status & Error Messages */}
        {error && (
          <div className="mb-6 p-4 rounded-2xl bg-red-50 border border-red-200">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-red-700 font-semibold">Error:</span>
              <span className="text-red-600">{error}</span>
            </div>
          </div>
        )}

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

        {/* Sensor Readings - KPI Cards */}
        <div className="mb-6">
          <h2 className="text-lg font-semibold mb-3 text-gray-700">📊 Pembacaan Sensor Real-Time</h2>
          <div className="grid md:grid-cols-6 gap-4">
            {card("Suhu", fmt.format(temp), "°C")}
            {card("Dissolved Oxygen (DO)", fmt.format(doMgl), "mg/L", bDO)}
            {card("pH", fmt.format(ph), "", bPH)}
            {card("Konduktivitas", fmt.format(cond), "µS/cm", bCond)}
            {card("Total Coliform (Sensor)", fmt.format(coliform), "mV")}
            <div className="rounded-2xl shadow-sm p-4 bg-white border border-gray-100">
              <div className="text-gray-500 text-sm mb-2">Status Kelayakan</div>
              <div className="h-24">
                <ResponsiveContainer width="100%" height="100%">
                  <RadialBarChart innerRadius="70%" outerRadius="100%" data={[{ name: "score", value: gaugeValue }]} startAngle={180} endAngle={0}>
                    <RadialBar background dataKey="value" fill={gaugeValue===100?"#22c55e":"#ef4444"} />
                  </RadialBarChart>
                </ResponsiveContainer>
              </div>
              <div className={`text-center text-sm font-bold ${gaugeValue===100?"text-green-600":"text-red-600"}`}>
                {gaugeValue===100?"LAYAK MINUM":"TIDAK LAYAK"}
              </div>
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

        {/* Tabel History Data IoT */}
        <div className="mt-6 rounded-2xl shadow-sm p-6 bg-white border border-gray-100">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-bold text-gray-800">📜 Riwayat Data IoT</h2>
              <p className="text-sm text-gray-500 mt-1">History data sensor dengan prediksi AI (max 50 data terbaru)</p>
            </div>
            <div className="flex gap-2">
              <button 
                onClick={fetchIoTHistory} 
                disabled={historyLoading}
                className="px-4 py-2 text-sm rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {historyLoading ? "⟳ Loading..." : "🔄 Refresh"}
              </button>
              <button 
                onClick={() => setShowDeleteModal(true)} 
                disabled={historyLoading || iotHistory.length === 0}
                className="px-4 py-2 text-sm rounded-lg bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                🗑️ Hapus Semua
              </button>
            </div>
          </div>

          {historyLoading && iotHistory.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
              <p>Memuat data history...</p>
            </div>
          ) : iotHistory.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
              </svg>
              <p className="text-lg font-semibold">Belum ada data history</p>
              <p className="text-sm mt-2">Data IoT akan muncul di sini setelah ESP32 mengirim data</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b-2 border-gray-200">
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">#</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Timestamp (WIB)</th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-700">Suhu<br/>(°C)</th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-700">DO<br/>(mg/L)</th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-700">pH</th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-700">Konduktivitas<br/>(µS/cm)</th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-700">Total Coliform<br/>(MPN/100mL)</th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-700">Prediksi AI<br/>(MPN/100mL)</th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-700">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {iotHistory.map((item, idx) => (
                    <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                      <td className="py-3 px-4 text-gray-600">{idx + 1}</td>
                      <td className="py-3 px-4 text-gray-700 font-mono text-xs">
                        {formatDateWIB(item.timestamp)}
                      </td>
                      <td className="text-center py-3 px-4">{fmt.format(item.temp_c)}</td>
                      <td className="text-center py-3 px-4">{fmt.format(item.do_mgl)}</td>
                      <td className="text-center py-3 px-4">{fmt.format(item.ph)}</td>
                      <td className="text-center py-3 px-4">{fmt.format(item.conductivity_uscm)}</td>
                      <td className="text-center py-3 px-4">{fmt.format(item.totalcoliform_mv)}</td>
                      <td className="text-center py-3 px-4 font-semibold">
                        {item.prediction !== null ? (
                          <span className={`${item.prediction > 0 ? 'text-red-600' : 'text-green-600'}`}>
                            {fmt.format(item.prediction)}
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="text-center py-3 px-4">
                        {item.potable !== null ? (
                          <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${
                            item.potable 
                              ? 'bg-green-100 text-green-700' 
                              : 'bg-red-100 text-red-700'
                          }`}>
                            {item.potable ? '✓ Layak' : '✗ Tidak Layak'}
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          
          {iotHistory.length > 0 && (
            <div className="mt-4 text-sm text-gray-500 text-center">
              Menampilkan {iotHistory.length} data terbaru
            </div>
          )}
        </div>

        {/* Modal Konfirmasi Hapus */}
        {showDeleteModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm flex items-center justify-center z-50 animate-fadeIn">
            <div className="bg-white rounded-3xl shadow-2xl p-8 max-w-md w-full mx-4 transform animate-scaleIn">
              {/* Icon Warning */}
              <div className="flex justify-center mb-6">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-red-100 to-red-200 flex items-center justify-center animate-bounce">
                  <svg className="w-12 h-12 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
              </div>

              {/* Title */}
              <h3 className="text-2xl font-bold text-center text-gray-900 mb-3">
                Hapus Semua Data?
              </h3>

              {/* Message */}
              <div className="text-center mb-6">
                <p className="text-gray-600 mb-2">
                  Anda akan menghapus <span className="font-bold text-red-600">{iotHistory.length} data</span> history
                </p>
                <p className="text-sm text-gray-500">
                  Tindakan ini tidak dapat dibatalkan!
                </p>
              </div>

              {/* Buttons */}
              <div className="flex gap-3">
                <button
                  onClick={() => setShowDeleteModal(false)}
                  className="flex-1 px-6 py-3 rounded-xl font-semibold text-gray-700 bg-gray-100 hover:bg-gray-200 transition-all duration-200 transform hover:scale-105"
                >
                  Batal
                </button>
                <button
                  onClick={confirmClearHistory}
                  className="flex-1 px-6 py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 transition-all duration-200 transform hover:scale-105 shadow-lg hover:shadow-xl"
                >
                  Ya, Hapus
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modal Success/Error */}
        {showSuccessModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm flex items-center justify-center z-50 animate-fadeIn">
            <div className="bg-white rounded-3xl shadow-2xl p-8 max-w-md w-full mx-4 transform animate-scaleIn">
              {/* Icon Success */}
              <div className="flex justify-center mb-6">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-green-100 to-green-200 flex items-center justify-center">
                  <svg className="w-12 h-12 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              </div>

              {/* Title */}
              <h3 className="text-2xl font-bold text-center text-gray-900 mb-3">
                {successMessage.includes("Gagal") ? "Oops!" : "Berhasil!"}
              </h3>

              {/* Message */}
              <p className="text-center text-gray-600 mb-6">
                {successMessage}
              </p>

              {/* Button */}
              <button
                onClick={() => setShowSuccessModal(false)}
                className="w-full px-6 py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 transition-all duration-200 transform hover:scale-105 shadow-lg hover:shadow-xl"
              >
                OK
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
