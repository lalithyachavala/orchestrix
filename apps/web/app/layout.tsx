import "./globals.css";
import type { Metadata } from "next";
import Sidebar from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "Orchestrix — AI Agent & Workflow Orchestration",
  description: "Build, run, and monitor AI agents that use tools to execute business tasks.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="flex h-screen flex-col overflow-hidden">
          <div className="shrink-0 border-b border-edge bg-warn/10 px-4 py-1.5 text-center text-xs text-warn">
            Public demo · synthetic data · keyless mock agents. Illustrative engineering artifact — not a real product, not affiliated with any company.
          </div>
          <div className="flex min-h-0 flex-1 overflow-hidden">
            <Sidebar />
            <main className="flex-1 overflow-y-auto">{children}</main>
          </div>
        </div>
      </body>
    </html>
  );
}
