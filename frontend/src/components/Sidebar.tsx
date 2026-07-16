import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/portfolio", label: "Portfolio" },
  { to: "/advisor", label: "Advisor" },
  { to: "/risk", label: "Risk profile" },
];

export function Sidebar() {
  const { user, logout } = useAuth();

  return (
    <aside className="flex h-full w-60 flex-col border-r border-slate-line bg-white">
      <div className="border-b border-slate-line px-6 py-6">
        <p className="font-display text-lg font-medium leading-tight text-ink">Ledger</p>
        <p className="font-mono text-[11px] uppercase tracking-widest text-slate-soft">Agentic Advisor</p>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `block rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-indigo-light text-indigo-dark"
                  : "text-ink/70 hover:bg-paperdim hover:text-ink"
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-slate-line px-4 py-4">
        <p className="truncate text-xs text-slate-soft">{user?.email}</p>
        <button
          onClick={logout}
          className="mt-2 w-full rounded-md border border-slate-line px-3 py-1.5 text-xs font-medium text-ink/70 hover:border-ink/30 hover:text-ink"
        >
          Sign out
        </button>
      </div>
    </aside>
  );
}
