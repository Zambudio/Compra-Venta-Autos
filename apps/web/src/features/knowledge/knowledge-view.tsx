import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  BookOpen,
  CheckCircle2,
  Cpu,
  Layers,
  ShieldCheck,
} from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import {
  getClassifications,
  getEngines,
  getGenerations,
  getKnownIssues,
  getManufacturers,
  getModels,
} from "./api";
import {
  CLASSIFICATION_LABELS,
  classificationBadgeTone,
  COMPONENT_LABELS,
  SEVERITY_LABELS,
} from "./format";
import { KnownIssueCard } from "./known-issue-card";
import type {
  Engine,
  Manufacturer,
  VehicleGeneration,
  VehicleModel,
} from "./types";

type KnowledgeTab = "issues" | "classifications" | "catalog";

export function KnowledgeView() {
  const [activeTab, setActiveTab] = useState<KnowledgeTab>("issues");

  // Filtros de problemas conocidos
  const [selectedComponent, setSelectedComponent] = useState<string>("");
  const [selectedSeverity, setSelectedSeverity] = useState<string>("");

  // Filtros de clasificaciones
  const [selectedClassificationStatus, setSelectedClassificationStatus] =
    useState<string>("");

  // Catálogo jerárquico
  const [selectedManufacturerId, setSelectedManufacturerId] =
    useState<string>("");
  const [selectedModelId, setSelectedModelId] = useState<string>("");

  // Consultas
  const { data: issuesPage, isLoading: isLoadingIssues } = useQuery({
    queryKey: ["known-issues", selectedComponent, selectedSeverity],
    queryFn: () =>
      getKnownIssues({
        component: selectedComponent || undefined,
        severity: selectedSeverity || undefined,
        status: "VERIFIED", // Mostrar por defecto problemas con evidencias trazables (Plan Maestro §15)
        pageSize: 50,
      }),
    enabled: activeTab === "issues",
  });

  const { data: classificationsPage, isLoading: isLoadingClassifications } =
    useQuery({
      queryKey: ["classifications", selectedClassificationStatus],
      queryFn: () =>
        getClassifications({
          status: selectedClassificationStatus || undefined,
          pageSize: 50,
        }),
      enabled: activeTab === "classifications",
    });

  const { data: manufacturers } = useQuery<Manufacturer[]>({
    queryKey: ["manufacturers"],
    queryFn: getManufacturers,
    enabled: activeTab === "catalog",
  });

  const { data: models } = useQuery<VehicleModel[]>({
    queryKey: ["models", selectedManufacturerId],
    queryFn: () => getModels(selectedManufacturerId || undefined),
    enabled: activeTab === "catalog" && Boolean(selectedManufacturerId),
  });

  const { data: generations } = useQuery<VehicleGeneration[]>({
    queryKey: ["generations", selectedModelId],
    queryFn: () => getGenerations(selectedModelId || undefined),
    enabled: activeTab === "catalog" && Boolean(selectedModelId),
  });

  const { data: engines } = useQuery<Engine[]>({
    queryKey: ["engines", selectedManufacturerId],
    queryFn: () =>
      getEngines({ manufacturerId: selectedManufacturerId || undefined }),
    enabled: activeTab === "catalog" && Boolean(selectedManufacturerId),
  });

  return (
    <div className="page-frame flex flex-col gap-7">
      {/* Cabecera */}
      <div className="flex items-start gap-4">
        <span className="mt-1 hidden h-11 w-11 shrink-0 place-items-center rounded-[var(--radius-card)] bg-[var(--accent-soft)] text-[var(--accent)] sm:grid">
          <BookOpen aria-hidden size={21} />
        </span>
        <div>
          <p className="eyebrow">Taller / Evidencia</p>
          <h1 className="page-title mt-1">
            Base de Conocimiento Técnico y Fiabilidad
          </h1>
          <p className="mt-2 max-w-3xl text-sm text-[var(--muted)]">
            Evidencias mecánicas trazables de fuentes oficiales, estadísticas
            independientes y literatura técnica. Ninguna decisión se apoya en
            inferencias no verificadas.
          </p>
        </div>
      </div>

      {/* Navegación interna */}
      <nav
        aria-label="Subsecciones de conocimiento"
        className="flex self-start overflow-x-auto rounded-[0.625rem] bg-[var(--surface-inset)] p-1"
      >
        <button
          type="button"
          onClick={() => setActiveTab("issues")}
          aria-current={activeTab === "issues" ? "page" : undefined}
          className={`flex min-h-10 shrink-0 items-center gap-2 rounded-[var(--radius-control)] px-3.5 text-xs font-semibold transition-[background-color,color,box-shadow] ${
            activeTab === "issues"
              ? "bg-[var(--surface-raised)] text-[var(--foreground)] shadow-sm"
              : "text-[var(--muted)] hover:text-[var(--foreground)]"
          }`}
        >
          <AlertTriangle aria-hidden size={16} />
          Problemas Conocidos y Averías
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("classifications")}
          aria-current={activeTab === "classifications" ? "page" : undefined}
          className={`flex min-h-10 shrink-0 items-center gap-2 rounded-[var(--radius-control)] px-3.5 text-xs font-semibold transition-[background-color,color,box-shadow] ${
            activeTab === "classifications"
              ? "bg-[var(--surface-raised)] text-[var(--foreground)] shadow-sm"
              : "text-[var(--muted)] hover:text-[var(--foreground)]"
          }`}
        >
          <ShieldCheck aria-hidden size={16} />
          Clasificaciones (White / Watch / Blacklist)
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("catalog")}
          aria-current={activeTab === "catalog" ? "page" : undefined}
          className={`flex min-h-10 shrink-0 items-center gap-2 rounded-[var(--radius-control)] px-3.5 text-xs font-semibold transition-[background-color,color,box-shadow] ${
            activeTab === "catalog"
              ? "bg-[var(--surface-raised)] text-[var(--foreground)] shadow-sm"
              : "text-[var(--muted)] hover:text-[var(--foreground)]"
          }`}
        >
          <Cpu aria-hidden size={16} />
          Catálogo Mecánico Canónico
        </button>
      </nav>

      {/* Pestaña: Problemas Conocidos */}
      {activeTab === "issues" && (
        <section
          aria-labelledby="issues-heading"
          className="flex flex-col gap-5"
        >
          <div className="workbench-panel flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between sm:p-5">
            <h2 id="issues-heading" className="section-title">
              Averías y Defectos Sistémicos Verificados
            </h2>

            {/* Filtros */}
            <div className="flex flex-wrap items-center gap-3">
              <label htmlFor="component-filter" className="sr-only">
                Filtrar por componente
              </label>
              <select
                id="component-filter"
                value={selectedComponent}
                onChange={(e) => setSelectedComponent(e.target.value)}
                className="min-h-10 rounded-[var(--radius-control)] border border-[var(--control-border)] bg-[var(--control-bg)] px-3 text-xs font-medium text-[var(--foreground)] outline-none focus:border-[var(--accent)] focus:ring-4 focus:ring-[var(--focus-ring)]"
              >
                <option value="">Todos los componentes</option>
                {Object.entries(COMPONENT_LABELS).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v}
                  </option>
                ))}
              </select>

              <label htmlFor="severity-filter" className="sr-only">
                Filtrar por severidad
              </label>
              <select
                id="severity-filter"
                value={selectedSeverity}
                onChange={(e) => setSelectedSeverity(e.target.value)}
                className="min-h-10 rounded-[var(--radius-control)] border border-[var(--control-border)] bg-[var(--control-bg)] px-3 text-xs font-medium text-[var(--foreground)] outline-none focus:border-[var(--accent)] focus:ring-4 focus:ring-[var(--focus-ring)]"
              >
                <option value="">Todas las severidades</option>
                {Object.entries(SEVERITY_LABELS).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {isLoadingIssues ? (
            <div className="flex min-h-[200px] items-center justify-center">
              <p className="text-sm text-[var(--muted)]">
                Cargando base de averías conocidas…
              </p>
            </div>
          ) : issuesPage && issuesPage.items.length > 0 ? (
            <div className="flex flex-col gap-4">
              {issuesPage.items.map((issue) => (
                <KnownIssueCard key={issue.id} issue={issue} />
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <CheckCircle2
                aria-hidden
                size={32}
                className="text-[var(--success)]"
              />
              <p className="text-sm font-medium text-[var(--foreground)]">
                No hay problemas registrados con los filtros seleccionados.
              </p>
              <p className="text-xs text-[var(--muted)]">
                Intente seleccionar otro componente o severidad.
              </p>
            </div>
          )}
        </section>
      )}

      {/* Pestaña: Clasificaciones de Mercado */}
      {activeTab === "classifications" && (
        <section
          aria-labelledby="classifications-heading"
          className="flex flex-col gap-5"
        >
          <div className="workbench-panel flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between sm:p-5">
            <div>
              <h2
                id="classifications-heading"
                className="text-base font-bold text-[var(--foreground)]"
              >
                Clasificación de Modelos y Motores
              </h2>
              <p className="text-xs text-[var(--muted)]">
                Categorización auditable y justificada de combinaciones
                mecánicas.
              </p>
            </div>

            <label htmlFor="classification-status-filter" className="sr-only">
              Filtrar por estatus
            </label>
            <select
              id="classification-status-filter"
              value={selectedClassificationStatus}
              onChange={(e) => setSelectedClassificationStatus(e.target.value)}
              className="min-h-10 rounded-[var(--radius-control)] border border-[var(--control-border)] bg-[var(--control-bg)] px-3 text-xs font-medium text-[var(--foreground)] outline-none focus:border-[var(--accent)] focus:ring-4 focus:ring-[var(--focus-ring)]"
            >
              <option value="">Todos los estatus</option>
              <option value="WHITELIST">Lista Blanca (Recomendados)</option>
              <option value="WATCHLIST">Bajo Observación (Precaución)</option>
              <option value="BLACKLIST">Lista Negra (Desaconsejados)</option>
            </select>
          </div>

          {isLoadingClassifications ? (
            <div className="flex min-h-[200px] items-center justify-center">
              <p className="text-sm text-[var(--muted)]">
                Cargando clasificaciones…
              </p>
            </div>
          ) : classificationsPage && classificationsPage.items.length > 0 ? (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {classificationsPage.items.map((cls) => {
                const tone = classificationBadgeTone(cls.status);
                return (
                  <article
                    key={cls.id}
                    className="flex flex-col justify-between gap-3 rounded-[var(--radius-card)] border border-[var(--border)] bg-[var(--surface-raised)] p-5 shadow-[var(--shadow-card)]"
                  >
                    <div className="flex flex-col gap-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold tracking-wider text-[var(--muted)] uppercase">
                          Objetivo: {cls.target_type}
                        </span>
                        <Badge tone={tone}>
                          {CLASSIFICATION_LABELS[cls.status]}
                        </Badge>
                      </div>
                      <p className="text-sm font-medium text-[var(--foreground)]">
                        {cls.rationale}
                      </p>
                    </div>
                    <span className="text-[0.75rem] text-[var(--muted)]">
                      ID Objetivo: {cls.target_id}
                    </span>
                  </article>
                );
              })}
            </div>
          ) : (
            <div className="empty-state">
              <p className="text-sm font-medium text-[var(--foreground)]">
                No hay clasificaciones con el filtro seleccionado.
              </p>
            </div>
          )}
        </section>
      )}

      {/* Pestaña: Catálogo Mecánico Canónico */}
      {activeTab === "catalog" && (
        <section
          aria-labelledby="catalog-heading"
          className="flex flex-col gap-6"
        >
          <div className="workbench-panel p-5">
            <h2
              id="catalog-heading"
              className="mb-1 text-base font-bold text-[var(--foreground)]"
            >
              Jerarquía Técnica Canónica
            </h2>
            <p className="mb-4 text-xs text-[var(--muted)]">
              Seleccione un fabricante para explorar sus modelos, generaciones y
              motores asociados.
            </p>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label
                  htmlFor="catalog-mfg-select"
                  className="mb-1 block text-xs font-semibold"
                >
                  1. Fabricante / Marca:
                </label>
                <select
                  id="catalog-mfg-select"
                  value={selectedManufacturerId}
                  onChange={(e) => {
                    setSelectedManufacturerId(e.target.value);
                    setSelectedModelId("");
                  }}
                  className="min-h-11 w-full rounded-[var(--radius-control)] border border-[var(--control-border)] bg-[var(--control-bg)] px-3 text-sm outline-none focus:border-[var(--accent)] focus:ring-4 focus:ring-[var(--focus-ring)]"
                >
                  <option value="">Seleccione marca…</option>
                  {manufacturers?.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name} {m.country ? `(${m.country})` : ""}
                    </option>
                  ))}
                </select>
              </div>

              {selectedManufacturerId && (
                <div>
                  <label
                    htmlFor="catalog-model-select"
                    className="mb-1 block text-xs font-semibold"
                  >
                    2. Modelo:
                  </label>
                  <select
                    id="catalog-model-select"
                    value={selectedModelId}
                    onChange={(e) => setSelectedModelId(e.target.value)}
                    className="min-h-11 w-full rounded-[var(--radius-control)] border border-[var(--control-border)] bg-[var(--control-bg)] px-3 text-sm outline-none focus:border-[var(--accent)] focus:ring-4 focus:ring-[var(--focus-ring)]"
                  >
                    <option value="">Seleccione modelo…</option>
                    {models?.map((mod) => (
                      <option key={mod.id} value={mod.id}>
                        {mod.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          </div>

          {/* Motores del fabricante */}
          {selectedManufacturerId && engines && engines.length > 0 && (
            <div className="workbench-panel flex flex-col gap-3 p-5">
              <h3 className="flex items-center gap-2 text-sm font-bold text-[var(--foreground)]">
                <Cpu aria-hidden size={16} /> Motores Registrados (
                {engines.length})
              </h3>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-3">
                {engines.map((eng) => (
                  <div
                    key={eng.id}
                    className="flex flex-col gap-1 rounded border border-[var(--border)] bg-[var(--surface)] p-3 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-bold text-[var(--foreground)]">
                        {eng.name}
                      </span>
                      <Badge tone="neutral">{eng.family_code}</Badge>
                    </div>
                    <p className="text-[var(--muted)]">
                      Combustible: {eng.fuel_type} • Aspiración:{" "}
                      {eng.aspiration}
                      {eng.displacement_cc && ` • ${eng.displacement_cc} cc`}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Generaciones del modelo seleccionado */}
          {selectedModelId && generations && generations.length > 0 && (
            <div className="workbench-panel flex flex-col gap-3 p-5">
              <h3 className="flex items-center gap-2 text-sm font-bold text-[var(--foreground)]">
                <Layers aria-hidden size={16} /> Generaciones Documentadas
              </h3>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {generations.map((gen) => (
                  <div
                    key={gen.id}
                    className="flex flex-col gap-1 rounded border border-[var(--border)] bg-[var(--surface)] p-3 text-xs"
                  >
                    <span className="text-sm font-bold text-[var(--foreground)]">
                      {gen.name}
                    </span>
                    <p className="text-[var(--muted)]">
                      Años de producción: {gen.year_start} –{" "}
                      {gen.year_end ?? "presente"}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
