import type { ReactNode } from "react";
import { useMemo, useState } from "react";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

type AppShellProps = {
  children: ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  const topbar = useMemo(
    () => (
      <Topbar
        onMenuToggle={() => {
          setMobileNavOpen((value) => !value);
        }}
        mobileMenuOpen={mobileNavOpen}
      />
    ),
    [mobileNavOpen],
  );

  return (
    <div className="min-h-screen bg-bg text-text">
      <div className="mx-auto flex min-h-screen max-w-[1600px] flex-col lg:flex-row">
        <aside className="hidden lg:flex lg:w-[300px] lg:shrink-0 lg:flex-col lg:border-r lg:border-white/5 lg:bg-black/10 lg:backdrop-blur-xl">
          <Sidebar />
        </aside>

        <div className="flex min-h-screen flex-1 flex-col">
          {topbar}

          {mobileNavOpen ? (
            <div className="border-b border-white/5 bg-black/50 px-4 py-4 backdrop-blur-xl lg:hidden">
              <Sidebar onNavigate={() => setMobileNavOpen(false)} />
            </div>
          ) : null}

          <main className="flex-1 px-4 py-4 pb-10 sm:px-6 lg:px-8">{children}</main>
        </div>
      </div>
    </div>
  );
}
