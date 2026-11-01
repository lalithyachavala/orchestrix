"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, Bot, GitBranch, LayoutDashboard, Network } from "lucide-react";

const NAV = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/agents", label: "Agents", icon: Bot },
  { href: "/workflows", label: "Workflow Builder", icon: GitBranch },
  { href: "/executions", label: "Executions", icon: Activity },
  { href: "/multi-agent", label: "Multi-Agent", icon: Network },
];

export default function Sidebar() {
  const path = usePathname();
  return (
    <aside className="flex w-60 shrink-0 flex-col border-r border-edge bg-panel px-3 py-5">
      <div className="px-3 pb-6">
        <div className="flex items-center gap-2 text-lg font-semibold tracking-tight">
          <span className="grid h-7 w-7 place-items-center rounded-lg bg-brand/20 text-brand">◆</span>
          Orchestrix
        </div>
        <div className="mt-1 pl-9 text-xs text-sub">agent orchestration</div>
      </div>
      <nav className="flex flex-col gap-1">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = href === "/" ? path === "/" : path.startsWith(href);
          return (
            <Link key={href} href={href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition ${
                active ? "bg-brand/15 text-brand" : "text-sub hover:bg-panel2 hover:text-ink"}`}>
              <Icon size={17} /> {label}
            </Link>
          );
        })}
      </nav>
      <div className="mt-auto px-3 pt-6 text-[11px] leading-relaxed text-sub">
        Keyless mock adapter · synthetic data. Illustrative demo, not a real product.
      </div>
    </aside>
  );
}
