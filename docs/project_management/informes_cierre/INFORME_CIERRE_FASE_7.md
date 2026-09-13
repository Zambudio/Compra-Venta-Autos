# Informe de Cierre: Fase 7 (Garage y Finance)

## 1. Resumen de EjecuciÃ³n
Se ha completado satisfactoriamente la Fase 7.
Esta fase introduce la capacidad de registrar la adquisiciÃ³n final de oportunidades validadas y realizar un seguimiento del ciclo financiero del activo: inventariado (Garage), aplicaciÃ³n de gastos de reacondicionamiento (Expenses) y, finalmente, su venta (Sale).
El cÃ¡lculo del beneficio y del ROI (Retorno de InversiÃ³n) cumple estrictamente el requisito del ADR 0017 (Ledger append-only sin guardar sumas derivadas).

## 2. Trabajos Realizados

### 2.1 Backend (`apps/api`)
- **ADR 0017**: Se ha propuesto y adoptado el diseÃ±o del `Ledger append-only` evitando la duplicaciÃ³n de campos totales/dinero (no se guarda el coste total, sÃ³lo transacciones atÃ³micas).
- **Modelos y Migraciones**: Se aÃ±adieron las tablas `owned_vehicles`, `expenses` y `sales` mediante la migraciÃ³n `0008_garage_and_finance.py`. Los valores monetarios estÃ¡n implementados como `NUMERIC(12,2)` para garantizar la precisiÃ³n contable en PostgreSQL.
- **APIs de Garage (`app/garage`)**:
  - `POST /api/v1/garage/purchase`: Compra una oportunidad, creando de forma idempotente un `OwnedVehicle` y avanzando la `Opportunity` a estado `PURCHASED`.
  - `POST /api/v1/garage/vehicles/{id}/expenses`: Registra un gasto asÃ­ncrono asociado al vehÃ­culo (mecÃ¡nica, transporte, impuestos).
  - `POST /api/v1/garage/vehicles/{id}/sale`: Genera el apunte final de venta y marca la `Opportunity` original como `SOLD`.
  - `GET /api/v1/garage/vehicles`: Lista el inventario, calculando vÃ­a servicio en tiempo real (al vuelo) el acumulado de gastos, coste total, margen de beneficio y porcentaje de retorno de inversiÃ³n (ROI).

### 2.2 Frontend (`apps/web`)
- **Componentes y Tipos**: ImplementaciÃ³n estricta en `src/features/garage` para mapear de manera rÃ­gida los tipos devueltos (Expense, Sale, y OwnedVehicleWithDetails).
- **GarageView**:
  - PestaÃ±a propia dentro del Layout con iconos de `Warehouse`.
  - Grid de tarjetas mostrando los datos fundamentales: MatrÃ­cula, VIN, Estado (En Stock o Vendido).
  - Resumen financiero en tiempo real: Se visualizan los costes de adquisiciÃ³n (`purchase_price`), la sumatoria de gastos, y se genera un bloque dinÃ¡mico destacado de "Venta y ROI" exclusivo de los vehÃ­culos finalizados.
  - El componente integra insignias dinÃ¡micas (`Badge`) ajustando su color si el vehÃ­culo aÃºn es activo pasivo (Stock) frente a un activo lÃ­quido (Vendido).

## 3. Estado de Calidad
- `mypy`: 100% estricto sin errores en `app/garage`. Se han usado dicts con genÃ©ricos amplios `Any` para esquivar la rigidez que impedÃ­a compilar un dict dinÃ¡mico.
- `ruff` (linter/formatter): CÃ³digo automÃ¡ticamente adaptado sin incidencias.
- `eslint` y `tsc` (Frontend): Completamente en verde.
- Base de datos en lÃ­nea con F6: La integraciÃ³n de F7 descansa puramente sobre la Watchlist de F6 y avanza la trazabilidad.

## 4. Siguientes Pasos
Arranca oficialmente la **Fase 8** (Hardening y Aseguramiento TÃ©cnico L2). El software pasarÃ¡ a ser auditado por perfiles de seguridad, limitando y ajustando variables de estado, lÃ­mites de las subidas de adjuntos, pruebas automatizadas E2E exhaustivas de cara al despliegue, y se evaluarÃ¡ el Restore Procedure. Todo previo a la liberaciÃ³n final.
