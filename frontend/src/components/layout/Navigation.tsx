"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { label: "Dashboard", href: "/", icon: HomeIcon },
  { label: "Games", href: "/games", icon: ListIcon },
  { label: "Analytics", href: "/analytics", icon: ChartIcon },
];

export default function Navigation() {
  const pathname = usePathname();

  return (
    <nav
      className="fixed z-navigation bottom-6 left-1/2 -translate-x-1/2 max-md:bottom-0 max-md:left-0 max-md:right-0 max-md:translate-x-0 max-md:w-full"
      aria-label="Main navigation"
    >
      <div className="glass flex items-center gap-1 px-3 py-2 rounded-2xl max-md:rounded-none max-md:px-0 max-md:justify-around max-md:border-t max-md:border-t-white/[0.06] max-md:pb-[max(0.5rem,env(safe-area-inset-bottom))]">
        {navItems.map((item) => {
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`
                group flex items-center gap-2 px-4 py-2.5 rounded-xl
                transition-all duration-base
                max-md:flex-col max-md:gap-0.5 max-md:px-3 max-md:py-1.5 max-md:rounded-lg
                ${
                  isActive
                    ? "bg-white/[0.08] text-text-primary"
                    : "text-text-muted hover:text-text-secondary hover:bg-white/[0.04]"
                }
              `}
            >
              <item.icon
                className={`w-5 h-5 transition-transform duration-base group-hover:scale-110 ${
                  isActive ? "scale-110" : ""
                }`}
              />
              <span
                className={`
                  font-medium transition-all duration-base
                  text-sm max-md:text-[10px]
                  max-md:opacity-100 max-md:max-w-none
                  ${
                    isActive
                      ? "opacity-100 max-w-[100px] md:opacity-100 md:max-w-[100px]"
                      : "opacity-0 max-w-0 overflow-hidden md:group-hover:opacity-100 md:group-hover:max-w-[100px]"
                  }
                `}
              >
                {item.label}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

function HomeIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0a1 1 0 01-1-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 01-1 1h-2z" />
    </svg>
  );
}

function ListIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M4 6h16M4 10h16M4 14h16M4 18h16" />
    </svg>
  );
}

function ChartIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  );
}
