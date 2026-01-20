# k8s/scripts/test-ingress.ps1
# Tests de Ingress (requiere que el port-forward esté activo en localhost:8080)
# Uso: .\k8s\scripts\test-ingress.ps1

$ErrorActionPreference = "Stop"

$BaseUrl = "http://localhost:8080"
$HostHeader = "noah.local"

$Endpoints = @(
  "/healthz/",
  "/readyz/"
)

function Test-Endpoint {
  param(
    [string]$Path
  )

  $Url = "$BaseUrl$Path"
  Write-Host "==> Probando: $Url (Host: $HostHeader)"

  # Ejecuta curl.exe y captura salida
  $output = & curl.exe -s -i $Url -H "Host: $HostHeader"

  if (-not $output) {
    throw "Sin respuesta de curl.exe. ¿Está corriendo el port-forward? (port-forward-ingress.ps1)"
  }

  # Primera línea del response: HTTP/1.1 200 OK
  $statusLine = ($output -split "`n")[0].Trim()

  if ($statusLine -notmatch "200") {
    Write-Host $output
    throw "Falló $Path. Status recibido: $statusLine"
  }

  Write-Host "OK -> $statusLine"
  Write-Host ""
}

foreach ($ep in $Endpoints) {
  Test-Endpoint -Path $ep
}

Write-Host "==> Todo OK. Ingress enruta correctamente al backend."
