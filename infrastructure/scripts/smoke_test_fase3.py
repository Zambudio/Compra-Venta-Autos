import os
import sys
import time
from pathlib import Path
import httpx

BASE_URL = "http://192.168.1.3:3080"
ENV_PATH = Path("N:/IA/02_Proyectos/Compra-Venta Autos/.env")

def load_env_credentials():
    email, password = None, None
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("OWNER_EMAIL="):
                email = line.split("=", 1)[1].strip()
            elif line.startswith("OWNER_PASSWORD="):
                password = line.split("=", 1)[1].strip()
    return email, password

def main():
    print("=== INICIANDO SMOKE TEST COMPLETO DE FASE 3 EN SYNOLOGY NAS ===")
    client = httpx.Client(base_url=BASE_URL, timeout=15.0)

    # 1. Health checks
    r_live = client.get("/api/v1/health/live")
    assert r_live.status_code == 200, f"Live falló: {r_live.status_code}"
    print(f"1. Health Live: OK ({r_live.json()})")

    r_ready = client.get("/api/v1/health/ready")
    assert r_ready.status_code == 200, f"Ready falló: {r_ready.status_code}"
    print(f"2. Health Ready: OK ({r_ready.json()})")

    # 2. Login
    email, password = load_env_credentials()
    assert email and password, "No se encontraron credenciales OWNER en .env"
    
    r_login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r_login.status_code == 200, f"Login falló: {r_login.status_code} {r_login.text}"
    csrf_token = client.cookies.get("motorscope_csrf")
    headers = {"X-CSRF-Token": csrf_token} if csrf_token else {}
    print(f"3. Login OWNER: OK (Status 200, CSRF token presente: {bool(csrf_token)})")

    # 3. Listar fuentes
    r_sources = client.get("/api/v1/sources")
    assert r_sources.status_code == 200, f"Sources falló: {r_sources.status_code}"
    sources = r_sources.json()
    print(f"4. Sources: OK ({[s['key'] for s in sources]})")

    # 4. Sincronizar catálogo mock
    r_sync = client.post("/api/v1/sources/mock/sync", headers=headers)
    assert r_sync.status_code in (200, 202), f"Sync mock falló: {r_sync.status_code} {r_sync.text}"
    sync_data = r_sync.json()
    print(f"5. Sync Mock: OK (Status {r_sync.status_code}, seen={sync_data.get('listings_seen')})")

    # 5. Obtener un anuncio del catálogo para crear un clon manual y activar deduplicación
    r_listings = client.get("/api/v1/listings", params={"page_size": 5})
    assert r_listings.status_code == 200
    listings = r_listings.json().get("items", [])
    assert len(listings) > 0, "No hay anuncios en el catálogo"
    sample = listings[0]
    print(f"6. Anuncio base para duplicado: {sample['brand']} {sample['model']} ({sample['year']}, {sample['mileage_km']} km, {sample['price_amount']} €)")

    # 6. Crear anuncio manual casi idéntico
    unique_url = f"https://example.com/manual-test-{int(time.time())}"
    manual_payload = {
        "url": unique_url,
        "brand": sample["brand"],
        "model": sample["model"],
        "year": sample["year"],
        "mileage_km": sample["mileage_km"] + 500,  # variación leve de 500 km
        "price_amount": sample["price_amount"],
        "fuel_type": sample["fuel_type"],
        "transmission": sample["transmission"],
        "province": sample.get("province") or "Madrid",
        "description": "Vehiculo de prueba para matching asistido de Fase 3",
    }
    r_create = client.post("/api/v1/listings/manual", json=manual_payload, headers=headers)
    assert r_create.status_code == 201, f"Creación manual falló: {r_create.status_code} {r_create.text}"
    new_listing = r_create.json()
    print(f"7. Alta manual creada: OK (ID: {new_listing['id']}, Brand: {new_listing['brand']}, Model: {new_listing['model']})")

    # 7. Consultar candidatos de matching pendientes
    r_candidates = client.get("/api/v1/match-candidates", params={"status": "PENDING"})
    assert r_candidates.status_code == 200
    cand_data = r_candidates.json()
    total_cand = cand_data.get("total", 0)
    print(f"8. Candidatos de matching PENDING: total={total_cand}")
    assert total_cand > 0, "El algoritmo multicriterio debió generar al menos un candidato PENDING"

    # 8. Confirmar el primer candidato pendiente
    candidate = cand_data["items"][0]
    cand_id = candidate["id"]
    print(f"9. Confirmando candidato {cand_id} (Score: {candidate['confidence_score']})...")
    r_confirm = client.post(f"/api/v1/match-candidates/{cand_id}/confirm", headers=headers)
    assert r_confirm.status_code == 200, f"Confirm falló: {r_confirm.status_code} {r_confirm.text}"
    conf_res = r_confirm.json()
    vehicle_id = conf_res.get("vehicle_id")
    print(f"   Confirmación OK: status={conf_res.get('status')}, vehicle_id={vehicle_id}")
    assert vehicle_id, "La confirmación debe vincular un vehicle_id"

    # 9. Consultar catálogo unificado de vehículos
    r_vehicles = client.get("/api/v1/vehicles")
    assert r_vehicles.status_code == 200
    vehicles_data = r_vehicles.json()
    print(f"10. Catálogo de vehículos unificados: total={vehicles_data.get('total')}")
    assert vehicles_data.get("total", 0) > 0, "Debe existir al menos 1 vehículo unificado"

    # 10. Inspeccionar detalle de vehículo consolidado
    r_detail = client.get(f"/api/v1/vehicles/{vehicle_id}")
    assert r_detail.status_code == 200, f"Detalle de vehículo falló: {r_detail.status_code}"
    det = r_detail.json()
    print(f"11. Ficha técnica de vehículo unificado: OK ({det['brand']} {det['model']}, {det['year']}, listings={len(det.get('listings', []))})")
    assert len(det.get("listings", [])) >= 2, "El vehículo unificado debe tener ambos listings consolidados"

    # 11. Calcular y guardar valoración de mercado
    r_est = client.post(f"/api/v1/vehicles/{vehicle_id}/market-estimate", headers=headers)
    assert r_est.status_code == 200, f"Estimación falló: {r_est.status_code} {r_est.text}"
    est = r_est.json()
    print(f"12. Valoración de mercado: OK (Estimado={est['estimated_amount']} {est['currency']}, Rango=[{est['low_amount']} - {est['high_amount']}], Comparables={est['number_of_comparables']}, Confianza={est['confidence_score']})")

    # 12. Consultar evolución histórica consolidada
    r_hist = client.get(f"/api/v1/vehicles/{vehicle_id}/history")
    assert r_hist.status_code == 200, f"Histórico falló: {r_hist.status_code}"
    hist = r_hist.json()
    print(f"13. Histórico de precios consolidado: OK (Días en mercado={hist['days_on_market']}, Min={hist['lowest_observed_price']} EUR, Max={hist['highest_observed_price']} EUR, Cambios={hist['total_price_changes']})")

    # 13. Frontend Web Next.js
    r_web = client.get("/")
    assert r_web.status_code == 200, f"Web UI falló: {r_web.status_code}"
    print(f"14. Frontend Web Next.js en puerto 3080: OK (Status 200)")

    print("\n=======================================================")
    print(">>> SMOKE TEST FASE 3: 100% EXITOSO EN SYNOLOGY NAS <<<")
    print("=======================================================")

if __name__ == "__main__":
    main()
