import { useState, useEffect } from "react";
import { 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  Legend, 
  LineChart, 
  Line 
} from "recharts";
import { BarChart3, TrendingUp, ShieldAlert, Award } from "lucide-react";

export function Analytics() {
  const [distData, setDistData] = useState<any[]>([]);
  const [timelineData, setTimelineData] = useState<any[]>([]);
  const [qualityData, setQualityData] = useState<any>({ lighting: 0, blur: 0, centering: 0 });
  const [loading, setLoading] = useState(true);

  const fetchAnalytics = async () => {
    try {
      // 1. Fetch Expression Distributions
      const distRes = await fetch("http://127.0.0.1:8000/api/analytics/distribution");
      if (distRes.ok) {
        const data = await distRes.json();
        setDistData(data);
      }
      
      // 2. Fetch Time series details
      const timelineRes = await fetch("http://127.0.0.1:8000/api/analytics/timeline");
      if (timelineRes.ok) {
        const data = await timelineRes.json();
        // Keep last 30 entries
        setTimelineData(data.slice(-30));
      }
      
      // 3. Fetch Quality Metrics
      const qualityRes = await fetch("http://127.0.0.1:8000/api/analytics/quality");
      if (qualityRes.ok) {
        const data = await qualityRes.json();
        setQualityData(data);
      }
    } catch (err) {
      console.warn("Error fetching analytics datasets:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  // Standard premium theme color palette
  const COLORS = ["#00f2fe", "#7e1aff", "#fbbf24", "#34d399", "#f87171", "#a78bfa", "#f472b6", "#64748b"];

  const qualityBarData = [
    { name: "Focus / Blur", Score: qualityData.blur || 0 },
    { name: "Lighting", Score: qualityData.lighting || 0 },
    { name: "Centering", Score: qualityData.centering || 0 },
  ];

  return (
    <div className="flex-1 overflow-y-auto p-8 space-y-8 select-none">
      <div>
        <h2 className="text-2xl font-bold text-glow">Expression Analytics</h2>
        <p className="text-xs text-slate-400">DuckDB aggregated dashboards summarizing session historical telemetry.</p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-96">
          <div className="text-center space-y-3">
            <div className="w-8 h-8 rounded-full border-2 border-brand-accent border-t-transparent animate-spin mx-auto" />
            <p className="text-xs text-slate-500">Compiling DuckDB aggregations...</p>
          </div>
        </div>
      ) : distData.length === 0 ? (
        <div className="p-12 rounded-3xl bg-white/5 border border-white/5 text-center text-sm text-slate-500 max-w-xl mx-auto space-y-3">
          <BarChart3 size={32} className="mx-auto text-slate-600" />
          <h4 className="font-semibold text-slate-400">No Analytics Available</h4>
          <p className="text-xs text-slate-600 leading-relaxed">
            Record a live camera session to log data points. Historical records will be immediately indexed and compiled by the analytical engine.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Expression Distribution (Pie Chart) */}
          <div className="glass-panel p-6 rounded-3xl space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Award size={16} className="text-brand-accent" />
              Facial Expressions Occurrence
            </h3>
            <div className="h-64 flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={distData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={3}
                    dataKey="count"
                    nameKey="expression"
                  >
                    {distData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: "rgba(15, 23, 42, 0.95)", borderColor: "rgba(255, 255, 255, 0.1)", borderRadius: "12px" }}
                    itemStyle={{ color: "#ffffff", fontSize: "12px" }}
                  />
                  <Legend 
                    verticalAlign="bottom" 
                    height={36} 
                    iconSize={10} 
                    iconType="circle"
                    wrapperStyle={{ fontSize: "11px", color: "#94a3b8" }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Average Quality Features (Bar Chart) */}
          <div className="glass-panel p-6 rounded-3xl space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <ShieldAlert size={16} className="text-brand-accent" />
              Mean Scene Quality Factors
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={qualityBarData}>
                  <XAxis dataKey="name" stroke="#64748b" fontSize={11} tickLine={false} />
                  <YAxis stroke="#64748b" fontSize={11} tickLine={false} domain={[0, 100]} />
                  <Tooltip 
                    cursor={{ fill: "rgba(255,255,255,0.02)" }}
                    contentStyle={{ backgroundColor: "rgba(15, 23, 42, 0.95)", borderColor: "rgba(255, 255, 255, 0.1)", borderRadius: "12px" }}
                    itemStyle={{ color: "#ffffff", fontSize: "12px" }}
                  />
                  <Bar dataKey="Score" radius={[8, 8, 0, 0]} maxBarSize={45}>
                    {qualityBarData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Pipeline Telemetry Trends (Line Chart) */}
          <div className="lg:col-span-2 glass-panel p-6 rounded-3xl space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <TrendingUp size={16} className="text-brand-accent" />
              Live Frame Classification Trend
            </h3>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={timelineData}>
                  <XAxis 
                    dataKey="timestamp" 
                    stroke="#64748b" 
                    fontSize={10} 
                    tickFormatter={(tick) => tick.split("T")[1]?.slice(0, 5) || tick}
                    tickLine={false}
                  />
                  <YAxis stroke="#64748b" fontSize={10} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: "rgba(15, 23, 42, 0.95)", borderColor: "rgba(255, 255, 255, 0.1)", borderRadius: "12px" }}
                    itemStyle={{ color: "#ffffff", fontSize: "12px" }}
                  />
                  <Legend wrapperStyle={{ fontSize: "11px", color: "#94a3b8" }} />
                  <Line 
                    type="monotone" 
                    dataKey="confidence" 
                    name="Avg Confidence (%)" 
                    stroke="#00f2fe" 
                    strokeWidth={2}
                    activeDot={{ r: 4 }} 
                    dot={false}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="smile_intensity" 
                    name="Smile Intensity (%)" 
                    stroke="#7e1aff" 
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="quality" 
                    name="Frame Quality (%)" 
                    stroke="#34d399" 
                    strokeWidth={1.5}
                    strokeDasharray="4 4"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
export default Analytics;
