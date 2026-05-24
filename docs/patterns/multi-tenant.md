# Pattern — Modèle multi-tenant (`TenantScopedModel` + RLS)

> Toute nouvelle table contenant des données personnelles doit hériter de `apps.core.models.TenantScopedModel`. La règle est appliquée par la base de données (RLS), pas par convention sociale.

## Decision tree

```
Le modèle stocke-t-il des données personnelles ou liées à un utilisateur ?
├── Oui                 → TenantScopedModel              (subjects: Story 2.x onboarding,
│                                                        recos 3.x, parcours 4.x, outreach 5.x)
└── Non
    ├── C'est un référentiel public partagé entre tenants ?
    │   ├── Oui         → models.Model                   (occupations, formations, schools)
    │   └── Non
    └── C'est de l'audit / supervision ?
        └── Oui         → models.Model                   (audit_logs — voir ADR-0009 §7)
```

**Si en doute :** par défaut `TenantScopedModel`. La sur-protection est sans coût ; la sous-protection coûte un incident.

## Recipe — 5 lignes

```python
from apps.core.models import TenantScopedModel
from django.db import models


class Bulletin(TenantScopedModel):  # ← inherits tenant_id, user_id, created_at, updated_at
    year = models.PositiveSmallIntegerField()
    pdf_s3_key = models.CharField(max_length=512)

    class Meta:
        db_table = "bulletins"
```

C'est tout. À la prochaine migration, ajoute une `RunPython` qui exécute le
`ENABLE/FORCE ROW LEVEL SECURITY` + les policies pour `bulletins`, en
copiant le pattern de `apps/accounts/migrations/0007_enable_rls.py`.

## Save behaviour

| Caller                                     | `user_id` / `tenant_id` source                                           |
|--------------------------------------------|--------------------------------------------------------------------------|
| Django view (authenticated request)        | Auto-rempli depuis `apps.core.request_context` (le middleware T2 le pose) |
| Celery task / shell / `seed_dev.py`        | **Doit** être fourni explicitement OU `save()` lève `ValueError`         |
| Migration `RunPython`                      | Toujours explicite — pas d'auto-fill                                     |

Le fail-loud est volontaire : un job Celery qui crée silencieusement des
rows à `tenant_id = NULL` contourne RLS et finit dans le bucket "aucun
tenant", qui est aussi celui des comptes B2C — mauvaise visibilité.

## Tests

Si ton modèle est `TenantScopedModel`, écris **au moins une paire** de tests
RLS dans `apps/<app>/tests/test_rls_isolation.py` :

1. **Positif** : un row appartenant à `user_a` est invisible quand les GUCs
   pointent sur `user_b`.
2. **Bypass admin** : sous `actor_role = 'path_admin'`, les deux rows
   apparaissent.

Le marker `@pytest.mark.postgresql_only @pytest.mark.rls` les exécute via
`make test-rls`. Le fast path SQLite les skip — ce qui est OK : les tests
applicatifs s'exécutent sur SQLite, les tests d'isolation sur Postgres.

## Anti-patterns

- ❌ **`tenant_id` sur un référentiel public**. Une fiche métier doit être
  visible cross-tenant — sinon Epic 7 SEO casse. Garde `models.Model`.
- ❌ **Audit log héritant de `TenantScopedModel`**. Le DPO est cross-tenant
  by design (ADR-0009 §7).
- ❌ **`SET SESSION` au lieu de `SET LOCAL`** pour les GUCs. Connection
  reuse leak le contexte à la requête suivante.
- ❌ **Compter sur `.filter(tenant_id=…)` seul**. Un test SQLite passe ; un
  bug arrive en prod ; RLS aurait sauvé. Toujours les deux couches.
- ❌ **Tester RLS sous un rôle superuser**. `FORCE ROW LEVEL SECURITY` est
  silencieusement ignoré et tu shippes une fausse garantie. La CI provisionne
  `path_advisor_test` en `NOSUPERUSER NOBYPASSRLS` ; la fixture
  `_assert_non_superuser_in_postgres_lane` plante au démarrage si le rôle
  test peut bypasser.

## References

- [ADR 0010 — Multi-tenant RLS](../adr/0010-multi-tenant-rls.md) — pourquoi cette architecture
- [ADR 0009 — Audit log immuable](../adr/0009-audit-log-immutable-trigger.md) — pourquoi `audit_logs` est exempt
- Migration template : [`apps/api/apps/accounts/migrations/0007_enable_rls.py`](../../apps/api/apps/accounts/migrations/0007_enable_rls.py)
- Base class : [`apps/api/apps/core/models.py`](../../apps/api/apps/core/models.py)
- Middleware : [`apps/api/path_advisor/middleware/tenant.py`](../../apps/api/path_advisor/middleware/tenant.py)
