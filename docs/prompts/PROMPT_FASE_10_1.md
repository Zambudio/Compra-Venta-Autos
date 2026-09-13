# 🤖 Prompt Técnico - MotorScope Fase 10.1: Completar Gestión de Conectores y Búsquedas Reales

**Branch:** `feature/fase-10-real-search`
**Base:** Commit `c9f2b95` (fix: pydantic schema generation y alembic revision chain)
**Estado:** Plataforma en producción en NAS, Fase 10.0 completada al 70%

---

## 📋 OBJETIVO

Completar la implementación de MotorScope Fase 10 eliminando mocks de prueba e implementando:
1. Gestión dinámica de conectores en Settings (activar/desactivar Wallapop)
2. Búsquedas reales con Wallapop en tiempo real
3. Eliminación completa de mock data de tests

**Usuarios finales podrán:**
- Ver estado de conectores en Settings
- Activar/desactivar Wallapop dinámicamente
- Realizar búsquedas reales que consulten Wallapop
- Ver resultados auténticos con información de anuncios

---

## 🎯 REQUERIMIENTOS ESPECÍFICOS

### 1. API: Gestión de Conectores (HIGH PRIORITY)

#### Nuevo Endpoint: `PATCH /api/v1/sources/{key}/config`
**Propósito:** Permitir cambiar configuración de conectores dinámicamente

**Implementación:**

1. **Archivo:** `apps/api/app/sources/router.py` - Agregar endpoint
   ```python
   @sources_router.patch("/{key}/config")
   async def update_source_config(
       key: str,
       config: dict,  # {"enabled": true/false, ...}
       current_user: User = Depends(get_current_user),
   ) -> dict:
       """Actualizar configuración de fuente"""
   ```

2. **Lógica en:** `apps/api/app/sources/service.py`
   ```python
   async def update_source_config(self, key: str, config: dict) -> dict:
       """Actualizar estado y config de fuente"""
       # Validaciones:
       # - key debe existir en registry
       # - No permitir desactivar TODOS los conectores
       # - Solo admin puede cambiar configuración
       
       # Persistir en BD:
       # - Nueva tabla: sources_config(id, source_key, enabled, updated_at)
       # - O agregar columna 'enabled' a tabla sources existente
       
       # Actualizar redis cache
       
       # Retornar: {key, enabled, config, updated_at}
   ```

3. **Modelo de BD:**
   ```python
   # apps/api/app/sources/models.py
   class SourceConfig(TimestampMixin, Base):
       __tablename__ = "source_configurations"
       
       id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
       source_key: Mapped[str] = mapped_column(String, unique=True)  # "wallapop", "manual"
       enabled: Mapped[bool] = mapped_column(default=True)
       config: Mapped[dict] = mapped_column(JSON, nullable=True)  # {rate_limit, timeout, etc}
       last_sync: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
       sync_error: Mapped[str | None] = mapped_column(Text, nullable=True)
   ```

4. **Migración Alembic:** `apps/api/alembic/versions/20260913_0010_source_config.py`
   ```
   - Crear tabla source_configurations
   - Insertar registros iniciales: {wallapop: enabled=true}, {manual: enabled=true}
   - Actualizar índices
   ```

#### Actualizar Endpoint: `GET /api/v1/sources`
- Retornar enabled/disabled status de cada conector
- Incluir config actual y timestamp del último sync
- Ejemplo:
  ```json
  [
    {
      "key": "wallapop",
      "name": "Wallapop",
      "enabled": true,
      "last_sync": "2026-09-13T10:30:00Z",
      "sync_error": null,
      "health": "ok"
    },
    {
      "key": "manual",
      "name": "Entrada Manual",
      "enabled": true,
      "config": {}
    }
  ]
  ```

#### Registrar Cambios de Configuración
- Crear tabla audit: `source_config_changes(id, source_key, before, after, changed_by, changed_at)`
- Registrar cada cambio para auditoría

---

### 2. Frontend: Settings UI Control (HIGH PRIORITY)

#### Actualizar Component: `apps/web/src/features/system/settings-view.tsx`

