"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Check, AlertTriangle, X, Camera, Paperclip, Upload } from "lucide-react";

import { Button } from "@/components/ui/button";

import type { InspectionWithDetails, CheckResult } from "./types";
import { addInspectionCheck, updateCheckResult, getInspectionFiles, uploadInspectionFile, updateInspectionStatus } from "./api";

const PREDEFINED_CATEGORIES = [
  "Motor y TransmisiÃ³n",
  "CarrocerÃ­a y Pintura",
  "Interior y ElectrÃ³nica",
  "Frenos y SuspensiÃ³n",
  "NeumÃ¡ticos",
  "DocumentaciÃ³n"
];

export function InspectionDetail({
  inspection,
  onBack,
}: {
  inspection: InspectionWithDetails;
  onBack: () => void;
}) {
  const queryClient = useQueryClient();
  const [isUploading, setIsUploading] = useState(false);

  const { data: files } = useQuery({
    queryKey: ["inspection-files", inspection.id],
    queryFn: () => getInspectionFiles(inspection.id),
  });

  const checkMutation = useMutation({
    mutationFn: (data: { category: string; name: string }) => 
      addInspectionCheck(inspection.id, data.category, data.name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inspections", inspection.watchlist_entry_id] });
    }
  });

  const updateResultMutation = useMutation({
    mutationFn: (data: { checkId: string; result: CheckResult }) =>
      updateCheckResult(data.checkId, data.result),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inspections", inspection.watchlist_entry_id] });
    }
  });

  const finishMutation = useMutation({
    mutationFn: () => updateInspectionStatus(inspection.id, "COMPLETED"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inspections", inspection.watchlist_entry_id] });
    }
  });

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setIsUploading(true);
    try {
      await uploadInspectionFile(inspection.id, file);
      queryClient.invalidateQueries({ queryKey: ["inspection-files", inspection.id] });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center gap-3 border-b border-[var(--border)] p-4">
        <Button variant="ghost" size="icon" onClick={onBack} aria-label="Volver">
          <ArrowLeft size={20} />
        </Button>
        <div className="min-w-0 flex-1">
          <h2 className="truncate font-semibold text-[var(--foreground)]">
            Detalle de InspecciÃ³n
          </h2>
          <p className="text-xs text-[var(--muted)]">
            Estado: {inspection.status} &bull; Inspector: {inspection.inspector_name || "N/A"}
          </p>
        </div>
        {inspection.status !== "COMPLETED" && (
          <Button size="compact" onClick={() => finishMutation.mutate()} disabled={finishMutation.isPending}>
            Completar
          </Button>
        )}
      </header>

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        
        {/* Checklist */}
        <section>
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-[var(--foreground)]">Checklist</h3>
          </div>
          
          <div className="space-y-4">
            {PREDEFINED_CATEGORIES.map(category => {
              const checks = inspection.checks.filter(c => c.category === category);
              
              return (
                <div key={category} className="rounded-md border border-[var(--border)] p-3 bg-[var(--background)]">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-xs font-semibold text-[var(--muted)] uppercase">{category}</h4>
                    <Button 
                      variant="ghost" 
                      size="compact" 
                      className="h-6 text-xs px-2"
                      onClick={() => {
                        const name = prompt("Nombre del nuevo punto de control:");
                        if (name) checkMutation.mutate({ category, name });
                      }}
                    >
                      AÃ±adir punto
                    </Button>
                  </div>
                  
                  {checks.length === 0 ? (
                    <p className="text-xs text-[var(--muted-soft)]">No hay puntos registrados.</p>
                  ) : (
                    <ul className="space-y-2">
                      {checks.map(check => (
                        <li key={check.id} className="flex items-center justify-between border-t border-[var(--border)] pt-2">
                          <span className="text-sm">{check.name}</span>
                          <div className="flex gap-1">
                            <button
                              onClick={() => updateResultMutation.mutate({ checkId: check.id, result: "PASS" })}
                              className={`flex h-7 w-7 items-center justify-center rounded-sm border transition-colors ${
                                check.result === "PASS" ? "bg-green-500/20 border-green-500 text-green-500" : "border-[var(--border)] text-[var(--muted)] hover:bg-[var(--surface-hover)]"
                              }`}
                              title="Correcto"
                            >
                              <Check size={14} />
                            </button>
                            <button
                              onClick={() => updateResultMutation.mutate({ checkId: check.id, result: "WARNING" })}
                              className={`flex h-7 w-7 items-center justify-center rounded-sm border transition-colors ${
                                check.result === "WARNING" ? "bg-yellow-500/20 border-yellow-500 text-yellow-500" : "border-[var(--border)] text-[var(--muted)] hover:bg-[var(--surface-hover)]"
                              }`}
                              title="Advertencia"
                            >
                              <AlertTriangle size={14} />
                            </button>
                            <button
                              onClick={() => updateResultMutation.mutate({ checkId: check.id, result: "FAIL" })}
                              className={`flex h-7 w-7 items-center justify-center rounded-sm border transition-colors ${
                                check.result === "FAIL" ? "bg-red-500/20 border-red-500 text-red-500" : "border-[var(--border)] text-[var(--muted)] hover:bg-[var(--surface-hover)]"
                              }`}
                              title="Fallo"
                            >
                              <X size={14} />
                            </button>
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              );
            })}
          </div>
        </section>

        {/* Archivos y Fotos */}
        <section>
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-[var(--foreground)]">Fotos y Documentos</h3>
            <div>
              <input 
                type="file" 
                id="file-upload" 
                className="hidden" 
                accept="image/*,application/pdf"
                onChange={(e) => void handleFileUpload(e)}
                disabled={isUploading}
              />
              <Button variant="secondary" size="compact" className="cursor-pointer h-7 text-xs px-2" onClick={() => document.getElementById("file-upload")?.click()}>
                {isUploading ? <Upload size={14} className="mr-1 animate-pulse" /> : <Camera size={14} className="mr-1" />}
                Subir archivo
              </Button>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
            {files?.map(file => (
              <div key={file.id} className="group relative flex aspect-square flex-col items-center justify-center overflow-hidden rounded-md border border-[var(--border)] bg-[var(--surface-hover)] p-2 text-center">
                <Paperclip size={24} className="text-[var(--muted)] mb-2" />
                <span className="w-full truncate text-xs text-[var(--foreground)]" title={file.file_name}>{file.file_name}</span>
                <span className="text-[0.65rem] text-[var(--muted)]">{(file.size_bytes / 1024).toFixed(1)} KB</span>
                
                <a 
                  href={`/api/v1/files/${file.id}/download`}
                  target="_blank"
                  rel="noreferrer"
                  className="absolute inset-0 flex items-center justify-center bg-black/60 opacity-0 transition-opacity group-hover:opacity-100"
                >
                  <span className="rounded bg-[var(--background)] px-2 py-1 text-xs font-medium text-[var(--foreground)]">Ver</span>
                </a>
              </div>
            ))}
          </div>
        </section>

      </div>
    </div>
  );
}
