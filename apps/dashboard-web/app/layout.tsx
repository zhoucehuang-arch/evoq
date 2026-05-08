import type { Metadata } from "next";

import { TopNav } from "@/components/top-nav";

import "./globals.css";

export const metadata: Metadata = {
  title: "EvoQ Workbench",
  description: "Dashboard-first quant research and paper trading workbench",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <header className="topbar">
            <div className="brand-shell">
              <div className="brand-mark" aria-hidden="true">
                EQ
              </div>
              <div className="brand">
                <div className="brand-status-row">
                  <span className="brand-status-dot" />
                  <span className="brand-status-label">Dashboard-first runtime</span>
                  <span className="brand-divider" />
                  <span className="brand-status-label">Optional light gateway</span>
                </div>
                <span className="eyebrow">Quant Research And Paper Runtime</span>
                <h1 className="title">EvoQ Workbench</h1>
                <p className="subtitle">
                  Use the dashboard for research, evidence, backtests, paper runs, and governance. The light gateway
                  stays limited to alerts, quick approvals, pause, resume, and emergency control.
                </p>
                <div className="header-note-row">
                  <span className="header-note">Paper-first live gating</span>
                  <span className="header-note">Simple entry, deep workflow</span>
                  <span className="header-note">Codex implementation lane</span>
                </div>
              </div>
            </div>
            <TopNav />
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
