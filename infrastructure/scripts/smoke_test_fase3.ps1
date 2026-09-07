$ErrorActionPreference = "Stop"

# Leer .env
$envContent = Get-Content "N:\IA\02_Proyectos\Compra-Venta Autos\.env"
$ownerEmail = ($envContent | Where-Object { $_ -match "^OWNER_EMAIL=(.*)$" } | ForEach-Object { $matches[1].Trim() })
$ownerPassword = ($envContent | Where-Object { $_ -match "^OWNER_PASSWORD=(.*)$" } | ForEach-Object { $matches[1].Trim() })

$baseUrl = "http://192.168.1.3:3080"
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession

Write-Output "1. Comprobando Health Live y Ready..."
$live = Invoke-RestMethod -Uri "$baseUrl/api/v1/health/live" -Method Get
Write-Output "   Live: $($live.status)"
$ready = Invoke-RestMethod -Uri "$baseUrl/api/v1/health/ready" -Method Get
Write-Output "   Ready: $($ready.status)"

Write-Output "2. Autenticando como OWNER..."
$loginBody = @{ email = $ownerEmail; password = $ownerPassword } | ConvertTo-Json
$loginRes = Invoke-WebRequest -Uri "$baseUrl/api/v1/auth/login" -Method Post -Body $loginBody -ContentType "application/json" -WebSession $session
Write-Output "   Login exitoso (Status: $($loginRes.StatusCode))"

# Obtener cookie CSRF
$csrfCookie = $session.Cookies.GetCookies($baseUrl) | Where-Object { $_.Name -eq "motorscope_csrf" }
$csrfToken = if ($csrfCookie) { $csrfCookie.Value } else { "" }

Write-Output "3. Consultando /api/v1/vehicles..."
$vehiclesRes = Invoke-RestMethod -Uri "$baseUrl/api/v1/vehicles" -Method Get -WebSession $session
Write-Output "   Total vehiculos: $($vehiclesRes.total)"

Write-Output "4. Consultando /api/v1/match-candidates..."
$candidatesRes = Invoke-RestMethod -Uri "$baseUrl/api/v1/match-candidates?status=PENDING" -Method Get -WebSession $session
Write-Output "   Candidatos pendientes: $($candidatesRes.total)"

Write-Output "5. Sincronizando catalogo Mock para refrescar matching..."
$headers = @{ "X-CSRF-Token" = $csrfToken }
$syncRes = Invoke-RestMethod -Uri "$baseUrl/api/v1/sources/mock/sync" -Method Post -Headers $headers -WebSession $session
Write-Output "   Sync Mock Status: $($syncRes.status), Vistos: $($syncRes.listings_seen)"

# Reconsultar candidatos y vehiculos tras sync
$candidatesAfter = Invoke-RestMethod -Uri "$baseUrl/api/v1/match-candidates?status=PENDING" -Method Get -WebSession $session
Write-Output "   Candidatos pendientes tras sync: $($candidatesAfter.total)"

$vehiclesAfter = Invoke-RestMethod -Uri "$baseUrl/api/v1/vehicles" -Method Get -WebSession $session
Write-Output "   Vehiculos tras sync: $($vehiclesAfter.total)"

if ($vehiclesAfter.items.Count -gt 0) {
    $firstVehicle = $vehiclesAfter.items[0]
    $vId = $firstVehicle.id
    Write-Output "6. Probando detalle, historico y valoracion para vehiculo $vId ($($firstVehicle.brand) $($firstVehicle.model))..."

    $detail = Invoke-RestMethod -Uri "$baseUrl/api/v1/vehicles/$vId" -Method Get -WebSession $session
    Write-Output "   Detalle OK: Marca=$($detail.brand), Modelo=$($detail.model), Listings asociados=$($detail.listings.Count)"

    $estimate = Invoke-RestMethod -Uri "$baseUrl/api/v1/vehicles/$vId/market-estimate" -Method Get -WebSession $session
    Write-Output "   Estimacion OK: Estimado=$($estimate.estimated_amount) $($estimate.currency), Comparables=$($estimate.number_of_comparables), Confianza=$($estimate.confidence_score)"

    $history = Invoke-RestMethod -Uri "$baseUrl/api/v1/vehicles/$vId/history" -Method Get -WebSession $session
    Write-Output "   Historico OK: Observaciones=$($history.observations.Count), Dias en mercado=$($history.days_on_market), Variacion=$($history.price_delta_percentage)%"
}

Write-Output "7. Verificando frontend web Next.js..."
$webRes = Invoke-WebRequest -Uri "$baseUrl/" -Method Get
Write-Output "   Web UI Status: $($webRes.StatusCode)"

Write-Output "SMOKE TEST COMPLETADO CON EXITO AL 100%"
