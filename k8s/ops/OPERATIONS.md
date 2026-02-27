# Backend Operations (Noah)

This document covers minimal ops for backup/restore and health alert checks.

## 1) Postgres Backup

Run:

```powershell
.\k8s\scripts\backup-postgres.ps1
```

Output file is created in `k8s/backups/` with timestamp, for example:
`noah-backup-20260227-120000.sql.gz`.

Notes:
- Backup is logical (`pg_dump --clean --if-exists`).
- Store copies outside local machine (cloud bucket or secure storage).

## 2) Postgres Restore

Run:

```powershell
.\k8s\scripts\restore-postgres.ps1 -BackupFile .\k8s\backups\noah-backup-20260227-120000.sql.gz
```

Default behavior:
- Restore backup into DB `noah`.
- Restart backend deployment after restore.

Before restore in production:
- Put API in maintenance mode or stop writes.
- Confirm backup file checksum.
- Validate restore in a staging namespace first.

## 3) Health Check / Basic Alert Probe

Run:

```powershell
.\k8s\scripts\check-backend-health.ps1
```

What it checks:
- `noah-backend` deployment available replicas >= desired replicas.
- HTTP 200 on `/healthz/` and `/readyz/` via ingress.

Integration tip:
- Schedule this script in CI/cron every 1-5 minutes.
- Trigger alert when exit code is non-zero.

## 4) Recommended Routine

Daily:
- Run health check script.
- Review backend pod restarts and events.

Weekly:
- Create backup and verify file exists + can be decompressed.

Monthly:
- Full restore drill in staging using latest backup.
