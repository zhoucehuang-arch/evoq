import type { Metadata } from "next";

import { TopNav } from "@/components/top-nav";

import "./globals.css";

export const metadata: Metadata = {
  title: "EvoQ Terminal",
  description: "Autonomous investment dashboard",
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
                  <span className="brand-status-label">Authority runtime</span>
                  <span className="brand-divider" />
                  <span className="brand-status-label">Discord-first owner flow</span>
                </div>
                <span className="eyebrow">Autonomous Investment Runtime</span>
                <h1 className="title">EvoQ Terminal</h1>
                <p className="subtitle">
                  Use Discord for control and approvals. Use the dashboard as the operating terminal for risk, learning,
                  strategy, and execution visibility.
                </p>
                <div className="header-note-row">
                  <span className="header-note">Paper-first live gating</span>
                  <span className="header-note">US and CN market modes</span>
                  <span className="header-note">Codex-driven worker plane</span>
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
