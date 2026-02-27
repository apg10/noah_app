# k8s/scripts/test-ingress.ps1
# Tests basicos de Ingress backend.
# Por defecto usa Ingress en http://localhost (Docker Desktop).
# Puedes override con NOAH_INGRESS_BASE_URL o activando port-forward a 18080.
# Uso: .\k8s\scripts\test-ingress.ps1

$ErrorActionPreference = "Stop"

$BaseUrl = if ($env:NOAH_INGRESS_BASE_URL) { $env:NOAH_INGRESS_BASE_URL } else { "http://localhost" }
$HostHeader = "noah.local"

$Tests = @(
  @{ Path = "/healthz/"; Expected = "200" },
  @{ Path = "/readyz/"; Expected = "200" },
  # Debe enrutar al backend (normalmente 401/403 por autenticacion).
  @{ Path = "/api/restaurants/"; Expected = "200|401|403" }
)

function Test-Endpoint {
  param(
    [string]$Path,
    [string]$Expected
  )

  $url = "$BaseUrl$Path"
  Write-Host "==> Probando: $url (Host: $HostHeader)"

  $output = & curl.exe -s -i $url -H "Host: $HostHeader"
  if (-not $output) {
    throw "Sin respuesta de curl.exe. Ejecuta port-forward-ingress.ps1."
  }

  $statusLine = ($output -split "`n")[0].Trim()
  if ($statusLine -notmatch "HTTP/\d\.\d ($Expected)") {
    Write-Host $output
    throw "Fallo $Path. Status recibido: $statusLine. Esperado: $Expected"
  }

  Write-Host "OK -> $statusLine"
  Write-Host ""
}

foreach ($test in $Tests) {
  Test-Endpoint -Path $test.Path -Expected $test.Expected
}

Write-Host "==> Todo OK. Ingress enruta correctamente al backend."
