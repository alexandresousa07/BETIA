"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  Bell,
  Brain,
  Globe,
  History,
  LayoutDashboard,
  Radio,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/competitions", label: "Competições", icon: Globe },
  { href: "/matches", label: "Partidas", icon: Radio },
  { href: "/recommendations", label: "Entradas", icon: Brain },
  { href: "/alerts", label: "Alertas", icon: Bell },
  { href: "/history", label: "Histórico", icon: History },
  { href: "/logs", label: "Logs", icon: Activity },
  { href: "/settings", label: "Configurações", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-screen w-64 flex-col border-r border-border bg-card">
      <div className="flex h-16 items-center gap-2 border-b border-border px-6">
        <Brain className="h-7 w-7 text-primary" />
        <div>
          <h1 className="text-sm font-bold tracking-wide">FOOTBALL AI</h1>
          <p className="text-[10px] text-muted-foreground">Analyst Platform</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 p-4">
        {navItems.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors",
              pathname === href || (href !== "/" && pathname.startsWith(href))
                ? "bg-primary/10 text-primary"
                : "text-muted-foreground hover:bg-accent hover:text-foreground"
            )}
          >
            <Icon className="h-4 w-4" />
            {label}
          </Link>
        ))}
      </nav>

      <div className="border-t border-border p-4">
        <div className="flex items-center gap-2 rounded-md bg-success/10 px-3 py-2">
          <span className="h-2 w-2 animate-pulse rounded-full bg-success" />
          <span className="text-xs text-success">Sistema Online</span>
        </div>
      </div>
    </aside>
  );
}
