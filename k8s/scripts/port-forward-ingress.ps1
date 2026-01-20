# k8s/scripts/port-forward-ingress.ps1
# Port-forward del Ingress NGINX controller a localhost:8080
# Uso: .\k8s\scripts\port-forward-ingress.ps1

$ErrorActionPreference = "Stop"

$Namespace = "ingress-nginx"
$ServiceName = "ingress-nginx-controller"
$LocalPort = 18080
$RemotePort = 80

Write-Host "==> Verificando Ingress Controller ($Namespace/$ServiceName)..."

# Verifica que el service exista
kubectl get svc $ServiceName -n $Namespace | Out-Null

Write-Host "=> Iniciando port-forward: localhost:${LocalPort} -> ${ServiceName}:${RemotePort}"
Write-Host "==> Deja esta ventana abierta. Para detener: Ctrl+C"
Write-Host ""

kubectl -n $Namespace port-forward "svc/$ServiceName" "$LocalPort`:$RemotePort"
