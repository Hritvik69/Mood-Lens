import { 
  LayoutDashboard, 
  Camera, 
  BarChart3, 
  History, 
  Settings, 
  Info,
  BrainCircuit
} from "lucide-react";

export type PageId = "dashboard" | "camera" | "analytics" | "history" | "settings" | "about";

interface SidebarProps {
  currentPage: PageId;
  onPageChange: (page: PageId) => void;
}

export function Sidebar({ currentPage, onPageChange }: SidebarProps) {
  const menuItems = [
    { id: "dashboard" as PageId, label: "Dashboard", icon: LayoutDashboard },
    { id: "camera" as PageId, label: "Live Camera", icon: Camera },
    { id: "analytics" as PageId, label: "Analytics", icon: BarChart3 },
    { id: "history" as PageId, label: "History Logs", icon: History },
    { id: "settings" as PageId, label: "Settings", icon: Settings },
    { id: "about" as PageId, label: "About", icon: Info },
  ];

  return (
    <aside className="w-64 h-screen border-r border-white/10 glass-panel flex flex-col shrink-0">
      {/* Brand Header */}
      <div className="p-6 border-b border-white/5 flex items-center gap-3">
        <div className="p-2 rounded-xl bg-gradient-to-tr from-brand-600 to-brand-400 border-glow text-white">
          <BrainCircuit size={24} />
        </div>
        <div>
          <h1 className="font-semibold text-lg leading-tight bg-gradient-to-r from-brand-accent to-brand-200 bg-clip-text text-transparent">
            EmotionVision
          </h1>
          <span className="text-[10px] uppercase tracking-wider text-slate-500 font-medium">
            Enterprise AI
          </span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentPage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onPageChange(item.id)}
              className={`w-full flex items-center gap-3.5 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-300 ${
                isActive
                  ? "bg-brand-500/20 text-brand-accent border border-brand-500/30 shadow-lg shadow-brand-500/5"
                  : "text-slate-400 hover:bg-white/5 hover:text-slate-100 border border-transparent"
              }`}
            >
              <Icon size={18} className={isActive ? "text-brand-accent" : "text-slate-400"} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Footer System Status */}
      <div className="p-4 border-t border-white/5 text-[10px] text-slate-500 flex flex-col gap-1">
        <div>App Version: 1.0.0 (Production)</div>
        <div>Model: FERPlus-8 (ONNX)</div>
        <div className="flex items-center gap-1.5 mt-1">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
          <span className="text-slate-400 font-medium">Local Node Ready</span>
        </div>
      </div>
    </aside>
  );
}
export default Sidebar;
