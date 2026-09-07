"use client";

import { LogOut } from "lucide-react";
import { useState } from "react";

import { KnowledgeView } from "@/features/knowledge/knowledge-view";
import { ListingsView } from "@/features/listings/listings-view";
import { StatusView } from "@/features/system/status-view";
import { VehiclesView } from "@/features/vehicles/vehicles-view";
import type { User } from "@/features/auth/types";

type AppShellProps = {
  user: User;
  onLogout: () => Promise<void>;
  isLoggingOut: boolean;
};

type Tab = "listings" | "vehicles" | "knowledge" | "status";

const TABS: { id: Tab; label: string }[] = [
  { id: "listings", label: "Anuncios" },
  { id: "vehicles", label: "Vehículos" },
  { id: "knowledge", label: "Conocimiento" },
  { id: "status", label: "Estado" },
];

export function AppShell({ user, onLogout, isLoggingOut }: AppShellProps) {
  const [active, setActive] = useState<Tab>("listings");

  return (
    <div className="min-h-dvh bg-white">
      <header className="border-b border-[var(--border)]">
        <div className="mx-auto flex min-h-16 max-w-6xl items-center gap-8 px-6 sm:px-10">
          <p className="text-xl font-bold tracking-[-0.03em] text-[var(--accent)]">
            MotorScope
          </p>
          <nav aria-label="Secciones" className="flex self-stretch">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActive(tab.id)}
                aria-current={active === tab.id ? "page" : undefined}
                className={`flex h-full items-center border-b-2 px-3 text-[0.9375rem] ${
                  active === tab.id
                    ? "border-[var(--accent)] font-medium"
                    : "border-transparent text-[var(--muted)] hover:text-[var(--foreground)]"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
          <button
            className="ml-auto inline-flex min-h-11 items-center gap-2 px-2 text-[0.9375rem] font-medium disabled:opacity-60"
            type="button"
            onClick={() => void onLogout()}
            disabled={isLoggingOut}
          >
            <LogOut aria-hidden size={19} />
            {isLoggingOut ? "Cerrando…" : "Cerrar sesión"}
          </button>
        </div>
      </header>

      <p className="sr-only">Sesión iniciada como {user.email}</p>
      <main>
        {active === "listings" && <ListingsView />}
        {active === "vehicles" && <VehiclesView />}
        {active === "knowledge" && <KnowledgeView />}
        {active === "status" && <StatusView />}
      </main>
    </div>
  );
}