**Agregar Toggle Switches:**
```tsx
// Para cada conector:
- Toggle ON/OFF con loading state
- Indicador de health status
- Mostrar última sincronización
- Botón de "Forzar sincronización"

// Estructura de UI:
┌─ Gestión de Conectores
│  ├─ Wallapop
│  │  ├─ Toggle: [●] Activo
│  │  ├─ Estado: ✓ Saludable
│  │  ├─ Última sincronización: hace 5 minutos
│  │  └─ [Forzar sincronización]
│  │
│  └─ Entrada Manual
│     ├─ Toggle: [●] Activo
│     └─ Estado: ✓ Disponible
```

**Funcionalidad:**
```tsx
const handleToggleConnector = async (key: string, enabled: boolean) => {
  try {
    setLoading(key, true);
    const response = await fetch(`/api/v1/sources/${key}/config`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled })
    });
    
    if (!response.ok) {
      if (response.status === 400) {
        // "No puedes desactivar todos los conectores"
        showAlert("error", "Mantén al menos un conector activo");
        return;
      }
      throw new Error(await response.text());
    }
    
    // Actualizar estado local
    setSources(prev => prev.map(s => 
      s.key === key ? {...s, enabled} : s
    ));
    
    showAlert("success", `Conector ${key} ${enabled ? 'activado' : 'desactivado'}`);
    
  } catch (error) {
    showAlert("error", `Error: ${error.message}`);
  } finally {
    setLoading(key, false);
  }
};
```

**Tests:**
- `apps/web/src/features/system/settings-view.test.tsx` (CREAR)
  - Test toggle ON
  - Test toggle OFF
  - Test error cuando se intenta desactivar todos
  - Test loading states
  - Test validaciones

---

### 3. Backend: Búsquedas Reales (HIGH PRIORITY)

#### Nuevo Endpoint: `POST /api/v1/listings/search`
**Propósito:** Realizar búsquedas reales consultando Wallapop

**Implementación:**

1. **Archivo:** `apps/api/app/listings/router.py` - Agregar endpoint
   ```python
   @listings_router.post("/search")
   async def search_listings(
       query: str,
       filters: SearchFilters = Query(),  # {min_price, max_price, category, etc}
       current_user: User = Depends(get_current_user),
   ) -> SearchResult:
       """Buscar anuncios en Wallapop"""
   ```

2. **Modelos:** `apps/api/app/listings/models.py`
   ```python
   class SearchFilters(BaseModel):
       query: str
       min_price: int | None = None
       max_price: int | None = None
       location: str | None = None
       category: str | None = None
       source: str = "wallapop"  # Fuente a consultar
       limit: int = 20
       offset: int = 0

   class WallapopListing(BaseModel):
       id: str  # ID de Wallapop
       title: str
       description: str
       price: Decimal
       location: str
       images: list[str]
       seller: dict  # {name, rating, url}
       url: str
       posted_at: datetime
       source_key: str = "wallapop"

   class SearchResult(BaseModel):
       total: int
       listings: list[WallapopListing]
       query: str
       filters: dict
   ```

3. **Lógica en:** `apps/api/app/listings/service.py` (CREAR)
   ```python
   class ListingsService:
       def __init__(self, db: AsyncSession, cache: Redis):
           self.db = db
           self.cache = cache
           self.wallapop = WallapopConnector()
       
       async def search(self, filters: SearchFilters) -> SearchResult:
           """Buscar en Wallapop con caché"""
           
           # 1. Verificar si Wallapop está habilitado
           source_config = await self.db.get(SourceConfig, "wallapop")
           if not source_config.enabled:
               raise HTTPException(
                   status_code=503,
                   detail="Conector Wallapop deshabilitado"
               )
           
           # 2. Generar cache key
           cache_key = f"search:{filters.query}:{hash(str(filters))}"
           
           # 3. Intentar obtener de caché (TTL: 5 minutos)
           cached = await self.cache.get(cache_key)
           if cached:
               return SearchResult.model_validate_json(cached)
           
           # 4. Realizar búsqueda real
           try:
               listings = await self.wallapop.search(
                   query=filters.query,
                   min_price=filters.min_price,
                   max_price=filters.max_price,
                   location=filters.location
               )
               
               # 5. Transformar y normalizar datos
               normalized_listings = [
                   WallapopListing(
                       id=item['id'],
                       title=item['title'],
                       description=item['description'],
                       price=Decimal(item['price']),
                       location=item['location'],
                       images=item.get('images', []),
                       seller={
                           'name': item['seller']['name'],
                           'rating': item['seller'].get('rating'),
                           'url': item['seller'].get('url')
                       },
                       url=item['url'],
                       posted_at=datetime.fromisoformat(item['posted_at'])
                   )
                   for item in listings
               ]
               
               result = SearchResult(
                   total=len(normalized_listings),
                   listings=normalized_listings,
                   query=filters.query,
                   filters=filters.model_dump()
               )
               
               # 6. Cachear resultado
               await self.cache.setex(
                   cache_key,
                   300,  # 5 minutos
                   result.model_dump_json()
               )
               
               return result
               
           except HTTPException as e:
               # 403, 429, 5xx de Wallapop
               raise e
           except Exception as e:
               raise HTTPException(status_code=500, detail=str(e))
   ```

