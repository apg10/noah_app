# k8s/scripts/release-backend.ps1
# Build + deploy backend image with immutable tag.
#
# Usage:
#   .\k8s\scripts\release-backend.ps1
#   .\k8s\scripts\release-backend.ps1 -Tag 2026-02-27-r1

param(
  [string]$Namespace = "noah-dev",
  [string]$Deployment = "noah-backend",
  [string]$Container = "backend",
  [string]$ImageRepo = "noah-backend",
  [string]$Tag = ""
)

$ErrorActionPreference = "Stop"

if (-not $Tag) {
  $Tag = (git rev-parse --short HEAD).Trim()
}

$image = "$ImageRepo`:$Tag"

Write-Host "==> Building image $image ..."
docker build -t $image backend

Write-Host "==> Updating deployment image ($Namespace/$Deployment)..."
kubectl -n $Namespace set image "deployment/$Deployment" "$Container=$image" | Out-Null

Write-Host "==> Waiting rollout..."
kubectl -n $Namespace rollout status "deployment/$Deployment" --timeout=240s | Out-Null

$currentImage = kubectl -n $Namespace get deployment $Deployment -o jsonpath="{.spec.template.spec.containers[0].image}"
if ($currentImage -ne $image) {
  throw "Imagen activa inesperada. Esperada: $image / Actual: $currentImage"
}

Write-Host "==> Release backend OK con imagen inmutable: $currentImage"
