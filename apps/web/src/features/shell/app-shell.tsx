"use client";

import {
  Activity,
  BookOpenText,
  CarFront,
  LogOut,
  Radar,
  Rows3,
  Sparkles,
} from "lucide-react";
import { useState } from "react";

import type { User } from "@/features/auth/types";
import { KnowledgeView } from "@/features/knowledge/knowledge-view";
import { ListingsView } from "@/features/listings/listings-view";
import { OpportunitiesView } from "@/features/opportunities/opportunities-view";
import { StatusView } from "@/features/system/status-view";
import { VehiclesView } from "@/features/vehicles/vehicles-view";

type AppShellProps = {
  user: User;
  onLogout: () => Promise<void>;
  isLoggingOut: boolean;
};

type Tab = "opportunities" | "listings" | "vehicles" | "knowledge" | "status";

const TABS = [
  {
    id: "opportunities",
    label: "Oportunidades",
    hint: "Scoring y Margen",
    icon: Sparkles,
  },
  { id: "listings", label: "Anuncios", hint: "Mercado", icon: Rows3 },
  { id: "vehicles", label: "Vehículos", hint: "Unidades", icon: CarFront },
  {
    id: "knowledge",
    label: "Conocimiento",
    hint: "Fiabilidad",
    icon: BookOpenText,
  },
  { id: "status", label: "Estado", hint: "Sistema", icon: Activity },
] satisfies { id: Tab; label: string; hint: string; icon: typeof Radar }[];

export function AppShell({ user, onLogout, isLoggingOut }: AppShellProps) {
  const [active, setActive] = useState<Tab>("listings");

  return (
    <div className="min-h-dvh bg-[var(--background)] lg:grid lg:grid-cols-[15.5rem_minmax(0,1fr)]">
      <aside className="sticky top-0 z-30 flex flex-wrap items-center border-b border-[var(--border)] bg-[color-mix(in_srgb,var(--background)_94%,transparent)] px-4 backdrop-blur-lg lg:h-dvh lg:flex-col lg:items-stretch lg:border-r lg:border-b-0 lg:bg-[var(--background)] lg:p-4 lg:backdrop-blur-none">
        <div className="flex h-16 items-center gap-2.5 lg:gap-3 lg:px-2">
          <span className="grid h-9 w-9 place-items-center rounded-[0.625rem] bg-[var(--foreground)] shadow-sm lg:h-10 lg:w-10">
            <Radar
              aria-hidden
              size={21}
              className="text-[#9bd2c3]"
              strokeWidth={1.8}
            />
          </span>
          <div>
            <p className="font-display text-lg leading-5 font-semibold tracking-[-0.035em]">
              MotorScope
            </p>
            <p className="mt-0.5 hidden text-[0.625rem] font-bold tracking-[0.12em] text-[var(--muted)] uppercase lg:block">
              Mesa de análisis
            </p>
          </div>
        </div>

        <div className="mt-5 hidden items-center gap-2 px-3 text-[0.6875rem] font-semibold text-[var(--muted)] lg:flex">
          <Radar aria-hidden size={14} />
          OPERACIONES
        </div>
        <nav
          aria-label="Secciones"
          className="order-3 -mx-2 flex w-[calc(100%+1rem)] overflow-x-auto border-t border-[var(--border)] px-2 lg:order-none lg:mx-0 lg:mt-2 lg:w-full lg:flex-col lg:gap-1 lg:overflow-visible lg:border-0 lg:px-0"
        >
          {TABS.map((tab) => {
            const Icon = tab.icon;
            const selected = active === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActive(tab.id)}
                aria-current={selected ? "page" : undefined}
                aria-label={tab.label}
                className={`group relative inline-flex min-h-12 shrink-0 items-center gap-2 px-3 text-xs font-semibold transition-[background-color,color,transform] duration-150 active:scale-[0.99] lg:min-h-14 lg:w-full lg:gap-3 lg:rounded-[var(--radius-card)] lg:text-left ${selected ? "text-[var(--accent)] after:absolute after:inset-x-3 after:bottom-0 after:h-0.5 after:bg-[var(--accent)] lg:bg-[var(--accent-soft)] lg:after:hidden" : "text-[var(--muted)] hover:text-[var(--foreground)] lg:hover:bg-[var(--surface-hover)]"}`}
              >
                <Icon aria-hidden size={18} strokeWidth={1.8} />
                <span className="lg:min-w-0">
                  <span className="block text-xs font-semibold lg:text-sm">
                    {tab.label}
                  </span>
                  <span
                    aria-hidden
                    className={`hidden text-[0.6875rem] font-medium lg:block ${selected ? "text-[var(--accent)]/70" : "text-[var(--muted-soft)]"}`}
                  >
                    {tab.hint}
                  </span>
                </span>
              </button>
            );
          })}
        </nav>

        <div className="ml-auto lg:mt-auto lg:ml-0 lg:border-t lg:border-[var(--border)] lg:pt-4">
          <div className="mb-3 hidden min-w-0 items-center gap-3 px-2 lg:flex">
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-[var(--foreground)] text-xs font-bold text-white uppercase">
              {user.email.slice(0, 2)}
            </span>
            <div className="min-w-0">
              <p className="truncate text-xs font-semibold text-[var(--foreground)]">
                {user.email}
              </p>
              <p className="text-[0.6875rem] text-[var(--muted)]">
                Sesión privada
              </p>
            </div>
          </div>
          <button
            className="grid h-11 w-11 place-items-center rounded-[var(--radius-control)] text-[var(--muted)] transition-colors hover:bg-[var(--surface-hover)] hover:text-[var(--foreground)] disabled:opacity-50 lg:flex lg:w-full lg:justify-start lg:gap-2 lg:px-3 lg:text-xs lg:font-semibold"
            type="button"
            onClick={() => void onLogout()}
            disabled={isLoggingOut}
            aria-label="Cerrar sesión"
          >
            <LogOut aria-hidden size={18} />
            <span className="hidden lg:inline">
              {isLoggingOut ? "Cerrando…" : "Cerrar sesión"}
            </span>
          </button>
        </div>
      </aside>

      <p className="sr-only">Sesión iniciada como {user.email}</p>
      <main className="min-w-0">
        {active === "opportunities" && <OpportunitiesView />}
        {active === "listings" && <ListingsView />}
        {active === "vehicles" && <VehiclesView />}
        {active === "knowledge" && <KnowledgeView />}
        {active === "status" && <StatusView />}
      </main>
    </div>
  );
}