#### Integrar con Frontend Search
**Archivo:** `apps/web/src/features/listings/api.ts`
```typescript
export async function searchListings(
  query: string,
  filters?: Partial<SearchFilters>
): Promise<SearchResult> {
  const params = new URLSearchParams({
    query,
    ...filters
  });
  
  const response = await fetch(
    `/api/v1/listings/search?${params}`,
    { method: 'POST' }
  );
  
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}
```

---

### 4. Eliminar Mocks de Prueba (HIGH PRIORITY)

#### 4.1 Backend Tests: `apps/api/tests/`

**Buscar y eliminar:**
```bash
# Patrón a buscar:
grep -r "MockConnector\|mock_data\|test_fixtures.*mock" apps/api/tests/
grep -r '"mock"' apps/api/tests/  # Referencias a fuente "mock"
```

**Archivos a limpiar:**
- `apps/api/tests/conftest.py` - Eliminar fixtures de mock
- `apps/api/tests/unit/test_*.py` - Reemplazar data mock
- `apps/api/tests/integration/` - Usar BD test real

**Ejemplo - Reemplazar mocks:**
```python
# ❌ ANTES (Mock)
@pytest.fixture
def mock_listing():
    return {
        "id": "mock-123",
        "title": "Mock Vehículo",
        "source": "mock"
    }

# ✅ DESPUÉS (Data Real o Seed)
@pytest.fixture
async def test_listing(db: AsyncSession):
    # Crear dato real de prueba en BD
    listing = Listing(
        title="Vehículo Test",
        source_key="wallapop",
        # ... otros campos
    )
    db.add(listing)
    await db.commit()
    return listing
```

#### 4.2 Frontend Tests: `apps/web/src/`

**Archivos a limpiar:**
- `apps/web/src/features/opportunities/test-fixtures.ts` - Eliminar "Mock Portal"
- `apps/web/src/features/listings/api.test.ts` - Actualizar a Wallapop
- `apps/web/src/features/listings/listing-detail.test.tsx` - Sin "mock" source
- Cualquier archivo con `source: "mock"` → cambiar a "wallapop" o "manual"

**Eliminar menciones:**
```bash
grep -r "mock" apps/web/src --include="*.test.ts*" --include="*.spec.ts"
```

#### 4.3 E2E Tests: `apps/web/tests/e2e/`

**Archivo:** `apps/web/tests/e2e/listings.spec.ts`
- Reescribir scenario de búsqueda:
  ```typescript
  // ❌ ANTES: Sincronizar mock
  await page.click('button:has-text("Sincronizar Mock")');
  
  // ✅ DESPUÉS: Búsqueda real o entrada manual
  await page.fill('input[placeholder="Buscar..."]', 'BMW 320');
  await page.click('button:has-text("Buscar")');
  ```

- Agregar validación de datos reales:
  ```typescript
  // Verificar que los resultados tienen estructura Wallapop
  const listing = await page.locator('[data-testid="listing-card"]').first();
  expect(await listing.locator('h3').textContent()).toContain('BMW');
  expect(await listing.locator('[data-price]')).toBeVisible();
  ```

---

## 🗄️ CAMBIOS DE BASE DE DATOS

### Nueva Migración (20260913_0010)
**Archivo:** `apps/api/alembic/versions/20260913_0010_source_configurations.py`

```python
from alembic import op
import sqlalchemy as sa
from uuid import uuid4

def upgrade():
    op.create_table(
        'source_configurations',
        sa.Column('id', sa.UUID(), default=uuid4, primary_key=True),
        sa.Column('source_key', sa.String(), unique=True, nullable=False),
        sa.Column('enabled', sa.Boolean(), default=True),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('last_sync', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sync_error', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # Datos iniciales
    op.execute(
        "INSERT INTO source_configurations (id, source_key, enabled) VALUES "
        "(gen_random_uuid(), 'wallapop', true),"
        "(gen_random_uuid(), 'manual', true)"
    )

def downgrade():
    op.drop_table('source_configurations')
```

