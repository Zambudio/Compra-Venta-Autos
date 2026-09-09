import { Gauge, SearchCheck, ShieldCheck } from "lucide-react";
import Image from "next/image";

import { LoginForm, type LoginValues } from "@/features/auth/login-form";

type LoginScreenProps = {
  onSubmit: (values: LoginValues) => Promise<void>;
  serverError?: string | undefined;
};

export function LoginScreen(props: LoginScreenProps) {
  return (
    <main className="grid min-h-dvh bg-[var(--background)] lg:grid-cols-[minmax(28rem,46%)_1fr]">
      <div className="absolute top-6 left-5 z-20 flex items-center gap-3 text-[var(--foreground)] sm:left-12 lg:top-10 lg:left-10 lg:text-white xl:top-14 xl:left-14">
        <span className="grid h-11 w-11 place-items-center rounded-[0.75rem] bg-[var(--foreground)] shadow-sm ring-1 ring-black/5 lg:bg-white/10 lg:ring-white/15 lg:backdrop-blur-sm">
          <Gauge
            aria-hidden
            size={22}
            className="text-[#a8d8ca]"
            strokeWidth={1.8}
          />
        </span>
        <div>
          <p className="font-display text-xl font-semibold tracking-[-0.035em]">
            MotorScope
          </p>
          <p className="hidden text-[0.625rem] font-bold tracking-[0.13em] text-white/55 uppercase lg:block">
            Intelligence desk
          </p>
        </div>
      </div>
      <section className="relative hidden min-h-dvh overflow-hidden bg-[var(--foreground)] lg:flex lg:flex-col lg:justify-between lg:p-10 xl:p-14">
        <Image
          src="/images/auth-automotive-panel.png"
          alt=""
          fill
          priority
          sizes="46vw"
          className="object-cover object-center opacity-70"
        />
        <div className="absolute inset-0 bg-[#101816]/35" aria-hidden />

        <div aria-hidden />
        <div className="relative z-10 max-w-xl text-white">
          <p className="text-xs font-bold tracking-[0.13em] text-[#a8d8ca] uppercase">
            Decisiones con evidencia
          </p>
          <h2 className="font-display mt-4 text-4xl leading-[1.08] font-semibold tracking-[-0.04em] text-balance xl:text-5xl">
            Del anuncio disperso a una oportunidad entendible.
          </h2>
          <p className="mt-5 max-w-lg text-base leading-7 text-white/68">
            Mercado, historial y fiabilidad mecánica reunidos en una mesa de
            análisis privada.
          </p>
          <div className="mt-8 grid grid-cols-3 gap-3">
            {[
              { icon: SearchCheck, label: "Captura", value: "Trazable" },
              { icon: Gauge, label: "Valoración", value: "Objetiva" },
              { icon: ShieldCheck, label: "Riesgo", value: "Explicable" },
            ].map(({ icon: Icon, label, value }) => (
              <div
                key={label}
                className="rounded-[0.75rem] bg-white/7 p-3.5 ring-1 ring-white/10 backdrop-blur-sm"
              >
                <Icon aria-hidden size={17} className="text-[#a8d8ca]" />
                <p className="mt-3 text-[0.625rem] font-bold tracking-[0.1em] text-white/45 uppercase">
                  {label}
                </p>
                <p className="mt-0.5 text-sm font-semibold">{value}</p>
              </div>
            ))}
          </div>
        </div>

        <p className="relative z-10 text-xs text-white/45">
          Plataforma privada · Acceso auditado
        </p>
      </section>

      <section className="flex min-h-dvh items-center justify-center px-5 py-12 sm:px-12 lg:px-16">
        <div className="w-full max-w-[27rem]">
          <p className="eyebrow mt-12 lg:mt-0">Área de operaciones</p>
          <h1 className="page-title mt-2 text-[2.25rem]">Acceso privado</h1>
          <p className="mt-3 max-w-[24rem] text-base leading-6 text-[var(--muted)]">
            Gestiona tus oportunidades de vehículos con criterio y trazabilidad.
          </p>
          <div className="workbench-panel mt-8 p-5 sm:p-6">
            <LoginForm {...props} />
          </div>
          <p className="mt-5 text-center text-xs text-[var(--muted)]">
            Sólo personal autorizado
          </p>
        </div>
      </section>
    </main>
  );
}
