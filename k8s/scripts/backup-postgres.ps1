# k8s/scripts/backup-postgres.ps1
# Crea backup logico de Postgres desde el pod y lo descarga a local.
#
# Uso:
#   .\k8s\scripts\backup-postgres.ps1
#   .\k8s\scripts\backup-postgres.ps1 -Namespace noah-dev -OutputDir .\k8s\backups

param(
  [string]$Namespace = "noah-dev",
  [string]$PostgresSelector = "app=postgres",
  [string]$DbUser = "noah",
  [string]$DbName = "noah",
  [string]$OutputDir = "k8s/backups"
)

$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$pod = (kubectl -n $Namespace get pods -l $PostgresSelector -o jsonpath="{.items[0].metadata.name}").Trim()
if (-not $pod) {
  throw "No se encontro pod de Postgres con selector '$PostgresSelector' en namespace '$Namespace'."
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$remoteFile = "/tmp/noah-backup-$timestamp.sql.gz"
$localFile = Join-Path $OutputDir "noah-backup-$timestamp.sql.gz"

Write-Host "==> Generando backup en pod $pod ..."
kubectl -n $Namespace exec $pod -- sh -c "pg_dump --clean --if-exists -U $DbUser -d $DbName | gzip -9 > $remoteFile"

Write-Host "==> Descargando backup a $localFile ..."
kubectl -n $Namespace cp "${pod}:${remoteFile}" $localFile

Write-Host "==> Limpiando archivo temporal en pod ..."
kubectl -n $Namespace exec $pod -- rm -f $remoteFile | Out-Null

Write-Host "==> Backup completado: $localFile"
