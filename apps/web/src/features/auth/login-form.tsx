"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Eye, EyeOff, LockKeyhole } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const loginSchema = z.object({
  email: z.string().email("Introduce un correo electrónico válido."),
  password: z
    .string()
    .min(12, "La contraseña debe tener al menos 12 caracteres.")
    .max(128, "La contraseña no puede superar 128 caracteres."),
});

export type LoginValues = z.infer<typeof loginSchema>;

type LoginFormProps = {
  onSubmit: (values: LoginValues) => Promise<void>;
  serverError?: string | undefined;
};

export function LoginForm({ onSubmit, serverError }: LoginFormProps) {
  const [showPassword, setShowPassword] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginValues>({ resolver: zodResolver(loginSchema) });

  return (
    <form
      className="mt-8 space-y-5"
      noValidate
      onSubmit={handleSubmit(onSubmit)}
    >
      <div>
        <label className="mb-1.5 block text-sm font-medium" htmlFor="email">
          Correo electrónico
        </label>
        <Input
          id="email"
          type="email"
          autoComplete="username"
          aria-invalid={Boolean(errors.email)}
          aria-describedby={errors.email ? "email-error" : undefined}
          {...register("email")}
        />
        {errors.email ? (
          <p id="email-error" className="mt-1.5 text-sm text-[var(--danger)]">
            {errors.email.message}
          </p>
        ) : null}
      </div>

      <div>
        <label className="mb-1.5 block text-sm font-medium" htmlFor="password">
          Contraseña
        </label>
        <div className="relative">
          <Input
            id="password"
            type={showPassword ? "text" : "password"}
            autoComplete="current-password"
            className="pr-12"
            aria-invalid={Boolean(errors.password)}
            aria-describedby={errors.password ? "password-error" : undefined}
            {...register("password")}
          />
          <button
            type="button"
            className="absolute inset-y-0 right-0 flex w-11 items-center justify-center text-[var(--muted)] hover:text-[var(--foreground)]"
            aria-label={
              showPassword ? "Ocultar contraseña" : "Mostrar contraseña"
            }
            onClick={() => setShowPassword((visible) => !visible)}
          >
            {showPassword ? (
              <EyeOff aria-hidden size={19} />
            ) : (
              <Eye aria-hidden size={19} />
            )}
          </button>
        </div>
        {errors.password ? (
          <p
            id="password-error"
            className="mt-1.5 text-sm text-[var(--danger)]"
          >
            {errors.password.message}
          </p>
        ) : null}
      </div>

      {serverError ? (
        <p className="text-sm text-[var(--danger)]" role="alert">
          {serverError}
        </p>
      ) : null}

      <Button className="w-full" type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Comprobando…" : "Entrar"}
      </Button>
      <p className="flex items-center gap-2 text-sm text-[var(--muted)]">
        <LockKeyhole aria-hidden size={17} />
        Sesión segura y privada
      </p>
    </form>
  );
}
