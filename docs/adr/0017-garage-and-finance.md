# ADR 0017: Garage, Inventory, and Finance Ledger

## Status
Accepted

## Context
In Phase 7, MotorScope requires a subsystem to transition an `Opportunity` into an acquired asset (`OwnedVehicle`), tracking the complete financial lifecycle until its final sale (`Sale`). This requires tracking acquisition cost, reconditioning expenses, taxes, and final revenue to accurately compute the real return on investment (ROI).

A key restriction defined in the Master Plan is:
> "No almacenar dinero en `float` ... ni totales financieros duplicados."
> "Implementar ledger append-only; no persistir totales derivados."

We need a design that guarantees financial integrity, reproducibility, and auditability.

## Decision
1. **Core Entities**:
   - `OwnedVehicle`: Represents a purchased vehicle. One-to-one relationship with `Opportunity` (or `Vehicle`). Contains acquisition date, purchase price (stored as `Numeric` in DB, `Decimal` in Python), and registration details (VIN, License Plate).
   - `Expense`: Represents a discrete cost associated with an `OwnedVehicle` (e.g., repair, tax, transport). Contains an amount (`Numeric`), date, category, and optional receipt attachment (reusing `FileStorage`).
   - `Sale`: Represents the final disposal of the `OwnedVehicle`. Contains the sale price (`Numeric`), sale date, and buyer info.

2. **Append-Only Ledger**:
   - We will not store a mutable `total_cost` or `current_margin` field in `OwnedVehicle`.
   - Instead, the backend will compute total expenses, net margin, and actual ROI dynamically at read-time (or via SQL views/computed properties) by aggregating the `purchase_price`, all `Expense` records, and the `Sale` record (if any).

3. **Transition Transaction**:
   - Moving an `Opportunity` to `PURCHASED` and creating an `OwnedVehicle` must occur in a single, atomic database transaction to prevent dangling state.

4. **Currency Types**:
   - All financial amounts will be mapped to PostgreSQL `NUMERIC(12, 2)` (or similar precision) to avoid floating-point inaccuracies. Python's `decimal.Decimal` will be used exclusively for calculations.

## Consequences
- **Positive**: Exact financial trace. Computations are strictly derived from the ledger, making it impossible for the "total expenses" field to drift from the actual list of expenses. Complies with the Master Plan.
- **Negative**: Requires real-time aggregation which might add slight overhead, though negligible given the scale of a private platform.