---

## 🧪 CRITERIOS DE ACEPTACIÓN

### Código
- [ ] Todos los tests unitarios pasan: `pytest apps/api/tests/`
- [ ] Todos los tests frontend pasan: `npm test` (web)
- [ ] Tipos correctos: `mypy apps/api/app`
- [ ] Linting limpio: `ruff check apps/api/app`
- [ ] No hay warnings o errores en logs del API

### Funcionalidad
- [ ] Toggle de conectores funciona en Settings
- [ ] No se puede desactivar todos los conectores
- [ ] Búsqueda real consulta Wallapop y retorna datos
- [ ] Caché funciona (2 búsquedas iguales = una llamada a Wallapop)
- [ ] Errores de Wallapop (403, 429, 5xx) manejados correctamente
- [ ] Rate limiting respetado

### Eliminación de Mocks
- [ ] 0 referencias a "MockConnector" en código
- [ ] 0 referencias a `source: "mock"` excepto en historiales
- [ ] Todos los tests usan data real o controlada
- [ ] E2E tests ejecutan sin fixtures mock

### Documentación
- [ ] README actualizado con nuevos endpoints
- [ ] Ejemplos de curl/postman para búsqueda
- [ ] Documentación de configuración de conectores

---

## 📦 ARCHIVOS A CREAR/MODIFICAR

### Crear
- `apps/api/app/sources/models.py` (nueva tabla SourceConfig)
- `apps/api/app/listings/service.py` (lógica de búsqueda)
- `apps/api/alembic/versions/20260913_0010_*.py` (migración)
- `apps/web/src/features/system/settings-view.test.tsx` (tests Settings)
- `apps/web/src/features/listings/search.test.tsx` (tests búsqueda)

### Modificar
- `apps/api/app/sources/router.py` (agregar PATCH endpoint)
- `apps/api/app/sources/service.py` (lógica de config)
- `apps/api/app/listings/router.py` (agregar POST search)
- `apps/web/src/features/system/settings-view.tsx` (UI toggles)
- `apps/web/src/features/listings/api.ts` (search function)
- Varios archivos de tests (eliminar mocks)

---

## 🔍 CONSIDERACIONES TÉCNICAS

### Seguridad
- Validar permisos de usuario antes de cambiar configuración
- Sanitizar queries de búsqueda
- Rate limiting en endpoint de búsqueda

### Performance
- Caché con TTL de 5 minutos para búsquedas
- Índices en `source_configurations(source_key)`
- Paginación en resultados de búsqueda

### Escalabilidad
- Wallapop connector puede ser reemplazado por otro
- Arquitectura permite múltiples fuentes activas
- Audit trail de cambios de configuración

### Errores Esperados
- Wallapop 403: API key no autorizada
- Wallapop 429: Rate limit excedido (implementar backoff)
- Wallapop 5xx: Error del servidor (retry con jitter)
- No conectores activos: Retornar 503 Service Unavailable

---

## 🚀 PASOS DE IMPLEMENTACIÓN RECOMENDADOS

1. **DB Migration** - Crear tabla source_configurations
2. **API Endpoints** - PATCH /sources/{key}/config y POST /listings/search
3. **Frontend UI** - Toggles en Settings View
4. **Integration** - Conectar UI con nuevos endpoints
5. **Testing** - Tests unitarios y E2E
6. **Cleanup** - Eliminar todos los mocks
7. **Deploy** - Rebuild y redeploy en NAS

**Tiempo estimado:** 4-6 horas (incluye testing y deployment)

---

## 📞 REFERENCIAS

- Documentación de cambios: `FASE_10_STATUS.md`
- Wallapop API: Revisar en `apps/api/app/connectors/wallapop.py`
- Estructura de tests: `apps/api/tests/conftest.py`
- Settings UI base: `apps/web/src/features/system/settings-view.tsx`

---

**Generado:** 2026-09-13
**Para:** Siguiente agente en fase 10.1
**Branch:** feature/fase-10-real-search
**Prioridad:** ALTA - Completar implementación para producción
