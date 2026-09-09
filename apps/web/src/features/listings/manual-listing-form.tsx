"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { createManualListing } from "@/features/listings/api";
import {
  FUEL_LABELS,
  SELLER_LABELS,
  TRANSMISSION_LABELS,
} from "@/features/listings/format";
import type { ManualListingInput } from "@/features/listings/types";
import { ApiError } from "@/lib/api";

const currentYear = new Date().getFullYear();

const schema = z.object({
  url: z.string().url("Introduce una URL válida.").optional().or(z.literal("")),
  brand: z.string().min(1, "La marca es obligatoria."),
  model: z.string().min(1, "El modelo es obligatorio."),
  trim: z.string().optional(),
  year: z.coerce
    .number()
    .int()
    .min(1950, "Año no válido.")
    .max(currentYear + 1, "Año no válido."),
  mileage_km: z.coerce.number().int().min(0, "Kilometraje no válido."),
  price_amount: z
    .string()
    .regex(/^\d+(\.\d{1,2})?$/, "Introduce un importe válido en euros."),
  fuel_type: z.enum([
    "PETROL",
    "DIESEL",
    "LPG",
    "CNG",
    "HYBRID",
    "PLUGIN_HYBRID",
    "ELECTRIC",
    "OTHER",
  ]),
  transmission: z.enum(["MANUAL", "AUTOMATIC", "UNKNOWN"]),
  seller_type: z.enum(["PRIVATE", "DEALER", "UNKNOWN"]),
  province: z.string().optional(),
  description: z.string().max(5000).optional(),
});

type FormValues = z.input<typeof schema>;

type ManualListingFormProps = {
  onCreated: () => void;
  onCancel: () => void;
};

export function ManualListingForm({
  onCreated,
  onCancel,
}: ManualListingFormProps) {
  const queryClient = useQueryClient();
  const [serverError, setServerError] = useState<string>();
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      fuel_type: "OTHER",
      transmission: "UNKNOWN",
      seller_type: "PRIVATE",
    },
  });

  const mutation = useMutation({
    mutationFn: createManualListing,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["listings"] });
      onCreated();
    },
  });

  async function submit(values: FormValues) {
    setServerError(undefined);
    const parsed = schema.parse(values);
    const payload: ManualListingInput = {
      brand: parsed.brand,
      model: parsed.model,
      year: parsed.year,
      mileage_km: parsed.mileage_km,
      price_amount: parsed.price_amount,
      fuel_type: parsed.fuel_type,
      transmission: parsed.transmission,
      seller_type: parsed.seller_type,
      ...(parsed.url ? { url: parsed.url } : {}),
      ...(parsed.trim ? { trim: parsed.trim } : {}),
      ...(parsed.province ? { province: parsed.province } : {}),
      ...(parsed.description ? { description: parsed.description } : {}),
    };
    try {
      await mutation.mutateAsync(payload);
    } catch (error) {
      setServerError(
        error instanceof ApiError && error.code === "listing_already_exists"
          ? "Ese vehículo ya está registrado manualmente."
          : "No se pudo registrar el vehículo. Revisa los datos e inténtalo de nuevo.",
      );
    }
  }

  return (
    <form
      className="grid gap-4 sm:grid-cols-2"
      aria-label="Registrar vehículo manualmente"
      noValidate
      onSubmit={handleSubmit(submit)}
    >
      <Field id="manual-brand" label="Marca" error={errors.brand?.message}>
        {(p) => <Input {...p} {...register("brand")} />}
      </Field>
      <Field id="manual-model" label="Modelo" error={errors.model?.message}>
        {(p) => <Input {...p} {...register("model")} />}
      </Field>
      <Field id="manual-trim" label="Versión" error={errors.trim?.message}>
        {(p) => <Input {...p} {...register("trim")} />}
      </Field>
      <Field id="manual-year" label="Año" error={errors.year?.message}>
        {(p) => <Input inputMode="numeric" {...p} {...register("year")} />}
      </Field>
      <Field
        id="manual-mileage"
        label="Kilometraje"
        error={errors.mileage_km?.message}
      >
        {(p) => (
          <Input inputMode="numeric" {...p} {...register("mileage_km")} />
        )}
      </Field>
      <Field
        id="manual-price"
        label="Precio (€)"
        error={errors.price_amount?.message}
        hint="Solo el número, por ejemplo 2800"
      >
        {(p) => (
          <Input inputMode="decimal" {...p} {...register("price_amount")} />
        )}
      </Field>
      <Field
        id="manual-fuel"
        label="Combustible"
        error={errors.fuel_type?.message}
      >
        {(p) => (
          <Select {...p} {...register("fuel_type")}>
            {Object.entries(FUEL_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
        )}
      </Field>
      <Field
        id="manual-transmission"
        label="Cambio"
        error={errors.transmission?.message}
      >
        {(p) => (
          <Select {...p} {...register("transmission")}>
            {Object.entries(TRANSMISSION_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
        )}
      </Field>
      <Field
        id="manual-seller"
        label="Vendedor"
        error={errors.seller_type?.message}
      >
        {(p) => (
          <Select {...p} {...register("seller_type")}>
            {Object.entries(SELLER_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
        )}
      </Field>
      <Field
        id="manual-province"
        label="Provincia"
        error={errors.province?.message}
      >
        {(p) => <Input {...p} {...register("province")} />}
      </Field>
      <Field
        id="manual-url"
        label="URL del anuncio"
        error={errors.url?.message}
      >
        {(p) => <Input inputMode="url" {...p} {...register("url")} />}
      </Field>
      <div className="sm:col-span-2">
        <Field
          id="manual-description"
          label="Observaciones"
          error={errors.description?.message}
        >
          {(p) => (
            <textarea
              className="min-h-28 w-full resize-y rounded-[var(--radius-control)] border border-[var(--control-border)] bg-[var(--control-bg)] px-3.5 py-3 text-sm transition-[background-color,border-color,box-shadow] outline-none focus:border-[var(--accent)] focus:bg-[var(--surface-raised)] focus:ring-4 focus:ring-[var(--focus-ring)]"
              {...p}
              {...register("description")}
            />
          )}
        </Field>
      </div>

      {serverError ? (
        <p className="text-sm text-[var(--danger)] sm:col-span-2" role="alert">
          {serverError}
        </p>
      ) : null}

      <div className="flex items-center gap-3 sm:col-span-2">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Guardando…" : "Registrar vehículo"}
        </Button>
        <button
          type="button"
          className="min-h-11 px-2 text-sm text-[var(--muted)] hover:text-[var(--foreground)]"
          onClick={onCancel}
        >
          Cancelar
        </button>
      </div>
    </form>
  );
}
