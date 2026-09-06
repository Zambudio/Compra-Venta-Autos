import Image from "next/image";

import { LoginForm, type LoginValues } from "@/features/auth/login-form";

type LoginScreenProps = {
  onSubmit: (values: LoginValues) => Promise<void>;
  serverError?: string | undefined;
};

export function LoginScreen(props: LoginScreenProps) {
  return (
    <main className="grid min-h-dvh bg-white lg:grid-cols-[minmax(20rem,30%)_1fr]">
      <div className="relative hidden min-h-dvh overflow-hidden bg-[#06131b] lg:block">
        <Image
          src="/images/auth-automotive-panel.png"
          alt=""
          fill
          priority
          sizes="30vw"
          className="object-cover object-center"
        />
      </div>
      <section className="flex min-h-dvh items-center px-6 py-12 sm:px-12 lg:px-20">
        <div className="w-full max-w-[27rem]">
          <p className="text-[1.75rem] leading-8 font-bold tracking-[-0.03em] text-[var(--accent)]">
            MotorScope
          </p>
          <h1 className="mt-10 text-[2rem] leading-[2.375rem] font-semibold tracking-[-0.025em]">
            Acceso privado
          </h1>
          <p className="mt-3 max-w-[24rem] text-base leading-6 text-[var(--muted)]">
            Gestiona tus oportunidades de vehículos con criterio y trazabilidad.
          </p>
          <LoginForm {...props} />
        </div>
      </section>
    </main>
  );
}
