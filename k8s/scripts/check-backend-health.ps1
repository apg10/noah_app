# k8s/scripts/check-backend-health.ps1
# Health check operativo para backend:
# - Deployment listo
# - Pods listos
# - Endpoints HTTP healthz/readyz por Ingress
#
# Uso:
#   .\k8s\scripts\check-backend-health.ps1
# Exit code 0 = OK, !=0 = falla (apto para alerta externa).

param(
  [string]$Namespace = "noah-dev",
  [string]$Deployment = "noah-backend",
  [string]$IngressBaseUrl = "http://localhost",
  [string]$HostHeader = "noah.local"
)

$ErrorActionPreference = "Stop"

function Assert-HttpStatus200 {
  param([string]$Path)
  $url = "$IngressBaseUrl$Path"
  $response = & curl.exe -s -i $url -H "Host: $HostHeader"
  if (-not $response) {
    throw "Sin respuesta HTTP para $url"
  }
  $statusLine = ($response -split "`n")[0].Trim()
  if ($statusLine -notmatch " 200 ") {
    throw "HTTP no OK en ${Path}: $statusLine"
  }
}

$desired = (kubectl -n $Namespace get deploy $Deployment -o jsonpath="{.status.replicas}")
$available = (kubectl -n $Namespace get deploy $Deployment -o jsonpath="{.status.availableReplicas}")
if (-not $desired) { $desired = 0 }
if (-not $available) { $available = 0 }

if ([int]$available -lt [int]$desired) {
  throw "Deployment $Deployment no esta listo. desired=$desired available=$available"
}

Assert-HttpStatus200 -Path "/healthz/"
Assert-HttpStatus200 -Path "/readyz/"

Write-Host "OK: backend saludable (deployment + health endpoints)."
exit 0
