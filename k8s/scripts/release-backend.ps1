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
  [string]$Tag = "",
  [string]$MigrateJobName = "noah-backend-migrate",
  [string]$MigrateTemplatePath = "k8s/25-backend-migrate-job.yaml"
)

$ErrorActionPreference = "Stop"

if (-not $Tag) {
  $Tag = (git rev-parse --short HEAD).Trim()
}

$image = "$ImageRepo`:$Tag"

Write-Host "==> Building image $image ..."
docker build -t $image backend

if (-not (Test-Path $MigrateTemplatePath)) {
  throw "No se encontro template de migracion: $MigrateTemplatePath"
}

Write-Host "==> Running migration job ($MigrateJobName) with image $image ..."
kubectl -n $Namespace delete job $MigrateJobName --ignore-not-found=true | Out-Null

$template = Get-Content -Path $MigrateTemplatePath -Raw
$jobYaml = $template.Replace("__BACKEND_IMAGE__", $image)
if ($jobYaml -match "__BACKEND_IMAGE__") {
  throw "No se pudo renderizar la imagen en el template de migracion."
}

$jobYaml | kubectl apply -f - | Out-Null

kubectl -n $Namespace wait --for=condition=complete "job/$MigrateJobName" --timeout=300s | Out-Null
if ($LASTEXITCODE -ne 0) {
  Write-Host "==> Migration job fallo. Ultimos logs:"
  kubectl -n $Namespace logs "job/$MigrateJobName" --tail=200
  throw "Migration job no completo correctamente."
}

Write-Host "==> Updating deployment image ($Namespace/$Deployment)..."
kubectl -n $Namespace set image "deployment/$Deployment" "$Container=$image" | Out-Null

Write-Host "==> Waiting rollout..."
kubectl -n $Namespace rollout status "deployment/$Deployment" --timeout=240s | Out-Null

$currentImage = kubectl -n $Namespace get deployment $Deployment -o jsonpath="{.spec.template.spec.containers[0].image}"
if ($currentImage -ne $image) {
  throw "Imagen activa inesperada. Esperada: $image / Actual: $currentImage"
}

Write-Host "==> Release backend OK con imagen inmutable: $currentImage"
