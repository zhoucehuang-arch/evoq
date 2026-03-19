"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Overview" },
  { href: "/trading", label: "Trading" },
  { href: "/evolution", label: "Evolution" },
  { href: "/learning", label: "Learning" },
  { href: "/system", label: "System" },
  { href: "/incidents", label: "Incidents" },
];

export function TopNav() {
  const pathname = usePathname();

  return (
    <nav className="nav" aria-label="Primary">
      {NAV_ITEMS.map((item) => {
        const isActive = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={isActive ? "is-active" : undefined}
            aria-current={isActive ? "page" : undefined}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
