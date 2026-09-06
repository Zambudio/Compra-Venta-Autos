"use client";

import { useQuery } from "@tanstack/react-query";
import { LogOut } from "lucide-react";

import { getSystemStatus } from "@/features/auth/api";
import type { User } from "@/features/auth/types";

type StatusScreenProps = {
  user: User;
  onLogout: () => Promise<void>;
  isLoggingOut: boolean;
};

export function StatusScreen({
  user,
  onLogout,
  isLoggingOut,
}: StatusScreenProps) {
  const status = useQuery({
    queryKey: ["system-status"],
    queryFn: getSystemStatus,
  });
  const rows = [
    ["API", status.data?.api === "available" ? "Disponible" : "Comprobando"],
    [
      "PostgreSQL",
      status.data?.postgresql === "available" ? "Disponible" : "Comprobando",
    ],
    ["Redis", status.data?.redis === "ready" ? "Preparado" : "Comprobando"],
  ] as const;

  return (
    <main className="min-h-dvh bg-white">
      <header className="border-b border-[var(--border)]">
        <div className="mx-auto flex min-h-20 max-w-6xl items-center px-6 sm:px-10">
          <p className="text-2xl font-bold tracking-[-0.03em] text-[var(--accent)]">
            MotorScope
          </p>
          <nav aria-label="Navegación principal" className="ml-12 self-stretch">
            <span className="flex h-full items-center border-b-2 border-[var(--accent)] px-2 text-[0.9375rem]">
              Estado
            </span>
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

      <section className="mx-auto max-w-5xl px-6 py-14 sm:px-10 sm:py-20">
        <h1 className="text-[2rem] leading-[2.375rem] font-semibold tracking-[-0.025em]">
          Foundation operativa
        </h1>
        <p className="sr-only">Sesión iniciada como {user.email}</p>
        {status.isError ? (
          <p
            className="mt-8 border-l-2 border-[var(--danger)] py-1 pl-4 text-sm text-[var(--danger)]"
            role="alert"
          >
            No se pudo comprobar el estado del sistema.
          </p>
        ) : (
          <dl className="mt-8 border-t border-[var(--border)]">
            {rows.map(([name, value]) => {
              const isReady = value === "Disponible" || value === "Preparado";
              return (
                <div
                  key={name}
                  className="grid min-h-16 grid-cols-[1fr_auto] items-center gap-6 border-b border-[var(--border)] px-3"
                >
                  <dt>{name}</dt>
                  <dd className="flex items-center gap-3 text-[var(--muted)]">
                    <span
                      className={`h-2 w-2 rounded-full ${isReady ? "bg-[var(--success)]" : "bg-[var(--muted)]"}`}
                      aria-hidden
                    />
                    {value}
                  </dd>
                </div>
              );
            })}
          </dl>
        )}
        <p className="mt-4 text-sm text-[var(--muted)]">
          Las funciones de búsqueda se habilitarán en la siguiente fase.
        </p>
      </section>
    </main>
  );
}
