# Deploy with the bundled Helm chart

`dbmail` ships a Helm chart at `deploy/helm/django-db-mailer/`. It is
intended for staging / production deployments of the demo project on
a Kubernetes cluster, but you can adapt it to your own Django project
with minimal changes.

## Prerequisites

- Kubernetes cluster (1.27+ recommended).
- Helm 3.13+.
- A registry push target for the dbmail Docker image (or a
  pre-built image you trust).

## Inspect the chart

```bash
helm show chart deploy/helm/django-db-mailer
helm show values deploy/helm/django-db-mailer | head -60
helm lint deploy/helm/django-db-mailer
```

## Customise values

```yaml
# my-values.yaml
image:
  repository: ghcr.io/your-org/django-db-mailer
  tag: 3.0.0
  pullPolicy: IfNotPresent

replicaCount:
  web: 2
  worker: 4
  beat: 1

env:
  DJANGO_SECRET_KEY:
    valueFrom:
      secretKeyRef: { name: dbmail-secrets, key: secret-key }
  DATABASE_URL:
    valueFrom:
      secretKeyRef: { name: dbmail-secrets, key: database-url }
  REDIS_URL:
    valueFrom:
      secretKeyRef: { name: dbmail-secrets, key: redis-url }
  CELERY_BROKER_URL:
    valueFrom:
      secretKeyRef: { name: dbmail-secrets, key: celery-broker }

resources:
  web:
    requests: { cpu: 100m, memory: 256Mi }
    limits:   { cpu: 500m, memory: 512Mi }
  worker:
    requests: { cpu: 100m, memory: 256Mi }
    limits:   { cpu: 1000m, memory: 1Gi }

ingress:
  enabled: true
  className: nginx
  hosts:
    - host: dbmail.example.com
      paths: [{ path: /, pathType: Prefix }]
  tls:
    - secretName: dbmail-tls
      hosts: [dbmail.example.com]

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

podDisruptionBudget:
  enabled: true
  minAvailable: 1

migrate:
  enabled: true   # pre-install / pre-upgrade Job runs `manage.py migrate`
```

## Create the Secret separately

```bash
kubectl create secret generic dbmail-secrets \
    --namespace=dbmail \
    --from-literal=secret-key="$(openssl rand -hex 32)" \
    --from-literal=database-url="postgres://user:pass@postgres:5432/dbmail" \
    --from-literal=redis-url="redis://redis:6379/0" \
    --from-literal=celery-broker="redis://redis:6379/0"
```

Never bake secrets into `values.yaml` — see the
[security model](../explanation/security.md).

## Install / upgrade

```bash
helm install dbmail deploy/helm/django-db-mailer \
    --namespace dbmail --create-namespace \
    -f my-values.yaml

# subsequent upgrades
helm upgrade dbmail deploy/helm/django-db-mailer -f my-values.yaml
```

The chart deploys:

- `Deployment/web` — gunicorn + Django, behind a `Service` and
  optional `Ingress`.
- `Deployment/celery-worker` — picks tasks from the configured
  Celery queues.
- `Deployment/celery-beat` — single replica, scheduled tasks.
- `Job/migrate` (pre-install / pre-upgrade hook) — runs
  `manage.py migrate --noinput`.
- `HorizontalPodAutoscaler` for web (optional).
- `PodDisruptionBudget` (optional).

## Verify

```bash
kubectl -n dbmail get pods
kubectl -n dbmail logs deploy/celery-worker --tail 50

# Smoke from inside the cluster
kubectl -n dbmail exec deploy/web -- curl -fsSI http://localhost:8000/admin/login/
```

## Rollback

```bash
helm history dbmail
helm rollback dbmail 1
```

## Hardening

- `automountServiceAccountToken: false` is set on every pod by
  default — flip to `true` only if your worker needs the K8s API.
- `seccompProfile: RuntimeDefault`, `readOnlyRootFilesystem: true`,
  `cap_drop: [ALL]` are baked in.
- Optional `NetworkPolicy` is gated behind `networkPolicy.enabled` —
  enable in multi-tenant clusters.

## What is NOT in the chart yet

These items are planned for the 3.1 backlog:

- **Anti-affinity / topology-spread** for celery workers (cookbook
  recipe pending).
- **NetworkPolicy** is gated off by default; the k8s base manifest at
  `deploy/k8s/` has a working policy you can port over.
- **`/health/` endpoint** — current healthcheck hits `/admin/login/`
  (CSRF page, fragile under auth changes).

## See also

- [Helm chart README](../../deploy/helm/django-db-mailer/README.md)
  if it exists in your repo.
- `deploy/k8s/` for raw kustomize manifests (alternative).
- [Security model](../explanation/security.md) — secret handling, threat model.
