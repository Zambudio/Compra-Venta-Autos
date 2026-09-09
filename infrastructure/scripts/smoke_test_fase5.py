import os
import sys
import time
from decimal import Decimal
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
    print("=======================================================================")
    print("=== SMOKE TEST Y VALIDACIÓN INTEGRAL FASE 5 (SCORING) EN NAS 192.168.1.3 ===")
    print("=======================================================================")
    client = httpx.Client(base_url=BASE_URL, timeout=25.0)

    # 1. Health checks
    print("[1/9] Verificando salud del API...")
    r_live = None
    for _ in range(15):
        try:
            r_live = client.get("/api/v1/health/live")
            if r_live.status_code == 200:
                break
        except Exception:
            pass
        time.sleep(2)
    assert r_live is not None and r_live.status_code == 200, f"Live fallo: {r_live.status_code if r_live else 'None'}"
    print(f"      Health Live: OK ({r_live.json()})")

    r_ready = client.get("/api/v1/health/ready")
    assert r_ready.status_code == 200, f"Ready fallo: {r_ready.status_code}"
    print(f"      Health Ready: OK ({r_ready.json()})")

    # 2. Login OWNER
    print("[2/9] Autenticando sesión OWNER...")
    email, password = load_env_credentials()
    assert email and password, "No se encontraron credenciales OWNER en .env"
    
    r_login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r_login.status_code == 200, f"Login fallo: {r_login.status_code} {r_login.text}"
    csrf_token = client.cookies.get("motorscope_csrf")
    headers = {"X-CSRF-Token": csrf_token} if csrf_token else {}
    print(f"      Login OWNER: OK (Status 200, CSRF token: {bool(csrf_token)})")

    # 3. Perfiles de Scoring y Versionado
    print("[3/9] Consultando perfiles de scoring determinista...")
    r_profiles = client.get("/api/v1/scoring/profiles", headers=headers)
    assert r_profiles.status_code == 200, f"Error listando perfiles: {r_profiles.text}"
    profiles = r_profiles.json()
    assert len(profiles) > 0, "No se encontraron perfiles de scoring (falta seed por defecto)"
    default_profile = next((p for p in profiles if p["slug"] == "reventa-rapida"), profiles[0])
    print(f"      Perfil activo: '{default_profile['name']}' (slug: {default_profile['slug']})")

    # Verificar versión y pesos
    version_data = default_profile.get("active_version") or default_profile["versions"][0]
    r_version = client.get(f"/api/v1/scoring/versions/{version_data['id']}", headers=headers)
    assert r_version.status_code == 200, f"Error obteniendo versión de perfil: {r_version.text}"
    version_data = r_version.json()
    weights = version_data["weights"]
    total_weights = sum(Decimal(str(w)) for w in weights.values())
    assert total_weights == Decimal("1.000"), f"Los pesos no suman 1.000 (suman {total_weights})"
    assert len(weights) == 9, f"Se esperaban 9 componentes de scoring, hay {len(weights)}"
    print(f"      Versión v{version_data['version_number']}: 9 componentes validados, suma exacta = 1.000 (100%)")

    # 4. Obtener anuncios disponibles para evaluar
    print("[4/9] Buscando anuncios existentes para evaluación de oportunidad...")
    r_listings = client.get("/api/v1/listings?page=1&page_size=10", headers=headers)
    assert r_listings.status_code == 200, f"Error obteniendo anuncios: {r_listings.text}"
    listings = r_listings.json().get("items", [])
    assert len(listings) > 0, "No hay anuncios en el sistema para evaluar"
    target_listing = listings[0]
    print(f"      Anuncio seleccionado: {target_listing['brand']} {target_listing['model']} ({target_listing['year']}) - {target_listing['price_amount']} EUR")

    # 5. Evaluar Oportunidad para el Anuncio
    print("[5/9] Ejecutando motor de evaluación determinista sobre anuncio...")
    r_eval = client.post(f"/api/v1/opportunities/evaluate/listing/{target_listing['id']}", headers=headers)
    assert r_eval.status_code == 200, f"Error evaluando oportunidad: {r_eval.text}"
    opp = r_eval.json()
    opp_id = opp["id"]
    assert opp["status"] in ["IDENTIFIED", "ANALYZING", "VALIDATED", "DISCARDED", "PURCHASED", "SOLD"]
    assert opp["score"] is not None, "La oportunidad no contiene puntuación de scoring"
    score_data = opp["score"]
    print(f"      Oportunidad generada: ID {opp_id}")
    total_score = score_data.get("total_score") or score_data.get("score_total")
    print(f"      Score Total: {total_score} / 100 (Confianza: {opp['confidence_level']})")
    print(f"      Presión Vendedor: {opp['seller_pressure_level']} ({len(opp['seller_pressure_reasons'])} motivos)")

    # 6. Validar Desglose Económico e Intervalos
    print("[6/9] Validando coherencia del modelo financiero (Plan Maestro §19)...")
    asking = Decimal(str(opp["asking_price"]))
    mkt = Decimal(str(opp["estimated_market_price"])) if opp["estimated_market_price"] else None
    fast_sale = Decimal(str(opp["estimated_fast_sale_price"])) if opp["estimated_fast_sale_price"] else None
    target_purchase = Decimal(str(opp["target_purchase_price"])) if opp["target_purchase_price"] else None
    cost_min = Decimal(str(opp["estimated_total_cost_min"]))
    cost_max = Decimal(str(opp["estimated_total_cost_max"]))
    assert cost_min <= cost_max, f"Coste min ({cost_min}) mayor que max ({cost_max})"
    print(f"      Precio Pedido: {asking} € | Venta Rápida: {fast_sale} € | Compra Sugerida: {target_purchase} €")
    print(f"      Inversión proyectada [Mín - Máx]: {cost_min} € - {cost_max} €")
    print(f"      Margen neto proyectado: {opp['estimated_margin_min']} € a {opp['estimated_margin_max']} €")
    print(f"      ROI neto proyectado: {opp['estimated_roi_min']} % a {opp['estimated_roi_max']} %")

    # 7. Evaluar Vehículo si existe
    print("[7/9] Evaluando oportunidad a nivel de vehículo canónico...")
    r_vehs = client.get("/api/v1/vehicles?page=1&page_size=5", headers=headers)
    if r_vehs.status_code == 200 and r_vehs.json().get("items"):
        target_veh = r_vehs.json()["items"][0]
        r_eval_veh = client.post(f"/api/v1/opportunities/evaluate/vehicle/{target_veh['id']}", headers=headers)
        assert r_eval_veh.status_code == 200, f"Error evaluando vehículo: {r_eval_veh.text}"
        opp_veh = r_eval_veh.json()
        veh_score = opp_veh["score"].get("total_score") or opp_veh["score"].get("score_total")
        print(f"      Oportunidad para vehículo {target_veh['brand']} {target_veh['model']}: Score {veh_score} / 100")
    else:
        print("      (Sin vehículos canónicos aún, omitiendo evaluación de vehículo)")

    # 8. Listar y Actualizar Estado de Oportunidad
    print("[8/9] Probando transición de estados y filtros de oportunidades...")
    # Cambiar a ANALYZING
    r_patch1 = client.patch(
        f"/api/v1/opportunities/{opp_id}/status",
        json={"status": "ANALYZING", "notes": "Auditoría en proceso: verificar ITV y fotos de bajos"},
        headers=headers,
    )
    assert r_patch1.status_code == 200, f"Error actualizando estado: {r_patch1.text}"
    assert r_patch1.json()["status"] == "ANALYZING"
    print("      Estado cambiado a: ANALYZING (con notas)")

    # Cambiar a VALIDATED
    r_patch2 = client.patch(
        f"/api/v1/opportunities/{opp_id}/status",
        json={"status": "VALIDATED", "notes": "Aprobado para contacto y negociación"},
        headers=headers,
    )
    assert r_patch2.status_code == 200, f"Error validando oportunidad: {r_patch2.text}"
    assert r_patch2.json()["status"] == "VALIDATED"
    print("      Estado cambiado a: VALIDATED")

    # Listar con filtro de estado
    r_filtered = client.get("/api/v1/opportunities?status=VALIDATED", headers=headers)
    assert r_filtered.status_code == 200
    validated_items = r_filtered.json()["items"]
    assert any(item["id"] == opp_id for item in validated_items), "La oportunidad validada no aparece en el filtro"
    print(f"      Filtro de oportunidades 'VALIDATED': OK ({len(validated_items)} encontradas)")

    # 9. Verificación de Frontend Web en el puerto 3080
    print("[9/9] Verificando respuesta del frontend web en Caddy (puerto 3080)...")
    r_web = client.get("/")
    assert r_web.status_code == 200, f"Frontend web falló con status {r_web.status_code}"
    assert "MotorScope" in r_web.text or "<!DOCTYPE html>" in r_web.text or "html" in r_web.text
    print("      Frontend Next.js: OK (HTTP 200)")

    print("=======================================================================")
    print("=== TODAS LAS PRUEBAS DE SMOKE TEST FASE 5 PASARON EXITOSAMENTE (OK) ===")
    print("=======================================================================")

if __name__ == "__main__":
    main()
