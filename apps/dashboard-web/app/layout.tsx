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
            <div className="brand">
              <span className="eyebrow">Autonomous Investment Runtime</span>
              <h1 className="title">EvoQ Terminal</h1>
              <p className="subtitle">
                Use Discord for control and approvals. Use the dashboard for monitoring, review, and operator visibility.
              </p>
              <div className="header-note-row">
                <span className="header-note">Discord-first owner workflow</span>
                <span className="header-note">Governed trading and evolution</span>
                <span className="header-note">Built for long-running VPS operation</span>
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
