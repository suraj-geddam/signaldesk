import { NavLink, Outlet } from "react-router";
import { useAuth } from "../hooks/useAuth";
import { Badge } from "./ui/Badge";

const navLinks = [
  { to: "/feedback", label: "Feedback" },
  { to: "/dashboard", label: "Dashboard" },
  { to: "/insights", label: "Insights" },
];

export function AppLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen flex flex-col">
      <nav className="sticky top-0 z-40 bg-white/80 backdrop-blur-md border-b border-stone-200/70">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center h-14 gap-8">
          {/* Logo */}
          <NavLink
            to="/feedback"
            className="text-base font-bold tracking-tight text-stone-900 whitespace-nowrap"
          >
            SignalDesk
          </NavLink>

          {/* Nav links */}
          <div className="flex items-center gap-1">
            {navLinks.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                className={({ isActive }) =>
                  `px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-signal-50 text-signal-700"
                      : "text-stone-500 hover:text-stone-800 hover:bg-stone-100"
                  }`
                }
              >
                {link.label}
              </NavLink>
            ))}
          </div>

          {/* Right side */}
          <div className="ml-auto flex items-center gap-3">
            {user && (
              <>
                <Badge type="role" value={user.role} />
                <span className="text-sm text-stone-600">{user.username}</span>
                <button
                  onClick={logout}
                  className="text-sm text-stone-400 hover:text-stone-700 transition-colors cursor-pointer"
                >
                  Log out
                </button>
              </>
            )}
          </div>
        </div>
      </nav>

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6">
        <div className="animate-page-in">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
