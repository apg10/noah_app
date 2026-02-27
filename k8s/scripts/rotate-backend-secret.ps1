# k8s/scripts/rotate-backend-secret.ps1
# Rota DJANGO_SECRET_KEY y POSTGRES_PASSWORD en noah-dev sin guardar valores en git.
# Flujo:
# 1) Genera secretos aleatorios.
# 2) Cambia password del usuario noah en Postgres.
# 3) Actualiza Secret noah-backend-secret.
# 4) Reinicia backend y espera rollout.
#
# Uso:
#   .\k8s\scripts\rotate-backend-secret.ps1
#   .\k8s\scripts\rotate-backend-secret.ps1 -Namespace noah-dev

param(
  [string]$Namespace = "noah-dev",
  [string]$PostgresDeployment = "postgres",
  [string]$BackendDeployment = "noah-backend",
  [string]$SecretName = "noah-backend-secret"
)

$ErrorActionPreference = "Stop"

function New-SecureRandomString {
  param([int]$Length = 64)

  $alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_=+"
  $chars = [char[]]$alphabet
  $bytes = New-Object byte[] $Length
  $rng = [System.Security.Cryptography.RNGCryptoServiceProvider]::Create()
  $rng.GetBytes($bytes)
  $rng.Dispose()

  $builder = New-Object System.Text.StringBuilder
  foreach ($b in $bytes) {
    [void]$builder.Append($chars[$b % $chars.Length])
  }
  return $builder.ToString()
}

$djangoSecret = New-SecureRandomString -Length 64
$postgresPassword = New-SecureRandomString -Length 48

Write-Host "==> Rotando password del usuario Postgres (namespace: $Namespace)..."
kubectl -n $Namespace exec "deploy/$PostgresDeployment" -- `
  psql -U noah -d noah -v ON_ERROR_STOP=1 -c "ALTER USER noah WITH PASSWORD '$postgresPassword';" | Out-Null

Write-Host "==> Actualizando Secret $SecretName..."
kubectl -n $Namespace create secret generic $SecretName `
  --from-literal=DJANGO_SECRET_KEY=$djangoSecret `
  --from-literal=POSTGRES_PASSWORD=$postgresPassword `
  --dry-run=client -o yaml | kubectl -n $Namespace apply -f - | Out-Null

Write-Host "==> Reiniciando backend..."
kubectl -n $Namespace rollout restart "deploy/$BackendDeployment" | Out-Null
kubectl -n $Namespace rollout status "deploy/$BackendDeployment" --timeout=240s | Out-Null

Write-Host "==> Secretos rotados y backend en rollout completo."
Write-Host "IMPORTANTE: guarda estos valores en un gestor de secretos externo."
Write-Host "DJANGO_SECRET_KEY=$djangoSecret"
Write-Host "POSTGRES_PASSWORD=$postgresPassword"
