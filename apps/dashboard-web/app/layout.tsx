import type { Metadata } from "next";
import Link from "next/link";

import "./globals.css";

const NAV_ITEMS = [
  { href: "/", label: "总览" },
  { href: "/trading", label: "交易" },
  { href: "/evolution", label: "进化" },
  { href: "/learning", label: "学习" },
  { href: "/system", label: "系统" },
  { href: "/incidents", label: "事件" },
];

export const metadata: Metadata = {
  title: "Quant Evo Terminal",
  description: "Next-generation autonomous investment dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>
        <div className="shell">
          <header className="topbar">
            <div className="brand">
              <span className="eyebrow">Next-Gen Autonomous Investment System</span>
              <h1 className="title">Quant Evo Terminal</h1>
              <p className="subtitle">
                Discord 自然语言控制面 + Dashboard 观察面。重点展示自动交易、自动进化、联网学习与系统治理状态。
              </p>
            </div>
            <nav className="nav" aria-label="Primary">
              {NAV_ITEMS.map((item) => (
                <Link key={item.href} href={item.href}>
                  {item.label}
                </Link>
              ))}
            </nav>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
