# k8s/scripts/restore-postgres.ps1
# Restaura un backup .sql.gz en Postgres dentro del cluster.
#
# Uso:
#   .\k8s\scripts\restore-postgres.ps1 -BackupFile .\k8s\backups\noah-backup-20260227-120000.sql.gz

param(
  [Parameter(Mandatory = $true)]
  [string]$BackupFile,
  [string]$Namespace = "noah-dev",
  [string]$PostgresSelector = "app=postgres",
  [string]$DbUser = "noah",
  [string]$DbName = "noah",
  [switch]$RestartBackend = $true,
  [string]$BackendDeployment = "noah-backend"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $BackupFile)) {
  throw "No existe archivo de backup: $BackupFile"
}

$pod = (kubectl -n $Namespace get pods -l $PostgresSelector -o jsonpath="{.items[0].metadata.name}").Trim()
if (-not $pod) {
  throw "No se encontro pod de Postgres con selector '$PostgresSelector' en namespace '$Namespace'."
}

$remoteFile = "/tmp/noah-restore.sql.gz"

Write-Host "==> Subiendo backup al pod $pod ..."
kubectl -n $Namespace cp $BackupFile "${pod}:${remoteFile}"

Write-Host "==> Restaurando base $DbName ..."
kubectl -n $Namespace exec $pod -- sh -c "gunzip -c $remoteFile | psql -v ON_ERROR_STOP=1 -U $DbUser -d $DbName"

Write-Host "==> Limpiando archivo temporal ..."
kubectl -n $Namespace exec $pod -- rm -f $remoteFile | Out-Null

if ($RestartBackend) {
  Write-Host "==> Reiniciando backend para limpiar conexiones ..."
  kubectl -n $Namespace rollout restart "deploy/$BackendDeployment" | Out-Null
  kubectl -n $Namespace rollout status "deploy/$BackendDeployment" --timeout=240s | Out-Null
}

Write-Host "==> Restore completado."
