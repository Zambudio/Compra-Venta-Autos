"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { FUEL_LABELS } from "@/features/listings/format";
import type { FuelType, ListingFilters } from "@/features/listings/types";

const numeric = z
  .string()
  .refine((value) => value === "" || Number.isFinite(Number(value)), {
    message: "Introduce un número válido.",
  });

const schema = z
  .object({
    brand: z.string(),
    model: z.string(),
    year_min: numeric,
    year_max: numeric,
    price_max: numeric,
    mileage_max: numeric,
    province: z.string(),
    fuel_type: z.string(),
    sort: z.enum(["newest", "price_asc", "price_desc"]),
  })
  .refine(
    (v) =>
      !v.year_min || !v.year_max || Number(v.year_min) <= Number(v.year_max),
    {
      path: ["year_max"],
      message: "El año máximo no puede ser menor que el mínimo.",
    },
  );

type FilterValues = z.infer<typeof schema>;

const EMPTY: FilterValues = {
  brand: "",
  model: "",
  year_min: "",
  year_max: "",
  price_max: "",
  mileage_max: "",
  province: "",
  fuel_type: "",
  sort: "newest",
};

type FilterFormProps = {
  onApply: (filters: ListingFilters) => void;
};

function num(value: string): number | undefined {
  return value ? Number(value) : undefined;
}

function str(value: string): string | undefined {
  return value.trim() || undefined;
}

export function FilterForm({ onApply }: FilterFormProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FilterValues>({
    resolver: zodResolver(schema),
    defaultValues: EMPTY,
  });

  function submit(values: FilterValues) {
    const filters: ListingFilters = { page: 1, sort: values.sort };
    const brand = str(values.brand);
    const model = str(values.model);
    const province = str(values.province);
    const yearMin = num(values.year_min);
    const yearMax = num(values.year_max);
    const priceMax = num(values.price_max);
    const mileageMax = num(values.mileage_max);
    if (brand) filters.brand = brand;
    if (model) filters.model = model;
    if (province) filters.province = province;
    if (yearMin !== undefined) filters.year_min = yearMin;
    if (yearMax !== undefined) filters.year_max = yearMax;
    if (priceMax !== undefined) filters.price_max = priceMax;
    if (mileageMax !== undefined) filters.mileage_max = mileageMax;
    if (values.fuel_type) filters.fuel_type = values.fuel_type as FuelType;
    onApply(filters);
  }

  return (
    <form
      className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
      aria-label="Filtros de anuncios"
      onSubmit={handleSubmit(submit)}
    >
      <Field id="filter-brand" label="Marca">
        {(p) => <Input placeholder="SEAT" {...p} {...register("brand")} />}
      </Field>
      <Field id="filter-model" label="Modelo">
        {(p) => <Input placeholder="Ibiza" {...p} {...register("model")} />}
      </Field>
      <Field id="filter-province" label="Provincia">
        {(p) => <Input placeholder="Murcia" {...p} {...register("province")} />}
      </Field>
      <Field
        id="filter-year-min"
        label="Año desde"
        error={errors.year_min?.message}
      >
        {(p) => <Input inputMode="numeric" {...p} {...register("year_min")} />}
      </Field>
      <Field
        id="filter-year-max"
        label="Año hasta"
        error={errors.year_max?.message}
      >
        {(p) => <Input inputMode="numeric" {...p} {...register("year_max")} />}
      </Field>
      <Field
        id="filter-price-max"
        label="Precio máximo (€)"
        error={errors.price_max?.message}
      >
        {(p) => <Input inputMode="numeric" {...p} {...register("price_max")} />}
      </Field>
      <Field
        id="filter-mileage-max"
        label="Km máximos"
        error={errors.mileage_max?.message}
      >
        {(p) => (
          <Input inputMode="numeric" {...p} {...register("mileage_max")} />
        )}
      </Field>
      <Field id="filter-fuel" label="Combustible">
        {(p) => (
          <Select {...p} {...register("fuel_type")}>
            <option value="">Todos</option>
            {Object.entries(FUEL_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
        )}
      </Field>
      <Field id="filter-sort" label="Ordenar por">
        {(p) => (
          <Select {...p} {...register("sort")}>
            <option value="newest">Más recientes</option>
            <option value="price_asc">Precio ascendente</option>
            <option value="price_desc">Precio descendente</option>
          </Select>
        )}
      </Field>
      <div className="flex items-end gap-3">
        <Button type="submit">Aplicar filtros</Button>
        <button
          type="button"
          className="min-h-11 px-2 text-sm text-[var(--muted)] hover:text-[var(--foreground)]"
          onClick={() => {
            reset(EMPTY);
            onApply({ sort: "newest", page: 1 });
          }}
        >
          Limpiar
        </button>
      </div>
    </form>
  );
}
