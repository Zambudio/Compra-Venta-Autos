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
    print("=======================================================================")
    print("=== SMOKE TEST Y SEED DE REFERENCIA FASE 4 (KNOWLEDGE BASE) EN NAS ===")
    print("=======================================================================")
    client = httpx.Client(base_url=BASE_URL, timeout=20.0)

    # 1. Health checks (con reintentos para arranque de contenedor)
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
    print(f"[1/8] Health Live: OK ({r_live.json()})")

    r_ready = client.get("/api/v1/health/ready")
    assert r_ready.status_code == 200, f"Ready fallo: {r_ready.status_code}"
    print(f"[2/8] Health Ready: OK ({r_ready.json()})")

    # 2. Login OWNER
    email, password = load_env_credentials()
    assert email and password, "No se encontraron credenciales OWNER en .env"
    
    r_login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r_login.status_code == 200, f"Login fallo: {r_login.status_code} {r_login.text}"
    csrf_token = client.cookies.get("motorscope_csrf")
    headers = {"X-CSRF-Token": csrf_token} if csrf_token else {}
    print(f"[3/8] Login OWNER: OK (Status 200, CSRF token: {bool(csrf_token)})")

    # 3. Registrar o reutilizar fuentes documentales
    print("[4/8] Registrando fuentes documentales trazables (Plan Maestro §15)...")
    sources_data = [
        {
            "source_type": "OFFICIAL_RECALL",
            "name": "Safety Gate Alerta A12/01504/20 PureTech EB2",
            "url": "https://ec.europa.eu/safety-gate-alerts/screen/webReport/alertDetail/10000000",
            "publisher": "Comisión Europea - Sistema Safety Gate",
            "trust_level": "A",
            "notes": "Recall oficial por degradación de la correa en baño de aceite y pérdida de asistencia de frenado",
        },
        {
            "source_type": "STATISTICAL_REPORT",
            "name": "TÜV Report & ADAC Pannenstatistik - Fiabilidad Diesel VAG 1.9 TDI",
            "url": "https://www.tuv.com/report-reliability",
            "publisher": "TÜV Rheinland / ADAC e.V.",
            "trust_level": "B",
            "notes": "Estadística longitudinal con tasa de fallos mecánicos inferior al 1.2% en 150.000 km",
        },
        {
            "source_type": "TECHNICAL_MEDIA",
            "name": "Boletín de Taller y Prensa Especializada - Cadena 1.4 TSI EA111",
            "url": "https://www.autobild.de/artikel/vw-tsi-motoren-steuerketten-probleme",
            "publisher": "Auto Bild & Red Técnica de Rectificadores",
            "trust_level": "C",
            "notes": "Análisis metalúrgico y de tolerancias del tensor y cadena en bloques 1.4 TSI Twincharger y Turbo",
        },
    ]

    r_existing_src = client.get("/api/v1/knowledge/sources", headers=headers)
    existing_src_names = {s["name"]: s["id"] for s in r_existing_src.json().get("items", [])} if r_existing_src.status_code == 200 else {}

    src_ids = {}
    for s_in in sources_data:
        if s_in["name"] in existing_src_names:
            src_ids[s_in["name"]] = existing_src_names[s_in["name"]]
        else:
            r_c = client.post("/api/v1/knowledge/sources", json=s_in, headers=headers)
            assert r_c.status_code == 201, f"Error creando fuente {s_in['name']}: {r_c.text}"
            src_ids[s_in["name"]] = r_c.json()["id"]
    print(f"     Fuentes trazables listas: {len(src_ids)} fuentes (Niveles A, B y C)")

    # 4. Registrar Jerarquia Tecnica
    print("[5/8] Registrando catalogo mecanico canonico (Fabricantes, Modelos y Motores)...")
    r_mfgs = client.get("/api/v1/knowledge/manufacturers", headers=headers)
    existing_mfgs = {m["name"]: m["id"] for m in r_mfgs.json()} if r_mfgs.status_code == 200 else {}
    
    mfg_ids = {}
    for m_name, country in [("Peugeot", "Francia"), ("SEAT", "España"), ("Volkswagen", "Alemania")]:
        if m_name in existing_mfgs:
            mfg_ids[m_name] = existing_mfgs[m_name]
        else:
            r_m = client.post("/api/v1/knowledge/manufacturers", json={"name": m_name, "country": country}, headers=headers)
            assert r_m.status_code == 201
            mfg_ids[m_name] = r_m.json()["id"]

    # Modelos
    model_ids = {}
    for mod_name, m_name in [("208", "Peugeot"), ("Ibiza", "SEAT"), ("Golf", "Volkswagen")]:
        r_mods = client.get("/api/v1/knowledge/models", params={"manufacturer_id": mfg_ids[m_name]}, headers=headers)
        ex_mods = {m["name"]: m["id"] for m in r_mods.json()} if r_mods.status_code == 200 else {}
        if mod_name in ex_mods:
            model_ids[mod_name] = ex_mods[mod_name]
        else:
            r_mo = client.post("/api/v1/knowledge/models", json={"manufacturer_id": mfg_ids[m_name], "name": mod_name}, headers=headers)
            assert r_mo.status_code == 201
            model_ids[mod_name] = r_mo.json()["id"]

    # Motores
    engine_ids = {}
    engines_data = [
        {"manufacturer_id": mfg_ids["Peugeot"], "family_code": "EB2", "name": "1.2 PureTech 3-cilindros", "displacement_cc": 1199, "fuel_type": "PETROL", "aspiration": "TURBOCHARGED"},
        {"manufacturer_id": mfg_ids["SEAT"], "family_code": "EA188", "name": "1.9 TDI Inyector-Bomba / Rotativa", "displacement_cc": 1896, "fuel_type": "DIESEL", "aspiration": "TURBOCHARGED"},
        {"manufacturer_id": mfg_ids["Volkswagen"], "family_code": "EA111", "name": "1.4 TSI / TFSI Cadena", "displacement_cc": 1390, "fuel_type": "PETROL", "aspiration": "TURBOCHARGED"},
    ]
    for eng in engines_data:
        r_engs = client.get("/api/v1/knowledge/engines", params={"manufacturer_id": eng["manufacturer_id"]}, headers=headers)
        ex_engs = {e["family_code"]: e["id"] for e in r_engs.json()} if r_engs.status_code == 200 else {}
        if eng["family_code"] in ex_engs:
            engine_ids[eng["family_code"]] = ex_engs[eng["family_code"]]
        else:
            r_en = client.post("/api/v1/knowledge/engines", json=eng, headers=headers)
            assert r_en.status_code == 201
            engine_ids[eng["family_code"]] = r_en.json()["id"]
    print(f"     Catalogo canonico listo: Peugeot 208 (EB2), SEAT Ibiza (EA188), VW Golf (EA111)")

    # 5. Evidencias tecnicas y Problemas conocidos
    print("[6/8] Registrando evidencias tecnicas y problemas conocidos...")
    # Evidencias
    ev_eb2_id = None
    r_evs = client.get("/api/v1/knowledge/evidences", headers=headers)
    for e in r_evs.json().get("items", []):
        if "Safety Gate" in e.get("summary", ""):
            ev_eb2_id = e["id"]
            break
    if not ev_eb2_id:
        r_ev = client.post("/api/v1/knowledge/evidences", json={
            "source_id": src_ids["Safety Gate Alerta A12/01504/20 PureTech EB2"],
            "component": "TIMING_SYSTEM",
            "summary": "Boletin oficial Safety Gate: desprendimiento de particulas de la correa humeda que obturan el depresor de freno",
            "severity": "CRITICAL",
            "confidence_score": "0.990",
            "verified": True,
        }, headers=headers)
        assert r_ev.status_code == 201, f"Error creando evidencia EB2: {r_ev.status_code} {r_ev.text}"
        ev_eb2_id = r_ev.json()["id"]

    ev_ea111_id = None
    for e in r_evs.json().get("items", []):
        if "elongacion" in e.get("summary", "").lower():
            ev_ea111_id = e["id"]
            break
    if not ev_ea111_id:
        r_ev = client.post("/api/v1/knowledge/evidences", json={
            "source_id": src_ids["Boletín de Taller y Prensa Especializada - Cadena 1.4 TSI EA111"],
            "component": "TIMING_SYSTEM",
            "summary": "Estudio de averias de taller: elongacion de la cadena de eslabones simples y destensado en arranque en frio",
            "severity": "HIGH",
            "confidence_score": "0.910",
            "verified": True,
        }, headers=headers)
        assert r_ev.status_code == 201, f"Error creando evidencia EA111: {r_ev.status_code} {r_ev.text}"
        ev_ea111_id = r_ev.json()["id"]

    # Problemas Conocidos
    r_issues = client.get("/api/v1/knowledge/issues", headers=headers)
    ex_issues = {i["title"]: i["id"] for i in r_issues.json().get("items", [])}

    if "Degradacion de correa humeda en bano de aceite (EB2)" not in ex_issues:
        r_iss = client.post("/api/v1/knowledge/issues", json={
            "component": "TIMING_SYSTEM",
            "title": "Degradacion de correa humeda en bano de aceite (EB2)",
            "description": "La correa de distribucion sumergida en aceite sufre degradacion quimica prematura; los residuos colmatan la chupona de aceite y la bomba de vacio de frenos.",
            "symptoms": "Testigo de presion de aceite encendido, pedal de freno duro, aviso de fallo motor.",
            "prevention": "Uso estricto de aceite homologado PSA B71 2010 / 2297 y cambio preventivo cada 50.000 km o 4 anos.",
            "definitive_repair": "Sustitucion de kit de distribucion reforzado, limpieza integral de carter/chupona y verificacion de depresor de frenado.",
            "severity": "CRITICAL",
            "frequency": "SYSTEMIC",
            "has_recall_campaign": True,
            "estimated_repair_cost_min": 1000,
            "estimated_repair_cost_max": 4000,
            "status": "VERIFIED",
            "engine_ids": [engine_ids["EB2"]],
            "evidence_ids": [ev_eb2_id],
        }, headers=headers)
        assert r_iss.status_code == 201, f"Error creando issue EB2: {r_iss.text}"
        issue_eb2_id = r_iss.json()["id"]
    else:
        issue_eb2_id = ex_issues["Degradacion de correa humeda en bano de aceite (EB2)"]

    if "Elongacion de cadena de distribucion y tensor (EA111)" not in ex_issues:
        r_iss = client.post("/api/v1/knowledge/issues", json={
            "component": "TIMING_SYSTEM",
            "title": "Elongacion de cadena de distribucion y tensor (EA111)",
            "description": "Elongacion de la cadena de distribucion por fatiga de material y fallo del tensor hidraulico sin antirretorno.",
            "symptoms": "Ruido metalico tipo traqueteo en frio durante los primeros 3 a 5 segundos de arranque.",
            "prevention": "Comprobacion periodica del desfase de arboles de levas por diagnosis y cambio de aceite cada 15.000 km.",
            "definitive_repair": "Instalacion del kit de cadena modificado con tensor antirretorno mejorado de fabricante original.",
            "severity": "HIGH",
            "frequency": "FREQUENT",
            "has_recall_campaign": False,
            "estimated_repair_cost_min": 750,
            "estimated_repair_cost_max": 1800,
            "status": "VERIFIED",
            "engine_ids": [engine_ids["EA111"]],
            "evidence_ids": [ev_ea111_id],
        }, headers=headers)
        assert r_iss.status_code == 201, f"Error creando issue EA111: {r_iss.text}"

    # Clasificaciones
    print("     Creando clasificaciones objetivas: Blacklist (EB2), Whitelist (1.9 TDI), Watchlist (EA111)...")
    r_cls = client.get("/api/v1/knowledge/classifications", headers=headers)
    ex_cls = {c["target_id"]: c["status"] for c in r_cls.json().get("items", [])}

    if engine_ids["EB2"] not in ex_cls:
        r_c = client.post("/api/v1/knowledge/classifications", json={
            "target_type": "ENGINE",
            "target_id": engine_ids["EB2"],
            "status": "BLACKLIST",
            "rationale": "Defecto sistemico de diseno en correa humeda con llamada oficial a revision por fallo en frenos (Safety Gate). No recomendado salvo sustitucion demostrable.",
        }, headers=headers)
        assert r_c.status_code == 201

    if engine_ids["EA188"] not in ex_cls:
        r_c = client.post("/api/v1/knowledge/classifications", json={
            "target_type": "ENGINE",
            "target_id": engine_ids["EA188"],
            "status": "WHITELIST",
            "rationale": "Mecanica de probada robustez y longevidad, con costes de mantenimiento y repuestos minimos en mercado europeo.",
        }, headers=headers)
        assert r_c.status_code == 201

    if engine_ids["EA111"] not in ex_cls:
        r_c = client.post("/api/v1/knowledge/classifications", json={
            "target_type": "ENGINE",
            "target_id": engine_ids["EA111"],
            "status": "WATCHLIST",
            "rationale": "Riesgo moderado-alto de elongacion de cadena de distribucion. Inspeccionar traqueteo en arranque en frio y facturas de kit sustituido.",
        }, headers=headers)
        assert r_c.status_code == 201

    # 6. Validacion del algoritmo explicable de fiabilidad (reliability-lookup)
    print("[7/8] Validando diagnostico explicable /reliability-lookup (Plan Maestro §15)...")
    # Caso 1: Peugeot 208 EB2 -> BLACKLIST
    r_diag1 = client.get("/api/v1/knowledge/reliability-lookup", params={"brand": "Peugeot", "model": "208", "engine_code": "EB2"}, headers=headers)
    assert r_diag1.status_code == 200, f"Diag 1 fallo: {r_diag1.status_code} {r_diag1.text}"
    d1 = r_diag1.json()
    print(f"     Caso 1 (Peugeot 208 EB2): Clasificacion={d1['classification']}, Issues={d1['issues_count']}, Recalls={d1['has_recalls']}, Costes={d1['total_estimated_repair_min']}-{d1['total_estimated_repair_max']} EUR")
    assert d1["classification"] == "BLACKLIST", f"EB2 debio ser BLACKLIST, fue {d1['classification']}"
    assert d1["has_recalls"] is True, "EB2 debio tener has_recalls=True"
    assert d1["issues_count"] >= 1
    assert len(d1["preventive_recommendations"]) > 0

    # Caso 2: SEAT Ibiza 1.9 TDI -> WHITELIST
    r_diag2 = client.get("/api/v1/knowledge/reliability-lookup", params={"brand": "SEAT", "model": "Ibiza", "engine_code": "EA188"}, headers=headers)
    assert r_diag2.status_code == 200
    d2 = r_diag2.json()
    print(f"     Caso 2 (SEAT Ibiza 1.9 TDI): Clasificacion={d2['classification']}, Issues={d2['issues_count']}, Recalls={d2['has_recalls']}")
    assert d2["classification"] == "WHITELIST", f"1.9 TDI debio ser WHITELIST, fue {d2['classification']}"
    assert d2["has_recalls"] is False

    # Caso 3: VW Golf 1.4 TSI EA111 -> WATCHLIST
    r_diag3 = client.get("/api/v1/knowledge/reliability-lookup", params={"brand": "Volkswagen", "model": "Golf", "engine_code": "EA111"}, headers=headers)
    assert r_diag3.status_code == 200
    d3 = r_diag3.json()
    print(f"     Caso 3 (VW Golf EA111): Clasificacion={d3['classification']}, Issues={d3['issues_count']}, Recalls={d3['has_recalls']}")
    assert d3["classification"] == "WATCHLIST", f"EA111 debio ser WATCHLIST, fue {d3['classification']}"
    assert d3["issues_count"] >= 1

    # 7. Validacion de Mitigaciones a nivel de unidad
    print("[8/8] Validando mitigaciones a nivel de unidad de vehiculo...")
    # Obtener un vehiculo existente en el sistema
    r_vehs = client.get("/api/v1/vehicles", params={"page_size": 1}, headers=headers)
    assert r_vehs.status_code == 200
    vehs = r_vehs.json().get("items", [])
    assert len(vehs) > 0, "Debe existir al menos un vehiculo para probar mitigaciones"
    target_veh = vehs[0]
    veh_id = target_veh["id"]

    # Crear una mitigacion para este vehiculo
    r_mit = client.post("/api/v1/knowledge/mitigations", json={
        "vehicle_id": veh_id,
        "known_issue_id": issue_eb2_id,
        "mitigation_type": "INVOICE_PROVED_REPLACEMENT",
        "description": "Correa sustituida en concesionario oficial Peugeot con factura demostrable y revision de chupona",
        "applied_at": "2026-03-01T10:00:00Z",
    }, headers=headers)
    assert r_mit.status_code == 201, f"Error creando mitigacion: {r_mit.text}"
    mit_data = r_mit.json()
    print(f"     Mitigacion registrada para vehiculo {veh_id}: Tipo={mit_data['mitigation_type']}")

    # Consultar mitigaciones del vehiculo
    r_get_mits = client.get(f"/api/v1/knowledge/vehicles/{veh_id}/mitigations", headers=headers)
    assert r_get_mits.status_code == 200
    mits_list = r_get_mits.json()
    assert any(m["id"] == mit_data["id"] for m in mits_list), "La mitigacion creada debe aparecer en el listado del vehiculo"
    print(f"     Listado de mitigaciones verificado: {len(mits_list)} mitigaciones en la unidad.")

    # 8. Verificacion frontend web
    r_web = client.get("/")
    assert r_web.status_code == 200, f"Web devolvio {r_web.status_code}"
    assert "MotorScope" in r_web.text or "<!DOCTYPE html>" in r_web.text, "La respuesta de la web debe ser HTML valido"
    print("     Frontend Web en http://192.168.1.3:3080: OK (Status 200, HTML servido por Caddy)")

    print("\n=======================================================================")
    print("=== SMOKE TEST Y SEED DE FASE 4 COMPLETADOS CON EXITO (100% OK)    ===")
    print("=======================================================================")

if __name__ == "__main__":
    main()
