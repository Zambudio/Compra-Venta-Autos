"use client";

import { useQuery } from "@tanstack/react-query";

import { getSystemStatus } from "@/features/auth/api";

export function StatusView() {
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
    <section className="mx-auto max-w-3xl px-6 py-12 sm:px-10">
      <h1 className="text-[1.75rem] leading-9 font-semibold tracking-[-0.025em]">
        Foundation operativa
      </h1>
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
    </section>
  );
}
