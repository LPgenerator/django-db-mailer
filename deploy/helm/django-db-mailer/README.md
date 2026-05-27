# django-db-mailer Helm chart

Reference Helm chart for the `django-db-mailer` demo project.
The library itself is a Python package on PyPI; this chart packages
the **demo** image as a deployable example.

## Quick start

```bash
helm install dbmail oci://ghcr.io/lpgenerator/charts/django-db-mailer \
    --version 3.0.0 \
    --create-namespace --namespace dbmail \
    -f my-values.yaml
```

## Production checklist

- Externalise secrets via `external-secrets-operator` or
  `sealed-secrets`. Set `existingSecret: my-secret` in values to
  bypass the chart-managed Secret.
- Pin `image.tag` to a digest, not a moving tag.
- `replicaCount.beat` MUST stay at `1` — multiple beat replicas
  duplicate every periodic task.
- Enable `networkPolicy.enabled: true` once your cluster has a
  default-deny baseline.
- Enable `autoscaling` if you have metrics-server installed.
- Provide a real database; do not rely on the in-cluster Postgres
  example for production traffic.

## Migrations

Migrations run as a Helm `pre-install,pre-upgrade` Job (not as an
init-container). This avoids the rolling-deploy race in which two web
replicas hit the database in different schema states.

If a migration fails, the Job pod is left around for `kubectl logs`;
the Helm release is rolled back automatically.

## Tests

```bash
helm test dbmail -n dbmail
```

Runs a single curl Pod against `/admin/login/` and exits 0 when the
web Service answers within 60 seconds.
