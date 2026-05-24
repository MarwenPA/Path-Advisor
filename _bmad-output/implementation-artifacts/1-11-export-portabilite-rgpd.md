# Story 1.11 : Export portabilité RGPD — toutes mes données personnelles

**Epic :** 1 — Foundation : Auth multi-rôle, RBAC, Conformité RGPD & Infra technique
**Status :** done
**Sprint :** 1 (Fondations)
**Story Key :** `1-11-export-portabilite-rgpd`
**Estimation :** L (large) — pose toute l'infrastructure d'export RGPD : modèle `GdprExportRequest`, service orchestrateur, **registry d'exporters par domaine** (extensible aux futures stories 2.3 bulletins / 3.x recos / 4.x parcours / 5.x outreach), tâche Celery de génération asynchrone, chiffrement AES-256 du ZIP (pyzipper), upload S3 (bucket `exports-gdpr` déjà configuré par 1.13), endpoints REST `/api/v1/me/gdpr-exports`, double email (lien + mot de passe envoyés séparément), page UI `/parametres/confidentialite/mes-donnees`, rate limit 1/jour, intégration `@audit_action` (1.13).

> Story 1.11 = **première story RGPD d'écriture côté front + back** après les fondations 1.3 (signup) et 1.13 (audit). Elle livre le pattern d'**exporter registry** que Stories 2.3 (bulletins), 3.x (recos), 4.x (parcours), 5.x (outreach), 6.x (espaces tiers) brancheront sans toucher le moteur d'export. **FR10** (Art. 20 RGPD portabilité) et **NFR-S6** (réponse < 30 jours) sont **adressés par cette story**.

---

## 1. User Story

**As a** élève authentifié (persona Sarah, ≥ 15 ans, ou tout utilisateur quel que soit son rôle),
**I want** télécharger l'intégralité de mes données personnelles dans un format standard, structuré et machine-readable,
**So that** je peux exercer mon droit à la portabilité RGPD (Art. 20) et déplacer mes données vers une autre plateforme ou les conserver pour mes archives.

**Valeur métier :**
- **Conformité légale bloquante** : sans cette feature, Path-Advisor ne peut pas répondre aux demandes Art. 20 RGPD ni satisfaire le délai légal de 30 jours (NFR-S6). Bloque la mise en production B2C.
- **Argument B2B** : les établissements scolaires (DPO interne) exigent que leurs élèves puissent exercer leurs droits avant tout déploiement cohorte (Epic 6).
- **Argument confiance utilisateur** : la portabilité est un signal fort de respect — un élève qui peut récupérer ses données sans friction sera plus à l'aise pour en confier davantage (bulletins, motivations, recos).
- **Pattern fondateur** : l'**exporter registry** posé ici devient le mécanisme canonique par lequel **chaque domaine** futur déclare *"voici mes données pour cet utilisateur"*. Toute story qui ajoute des données personnelles (bulletins 2.3, recos 3.x, outreach 5.x, etc.) doit livrer un exporter conforme — sans cela, l'export est incomplet et viole l'Art. 20.

---

## 2. Acceptance Criteria (BDD)

### AC1 — Modèle `GdprExportRequest` + cycle de vie

**Given** la table `gdpr_export_requests` créée par la migration `apps/accounts/migrations/000X_gdpr_export_request.py`
**When** je consulte le schéma PostgreSQL
**Then** la table contient les colonnes suivantes (snake_case end-to-end, cf. ADR-0006) :
- `id` (CharField PK, ULID préfixé `gex_`, généré via `apps.core.ids.generate_id("gex")`)
- `user_id` (CharField FK logique vers `users.id`, indexé — **pas** de contrainte FK pour survivre à un hard-delete RGPD 1.12 ; un export d'un compte supprimé reste téléchargeable 7 jours)
- `status` (CharField max 20, indexé — `pending` | `in_progress` | `ready` | `expired` | `failed`)
- `requested_at` (DateTimeField, `auto_now_add=True`, indexé)
- `started_at` (DateTimeField, nullable — fixé au pickup par Celery worker)
- `ready_at` (DateTimeField, nullable — fixé quand status passe à `ready`)
- `expires_at` (DateTimeField, nullable — `ready_at + 7 jours`, fixé en même temps que `ready_at`)
- `archive_s3_key` (CharField max 512, nullable — chemin S3 du ZIP chiffré)
- `manifest_s3_key` (CharField max 512, nullable — chemin S3 du manifest JSON détaillant le contenu)
- `archive_sha256` (CharField max 64, nullable — hash SHA-256 du ZIP avant chiffrement, pour intégrité)
- `archive_size_bytes` (BigIntegerField, nullable)
- `password_hash` (CharField max 128, nullable — hash Django (`make_password`) du mot de passe de l'archive ; le mot de passe en clair est uniquement transmis par email et **jamais** persisté)
- `error_code` (CharField max 50, nullable — code stable `domain.action` du dernier échec)
- `error_message` (TextField, nullable — message d'erreur sans PII, pour support)
- `download_count` (PositiveIntegerField, default 0 — incrémenté à chaque GET sur `/download`)
- `last_downloaded_at` (DateTimeField, nullable)

**And** les index suivants existent :
- `idx_gdpr_exports_user_id_requested_at` (user_id, requested_at DESC)
- `idx_gdpr_exports_status_expires_at` (status, expires_at) — pour le balayage Celery de l'expiration
- Index par défaut Django sur PK

**And** **aucun champ `tenant_id`** : un export RGPD est une demande individuelle, pas une donnée multi-tenant (un utilisateur B2B peut avoir un tenant_id mais son export reste personnel à lui).
**And** la table est `db_table = "gdpr_export_requests"` (pluriel, snake_case).

**Given** un utilisateur authentifié sans demande en cours
**When** il crée une demande
**Then** une ligne `status=pending` est créée et la tâche Celery `gdpr.build_export` est planifiée (`.delay(export_id=...)`).

**Given** un utilisateur qui a déjà une demande `pending` ou `in_progress`
**When** il tente de créer une seconde demande
**Then** l'endpoint POST retourne `409 Conflict` au format RFC 7807 :
```json
{
  "type": "https://path-advisor.fr/errors/gdpr-export-in-progress",
  "title": "Demande d'export en cours",
  "status": 409,
  "detail": "Une demande d'export est déjà en cours pour votre compte. Patientez jusqu'à sa complétion (max 30 minutes)."
}
```
**And** aucune nouvelle ligne n'est créée.

### AC2 — Rate limit : 1 export `ready` ou `pending` par utilisateur par 24 h

**Given** un utilisateur dont la dernière demande `ready` ou `pending`/`in_progress` date de moins de 24 h
**When** il tente de créer une nouvelle demande
**Then** l'endpoint POST retourne `429 Too Many Requests` au format RFC 7807 :
```json
{
  "type": "https://path-advisor.fr/errors/gdpr-export-rate-limited",
  "title": "Délai entre exports non écoulé",
  "status": 429,
  "detail": "Vous avez déjà demandé un export il y a moins de 24 heures. Réessayez après {retry_after_iso8601}.",
  "retry_after_seconds": 12345
}
```

**Rationale :** un export RGPD est coûteux (CPU, I/O S3, bande passante, place disque). Sans cap, un script abusif déclenche un DoS interne. NFR-S6 demande "réponse < 30 jours" — 1/jour reste largement dans la conformité légale. Un échec `failed` ne consomme PAS le quota (l'utilisateur peut retenter immédiatement après une erreur système).

### AC3 — Endpoints REST `/api/v1/me/gdpr-exports`

**Authentification :** session cookie Django (cf. ADR-0004) + CSRF token sur mutations. Tous les rôles sont éligibles (`student`, `parent`, `counselor`, `school_admin`, `path_admin`) — chacun ne voit **que ses propres demandes**.

**Verbes et payloads :**

| Méthode | URL | Réponse OK | Description |
|---|---|---|---|
| `POST` | `/api/v1/me/gdpr-exports` | `202 Accepted` + body ci-dessous | Crée une demande, planifie Celery, retourne l'`id` |
| `GET` | `/api/v1/me/gdpr-exports` | `200 OK` + liste paginée (CursorPagination) | Mes demandes (les 90 derniers jours, triées DESC) |
| `GET` | `/api/v1/me/gdpr-exports/{id}` | `200 OK` + détail | Statut d'une demande spécifique |
| `GET` | `/api/v1/me/gdpr-exports/{id}/download` | `302 Found` + `Location: <presigned-url>` | Redirige vers URL S3 presignée valide 5 min (lien interne) |

**Body de réponse `POST` / `GET /{id}` (snake_case) :**
```json
{
  "id": "gex_01HXJ7...",
  "status": "pending",
  "requested_at": "2026-05-17T14:30:00Z",
  "ready_at": null,
  "expires_at": null,
  "download_count": 0,
  "estimated_ready_at": "2026-05-17T15:00:00Z",
  "error_code": null,
  "error_message": null
}
```

**Règles métier :**
- `POST` est **idempotent par fenêtre 24h** : un second POST dans la fenêtre rate-limit retourne `429` (cf. AC2), pas une 2e ligne.
- `GET /{id}` retourne `404 Not Found` si l'`id` n'appartient pas à l'utilisateur courant (jamais 403 — on ne révèle pas l'existence d'IDs tiers).
- `GET /{id}/download` retourne `404` si `status != ready`, `410 Gone` si `status == expired`, `403` si `download_count >= 10` (cap anti-abus).
- L'URL S3 presignée est générée à la demande (TTL 5 min), pas stockée. Le `Location: ...` est en HTTPS strict (NFR-S1).
- Le `download_count` est **incrémenté côté view** (pas dans un middleware S3) — un `302` non suivi n'incrémente PAS, mais un téléchargement effectif sera tracé par l'audit log et les logs S3.
- L'endpoint `download` est **audité** : `record_audit(action="gdpr.export_downloaded", subject_id=user.id, metadata={"export_id": ..., "download_count": ...})`.

**Erreurs RFC 7807 — types complets :**
- `https://path-advisor.fr/errors/gdpr-export-not-found` (404)
- `https://path-advisor.fr/errors/gdpr-export-expired` (410)
- `https://path-advisor.fr/errors/gdpr-export-not-ready` (404, `detail="Export pas encore prêt. Statut: in_progress."`)
- `https://path-advisor.fr/errors/gdpr-export-in-progress` (409, cf. AC1)
- `https://path-advisor.fr/errors/gdpr-export-rate-limited` (429, cf. AC2)
- `https://path-advisor.fr/errors/gdpr-export-download-cap` (403)
- `https://path-advisor.fr/errors/gdpr-export-failed` (statut `failed` exposé dans GET — pas une erreur HTTP)

### AC4 — Exporter registry : pattern extensible par story

**Given** le module `apps/accounts/exporters/__init__.py` qui définit :
```python
ExporterFn = Callable[[User], Iterable[ExporterEntry]]

@dataclass
class ExporterEntry:
    """One artifact in the ZIP: a path inside the archive + binary content + content_type."""
    archive_path: str  # ex: "profile/profile.json", "audit/audit-log.jsonl"
    content: bytes
    content_type: str  # ex: "application/json", "application/pdf"

_REGISTRY: dict[str, ExporterFn] = {}

def register_exporter(domain: str) -> Callable[[ExporterFn], ExporterFn]:
    """Decorator. Usage: @register_exporter("audit") on the exporter fn."""
    def decorator(fn: ExporterFn) -> ExporterFn:
        if domain in _REGISTRY:
            raise ValueError(f"Exporter for domain '{domain}' already registered")
        _REGISTRY[domain] = fn
        return fn
    return decorator

def iter_exporters() -> Iterable[tuple[str, ExporterFn]]:
    return tuple(_REGISTRY.items())
```

**When** une story future (ex. 2.3 bulletins) veut contribuer ses données à l'export
**Then** elle crée `apps/profiles/exporters.py` :
```python
from apps.accounts.exporters import register_exporter, ExporterEntry

@register_exporter("bulletins")
def export_bulletins(user: User) -> Iterable[ExporterEntry]:
    for bulletin in Bulletin.objects.filter(student__user=user).iterator():
        with bulletin.encrypted_file.open("rb") as f:
            yield ExporterEntry(
                archive_path=f"bulletins/{bulletin.year}/{bulletin.id}.pdf",
                content=f.read(),
                content_type="application/pdf",
            )
```

**And** elle ajoute son app à `EXPORTER_APPS` (ou bien le mécanisme `AppConfig.ready()` charge l'`exporters` module automatiquement) — l'export inclura ses données dès l'appli installée, **sans modification du moteur d'export**.

**Story 1.11 livre 2 exporters initiaux :**

1. **`accounts`** — profil utilisateur :
   ```json
   // profile/profile.json
   {
     "id": "usr_01...",
     "email": "sarah@example.fr",
     "role": "student",
     "birth_date": "2008-03-15",
     "status": "active",
     "email_verified_at": "2026-05-13T10:22:00Z",
     "consent_rgpd_at": "2026-05-13T10:18:00Z",
     "consent_cgu_version": "2026-05-15",
     "tenant_id": null,
     "created_at": "2026-05-13T10:18:00Z",
     "updated_at": "2026-05-17T14:30:00Z"
   }
   ```
   Format : JSON UTF-8, indenté 2 espaces, clés snake_case, dates ISO 8601 UTC.

2. **`audit`** — entrées du journal d'audit où l'utilisateur est `subject_id` OU `actor_id` :
   ```jsonl
   // audit/audit-log.jsonl
   {"id":"aud_01...","created_at":"2026-05-13T10:18:00Z","action":"user.signed_up","result":"success","actor_id":"usr_01...","subject_id":"usr_01...","metadata":{"role":"student"}}
   {"id":"aud_02...","created_at":"2026-05-13T10:22:00Z","action":"user.email_verified","result":"success","actor_id":"usr_01...","subject_id":"usr_01...","metadata":{}}
   ```
   Format : JSON Lines UTF-8, un événement par ligne, ordre chronologique ASC, jamais de `row_hash`/`prev_hash` (interne à l'audit, pas pertinent pour l'utilisateur final).

**Given** un utilisateur sans données dans un domaine donné (ex. pas encore de bulletins, pas encore de recos)
**When** son exporter est appelé
**Then** il retourne `[]` (itérable vide) — **PAS** d'exception. Le ZIP final contient simplement moins de fichiers.

### AC5 — Tâche Celery `gdpr.build_export` : construction ZIP chiffré + upload S3

**Given** une `GdprExportRequest` `status=pending`
**When** la tâche `gdpr.build_export(export_id=...)` est exécutée
**Then** la tâche enchaîne :

1. **Charge la demande**, vérifie qu'elle est encore `pending` (sinon log + return — idempotence vs double-fire Celery beat). Bascule à `status=in_progress`, set `started_at=now()`.
2. **Génère un mot de passe** : `secrets.token_urlsafe(24)` (≥ 32 chars, 192 bits d'entropie). Persiste `password_hash = make_password(password)`. Le mot de passe en clair est **uniquement** présent en mémoire pour l'étape 5.
3. **Itère sur `iter_exporters()`** dans un ordre stable (alphabétique par domaine pour la reproductibilité). Pour chaque domaine :
   - Capture les exceptions d'un exporter individuel → log + Sentry + saute le domaine. Un exporter cassé ne doit pas avaler les autres (NFR-R4 dégradation gracieuse). Ajoute `errors/{domain}.error.txt` au ZIP avec le message d'erreur public-safe.
   - Streame chaque `ExporterEntry` directement dans le ZIP (pas de buffer mémoire global — un futur exporter bulletins peut produire 100+ MB).
4. **Ajoute le manifest** `manifest.json` à la racine de l'archive :
   ```json
   {
     "schema_version": "1.0",
     "format": "ISO Article 20 RGPD — structured, machine-readable, commonly used",
     "user_id": "usr_01...",
     "generated_at": "2026-05-17T15:00:00Z",
     "domains": [
       {"name": "accounts", "entries": 1, "errors": 0},
       {"name": "audit", "entries": 47, "errors": 0}
     ],
     "files": [
       {"path": "profile/profile.json", "size_bytes": 412, "sha256": "ab12..."},
       {"path": "audit/audit-log.jsonl", "size_bytes": 8244, "sha256": "cd34..."}
     ]
   }
   ```
   Et `README.txt` à la racine :
   ```
   Path-Advisor — Export RGPD (Article 20)
   =======================================
   Cet export contient l'intégralité de vos données personnelles détenues par Path-Advisor au moment de la génération.

   Fichiers inclus :
   - profile/profile.json — votre profil utilisateur
   - audit/audit-log.jsonl — l'historique des accès à vos données
   - manifest.json — description technique de cet export
   - (autres dossiers selon les fonctionnalités que vous avez utilisées)

   Pour toute question : dpo@path-advisor.fr
   ```
5. **Chiffre l'archive en AES-256** via `pyzipper.AESZipFile(..., encryption=pyzipper.WZ_AES, compression=pyzipper.ZIP_DEFLATED)`. Le mot de passe (étape 2) est appliqué à TOUS les fichiers du ZIP. Note : ZIP encryption AES-256 est lisible par 7-Zip, WinRAR, Keka, Archive Utility récents — pas le ZIP natif Windows (qui ne supporte que ZipCrypto).
6. **Calcule `archive_sha256`** sur le ZIP chiffré (pour intégrité, pas pour vérification utilisateur).
7. **Upload vers S3** :
   - Bucket : `settings.GDPR_EXPORTS_BUCKET` (default `exports-gdpr`, partagé avec audit exports — cf. §4.5)
   - Key : `gdpr-exports/{user_id}/{export_id}.zip`
   - `ServerSideEncryption="AES256"` (défense en profondeur — le ZIP est déjà chiffré, mais NFR-S1 exige aussi le chiffrement au repos côté S3)
   - `ContentType="application/zip"`
   - `Metadata={"export_id": ..., "user_id": ..., "schema_version": "1.0"}`
8. **Persiste l'état final** : `status=ready`, `ready_at=now()`, `expires_at=now() + 7 days`, `archive_s3_key`, `archive_sha256`, `archive_size_bytes`.
9. **Émet l'audit** `record_audit(action="gdpr.export_ready", subject_id=user.id, metadata={"export_id": ..., "size_bytes": ..., "domains": [...]})`.
10. **Planifie les deux emails séparés** (cf. AC6) : `send_gdpr_export_link_email.delay(export_id)` puis `send_gdpr_export_password_email.delay(export_id, password=password)`. Le mot de passe en clair traverse Celery via argument de tâche (pas idéal mais acceptable MVP : broker Redis local-only / TLS en prod, pas de persistance hors Redis short-lived). En growth, migrer vers un secret-vault one-shot.

**Given** un échec d'un sous-étape critique (S3 down, ZIP corrupted, OOM)
**When** la tâche lève une exception
**Then** :
- `status=failed`, `error_code=<domain>.<action>`, `error_message=<sanitized>`.
- Sentry capture.
- **PAS** de retry automatique en MVP (un export peut être très lourd ; retry naïf = double-charge S3). L'utilisateur recevra un email "ton export a échoué, retente dans quelques minutes" (cf. AC6 fallback).
- Le quota 24h n'est PAS consommé sur `failed`.

**Idempotence :** la tâche commence par vérifier `status == pending` et se no-op sinon. Un double-fire (Celery beat / retry manuel / replay) ne produit pas deux ZIPs.

### AC6 — Notifications email : lien + mot de passe envoyés séparément

**Given** un export `status=ready`
**When** la tâche Celery termine
**Then** **deux emails distincts** sont envoyés à l'utilisateur via le backend email standard (Mailpit en local, Postmark en prod via `DEFAULT_FROM_EMAIL`) :

**Email 1 — `path_advisor/templates/accounts/email/gdpr_export_ready.html` :**
- Sujet : `[Path-Advisor] Ton export RGPD est prêt`
- Contenu :
  - Lien vers `/parametres/confidentialite/mes-donnees/{export_id}` (pas l'URL S3 directe — passe par le front authentifié)
  - Date d'expiration explicite : "Lien valable jusqu'au {{expires_at}} (7 jours)"
  - Mention "Tu recevras le mot de passe pour ouvrir l'archive dans un email séparé"
  - Lien `dpo@path-advisor.fr` pour assistance
  - Pied de page conforme RGPD (mention CNIL, possibilité d'opposition)

**Email 2 — `path_advisor/templates/accounts/email/gdpr_export_password.html` :**
- Sujet : `[Path-Advisor] Mot de passe de ton export RGPD`
- Contenu :
  - **Mot de passe en clair** dans un bloc copiable (`<pre>`)
  - Avertissement : "Conserve ce mot de passe en sécurité. Path-Advisor ne peut PAS le récupérer si tu le perds (nous ne stockons qu'un hash, pas le mot de passe lui-même)."
  - Mention "Mot de passe à utiliser avec 7-Zip, Keka (Mac), ou WinRAR. Le ZIP natif Windows ne supporte pas l'AES-256."
  - Lien vers FAQ `docs/runbooks/gdpr-request.md` (à créer dans cette story — cf. §T7)

**Séparation temporelle :** les 2 emails sont planifiés à 30 secondes d'intervalle (`countdown=30` sur le 2e) pour réduire la probabilité d'arriver dans la même conversation Gmail / le même push notification batch. Pas une garantie cryptographique, juste un effort raisonnable.

**Given** un échec d'envoi email
**When** Postmark/SMTP retourne une erreur
**Then** la tâche `send_gdpr_export_*_email` retry avec backoff exponentiel (3 tentatives, 60s/300s/1800s) — cf. pattern Celery standard. L'export reste `status=ready` (le ZIP est en S3, l'utilisateur peut voir l'état dans l'UI même si l'email a échoué).

**Given** un export `status=failed`
**When** la tâche échoue
**Then** un seul email `gdpr_export_failed.html` est envoyé à l'utilisateur (sans mot de passe, sans lien) — "ton export a échoué, retente dans quelques minutes ou contacte dpo@path-advisor.fr".

### AC7 — Expiration automatique après 7 jours

**Given** un export `status=ready` dont `expires_at < now()`
**When** la tâche Celery beat `gdpr.expire_old_exports` s'exécute (planning quotidien 04:00 UTC)
**Then** pour chaque export expiré :
- Le ZIP est **supprimé de S3** (`s3.delete_object(Bucket=..., Key=archive_s3_key)`)
- Le `manifest_s3_key` est aussi supprimé si présent
- `status=expired`, `archive_s3_key=None`, `manifest_s3_key=None`, `archive_size_bytes=None`
- `password_hash` est conservé (pas de PII, et utile pour distinguer entre "jamais demandé" et "expiré sans téléchargement")
- `record_audit(action="gdpr.export_expired", subject_id=user.id, metadata={"export_id": ..., "downloaded": download_count > 0})`

**Rationale :** l'AC §AC1 demande 7 jours de validité explicite. Conserver le ZIP au-delà = surface d'attaque + coût stockage. La ligne `GdprExportRequest` reste en DB pour l'historique côté utilisateur ("j'ai exporté il y a 6 mois") et pour respect du quota.

**Idempotence :** si une expiration tourne deux fois sur la même ligne (status déjà `expired`), elle no-op.

### AC8 — UI front : page `/parametres/confidentialite/mes-donnees`

**Given** un utilisateur authentifié sur `/parametres/confidentialite`
**When** il consulte la page
**Then** il voit une carte "Mes données personnelles" avec :
- Un texte d'explication court (≤ 3 lignes) : "Conformément au RGPD (Art. 20), tu peux récupérer toutes les données personnelles que Path-Advisor détient sur toi, dans un format standard."
- Un bouton "Exporter mes données" — disabled si une demande est `pending` ou `in_progress`
- Un lien "Mes exports précédents →" vers `/parametres/confidentialite/mes-donnees`

**Given** un utilisateur sur `/parametres/confidentialite/mes-donnees`
**When** la page charge
**Then** elle affiche :
- Si aucune demande : un état vide avec le bouton "Demander un export"
- Si demande(s) existante(s) : une liste triée DESC par `requested_at`, chaque ligne montrant :
  - L'horodatage relatif ("Il y a 3 minutes", "Hier", "Le 10 mai 2026") + l'horodatage absolu en tooltip
  - Le statut avec un badge coloré (`pending` jaune, `in_progress` jaune avec spinner, `ready` vert, `expired` gris, `failed` rouge)
  - Pour `pending`/`in_progress` : un `ScenarioLoader` (cf. composant Story 2.8 — fallback : `<Skeleton />` shadcn si pas encore livré) avec message "Préparation de ton export, sous 30 minutes max"
  - Pour `ready` : bouton "Télécharger" qui ouvre `/api/v1/me/gdpr-exports/{id}/download` dans un nouvel onglet
  - Pour `ready` : compteur "X téléchargements / 10 max", info "expire le {date}"
  - Pour `expired` : tooltip "Ce lien a expiré. Demande un nouvel export pour récupérer tes données."
  - Pour `failed` : message d'erreur + bouton "Réessayer" (nouveau POST, qui marche car `failed` ne consomme pas le quota)

**Polling :** la page utilise `useQuery` TanStack Query avec `refetchInterval: 5000` UNIQUEMENT si une demande est `pending` ou `in_progress` ; sinon pas de polling (charge serveur minimale).

**A11y :**
- Boutons ont des labels explicites (`aria-label="Télécharger l'export du 15 mai 2026"`)
- Le badge de statut a un texte (pas couleur-seulement) → conformité RGAA NFR-A1
- Le `ScenarioLoader` annonce le statut via `aria-live="polite"`
- Navigation clavier complète (Tab + Enter)

**i18n :** tous les textes via `next-intl` namespace `gdpr` (fichier `apps/web/messages/fr.json`). Pas de hard-coded FR strings.

### AC9 — Audit : 3 événements émis

**Given** l'intégration avec Story 1.13
**When** les actions de la story s'exécutent
**Then** les événements suivants sont émis dans `audit_logs` :

| Action | Quand | Acteur | Subject | Metadata |
|---|---|---|---|---|
| `gdpr.export_requested` | POST `/api/v1/me/gdpr-exports` (status=200) | user.id | user.id | `{"export_id": "gex_..."}` |
| `gdpr.export_ready` | Fin de `gdpr.build_export` task | (système, actor_id=None) | user.id | `{"export_id": ..., "size_bytes": ..., "domains": ["accounts", "audit"]}` |
| `gdpr.export_downloaded` | GET `/api/v1/me/gdpr-exports/{id}/download` (302) | user.id | user.id | `{"export_id": ..., "download_count": ...}` |
| `gdpr.export_expired` | Tâche Celery `expire_old_exports` | (système, actor_id=None) | user.id | `{"export_id": ..., "downloaded": bool}` |
| `gdpr.export_failed` | Exception dans `gdpr.build_export` | (système) | user.id | `{"export_id": ..., "error_code": ...}` |

**Pattern d'intégration :** le service `GdprExportService.request_export(user)` est décoré `@audit_action("gdpr.export_requested", subject_from=lambda kwargs, ret: ret.user_id, metadata_from=lambda kwargs, ret: {"export_id": ret.id})`. Les autres événements sont émis via `record_audit(...)` directement depuis la tâche/le view (pas de fonction service à wrapper proprement pour les transitions Celery).

### AC10 — Tests bout-en-bout

**Given** l'arborescence `apps/api/apps/accounts/tests/test_gdpr_*.py`
**When** `pytest apps/accounts/tests/test_gdpr_*` est exécuté
**Then** les tests suivants existent et passent :

1. **`test_gdpr_models.py`** — création, transitions valides/invalides, contraintes DB
2. **`test_gdpr_exporters.py`** — registry register/duplicate, exporter `accounts` retourne bon JSON, exporter `audit` filtre bien `subject_id|actor_id == user.id`
3. **`test_gdpr_service.py`** — orchestration ZIP, idempotence Celery, gestion erreur exporter individuel
4. **`test_gdpr_views.py`** — auth required, 409 si pending existe, 429 si rate-limited, 404 pour id d'un autre user, 410 pour expired, 302 vers presigned URL pour ready, audit log entries créés
5. **`test_gdpr_tasks.py`** — build_export happy path + failure path (S3 down mocké), expire_old_exports supprime de S3 (mocké), idempotence sur double-fire
6. **`test_gdpr_emails.py`** — 2 emails séparés envoyés, contenu des templates, password présent uniquement dans le 2e
7. **`test_gdpr_encryption.py`** — le ZIP est ouvrable avec le mot de passe en clair généré ; n'est PAS ouvrable sans

**Tests front (apps/web/src/...) :**

8. **Vitest** — `gdpr-export-card.test.tsx`, `mes-donnees-page.test.tsx` (rendu des 5 statuts, polling actif uniquement si pending)
9. **Playwright `e2e/gdpr-export.spec.ts`** — parcours complet : login → page paramètres → clic export → attente status ready (mock Celery sync via `CELERY_TASK_ALWAYS_EAGER=True`) → clic télécharger → 302 → vérif que le ZIP est téléchargé et n'est PAS un texte d'erreur.

Couverture pytest cible **≥ 90 %** sur `apps/accounts/services/gdpr_service.py`, `apps/accounts/exporters/*.py`, `apps/accounts/tasks.py` (sections gdpr). NFR-M2 exige ≥ 70 % global, mais zone RGPD = critique → plus strict.

---

## 3. Developer Context Section

### 3.1 Vue d'ensemble : ce qui existe DÉJÀ

**Tu n'as PAS à recoder, tu BRANCHES sur :**

- **User model** [apps/api/apps/accounts/models.py](apps/api/apps/accounts/models.py) — Story 1.3. Champs : `id` (ULID `usr_`), `email`, `role`, `birth_date`, `consent_rgpd_at`, `consent_cgu_version`, `tenant_id`, `email_verified_at`, `created_at`, `updated_at`, `deleted_at`. **N'AJOUTE PAS de champ ici** — la `GdprExportRequest` est une nouvelle table.
- **AuditLog model** [apps/api/apps/audit/models.py](apps/api/apps/audit/models.py) — Story 1.13. Tu peux requêter `AuditLog.objects.filter(Q(subject_id=user.id) | Q(actor_id=user.id))` pour l'exporter `audit`. **Ne touche PAS aux managers immuables** — l'export est en lecture seule.
- **`@audit_action` decorator + `record_audit` helper** [apps/api/apps/audit/decorators.py](apps/api/apps/audit/decorators.py) — pattern canonique. Utilise `@audit_action("gdpr.export_requested")` sur ton service de création.
- **`generate_id("gex")`** [apps/api/apps/core/ids.py](apps/api/apps/core/ids.py) — ULID préfixé. Préfixe choisi : `gex_` (gdpr-export). **Vérifie qu'il n'est pas déjà utilisé** dans `apps/core/ids.py` ; si oui, choisis `gdx_` ou similaire.
- **`DomainError` hierarchy** [apps/api/apps/core/exceptions.py](apps/api/apps/core/exceptions.py) — toutes les erreurs métier de la story héritent de `DomainError`. Crée `GdprExportError`, `GdprExportInProgress`, `GdprExportRateLimited`, `GdprExportNotReady`, `GdprExportExpired`, `GdprExportDownloadCap`, `GdprExportFailed` (5+ classes — regroupe sous un seul fichier `apps/accounts/gdpr_exceptions.py` plutôt que polluer `core/exceptions.py`).
- **RFC 7807 handler** déjà branché côté DRF (Story 1.13 / 1.3). Les `DomainError` sont auto-converties en `application/problem+json`. **Tu ne crées PAS de handler**, tu lèves la bonne exception.
- **Settings S3 / MinIO** [apps/api/path_advisor/settings/base.py](apps/api/path_advisor/settings/base.py) — `AWS_S3_ENDPOINT_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_S3_REGION_NAME`, `AUDIT_EXPORTS_BUCKET="exports-gdpr"`. **Réutilise** `AUDIT_EXPORTS_BUCKET` ou ajoute un alias `GDPR_EXPORTS_BUCKET` (default identique) — cf. §4.5 pour la décision.
- **`AUDIT_EXPORT_PRESIGNED_TTL_SECONDS=7*24*3600`** — déjà défini. Ajoute `GDPR_EXPORT_DOWNLOAD_PRESIGNED_TTL_SECONDS=300` (5 min) pour le presigned URL du `download` endpoint (différent du TTL "valable 7 jours" qui est géré par `expires_at` côté DB).
- **`_s3_client()` helper** [apps/api/apps/audit/services/archive_service.py](apps/api/apps/audit/services/archive_service.py) — boto3 configuré. **Duplique-le** dans `apps/accounts/services/gdpr_service.py` (ne le déplace pas vers `core/` — c'est de la duplication acceptable MVP) OU déplace-le vers `apps/core/storage.py` si tu veux le mutualiser (préfère le déplacement si tu vois que la signature est identique). **Décision recommandée : duplique pour cette story, ne refactore PAS** — un refactor cross-app prématuré complique la PR review.
- **Celery beat** [apps/api/path_advisor/celery.py](apps/api/path_advisor/celery.py) — ajoute l'entrée `"gdpr-expire-old-exports": {"task": "gdpr.expire_old_exports", "schedule": crontab(hour=4, minute=0)}` à `beat_schedule`. Le pattern de prerun/postrun pour `request_context.clear()` est déjà en place — tu ne le retouches PAS.
- **Mailpit / SMTP backend** — déjà configuré local. `send_mail()` Django marche out-of-the-box. **N'ajoute PAS** d'abstraction nouvelle (pas de service `EmailService` à créer — c'est Story 8.1).
- **`apiFetch` client front** [apps/web/src/lib/api/](apps/web/src/lib/api/) — wrapper standardisé Story 1.3. **Utilise-le** pour POST/GET les endpoints, JAMAIS `fetch` brut (cf. règle d'enforcement architecture).
- **shadcn/ui** Button, Card, Badge, Skeleton, Tooltip — tous installés. **Réutilise-les**, ne crée pas de variantes custom.

### 3.2 Pièges identifiés (DON'T DO)

- ❌ **Ne mets PAS la business logic dans la view DRF.** ViewSets thin → délègue à `GdprExportService` (cf. règle architecture "business logic dans services/, pas dans views").
- ❌ **Ne wrappe PAS chaque event dans `@audit_action`.** Le décorateur est pour les services côté Django ; pour les transitions internes Celery (ready/failed/expired), utilise `record_audit(...)` direct. Wrapper un Celery task entier en `@audit_action` produirait un audit "audit_action returned" qui n'a aucun sens.
- ❌ **Ne stocke PAS le mot de passe en clair en DB ni dans Sentry ni dans les logs.** Uniquement en mémoire pendant la durée de la tâche + dans le 2e email. `password_hash` via `django.contrib.auth.hashers.make_password` (Argon2 par défaut).
- ❌ **Ne télécharge PAS l'archive entièrement en mémoire côté Django avant d'uploader vers S3.** Streame via `boto3.client.upload_fileobj()` avec un `BytesIO` reconstitué OU mieux : écris dans un `tempfile.NamedTemporaryFile()` puis upload en streaming. Un export bulletins futur peut faire 200 MB.
- ❌ **Ne mets PAS de FK contrainte `ON DELETE CASCADE` entre `GdprExportRequest.user_id` et `User`.** L'export doit survivre 7 jours à un hard-delete RGPD (Story 1.12). FK logique uniquement (`CharField` indexé), pas de contrainte DB.
- ❌ **Ne re-déclenche PAS l'envoi des emails si la tâche est ré-exécutée** (idempotence). Ajoute un champ `emails_sent_at` ou guard sur `status == ready and emails_sent_at is None` avant `send_email.delay()`. **OU** : passe les emails comme étape SÉPARÉE de `build_export` qui ne se déclenche que sur transition `in_progress → ready`. La 2e approche est plus propre — `build_export` produit le ZIP, `notify_export_ready` envoie les emails et est appelée UNE FOIS.
- ❌ **N'utilise PAS `zipfile.ZipFile` natif Python pour le chiffrement.** Python stdlib `zipfile` ne supporte PAS l'AES, uniquement le ZipCrypto vulnérable (broken par known-plaintext attacks depuis 2003). **Utilise `pyzipper`** — drop-in replacement avec AES support.
- ❌ **Ne fais PAS du polling agressif côté front** (`refetchInterval: 500`). 5 secondes minimum, et **uniquement** si le statut est `pending`/`in_progress`. Sinon coupe le polling — un export `ready` ne change plus.
- ❌ **N'expose PAS l'URL S3 directement** à l'utilisateur dans le JSON de réponse `GET /{id}`. Le presigned URL est généré uniquement à l'instant du `GET /download` et inclus dans le `Location` header de la redirection. Sinon le download_count ne s'incrémente pas et l'audit n'est pas tracé.
- ❌ **Ne crée PAS d'app Django `apps/gdpr/`** séparée. La logique vit dans `apps/accounts/` (FR1-FR12 cluster). Le seul "split" est `apps/accounts/exporters/` qui est un sous-module destiné à recevoir des contributions cross-app via un pattern AppConfig.ready() — mais ces contributions futures vivent dans `apps/profiles/exporters.py`, `apps/recommendations/exporters.py`, etc., pas dans `apps/accounts/`.
- ❌ **Ne mets PAS le bouton "Exporter mes données" sur la home page ou autre route que `/parametres/confidentialite`.** UX spec : la portabilité est dans les "Paramètres → Confidentialité", pas une feature mise en avant.
- ❌ **N'ajoute PAS de logique de notification "in-app"** (badge dans la navbar, etc.). L'AC ne mentionne **plus** la notification in-app (originale écrite avant Story 1.13). Email-only en MVP — la notification in-app est Story 8.x (notifications).

### 3.3 Pièges intermédiaires (À VÉRIFIER)

- ⚠️ **Préfixe `gex_`** — vérifie dans `apps/core/ids.py` qu'il n'est pas déjà réservé. Si conflit, utilise `gdx_` ou `exp_`. **N'INVENTE PAS** sans vérifier.
- ⚠️ **`AUDIT_EXPORTS_BUCKET` vs nouveau `GDPR_EXPORTS_BUCKET`** — cf. §4.5. Décision recommandée : **un seul bucket `exports-gdpr` partagé** mais 2 préfixes distincts (`audit-exports/...` vs `gdpr-exports/...`). Tu déclares `GDPR_EXPORTS_BUCKET = AUDIT_EXPORTS_BUCKET` comme alias en MVP. ADR optionnel si la sépration devient nécessaire en growth.
- ⚠️ **`pyzipper` dépendance** — ajoute à `apps/api/pyproject.toml` dans `[project.dependencies]`. Vérifie la version stable (≥ 0.3.6 ; cf. PyPI). Lance `uv sync` après ajout.
- ⚠️ **MinIO local supporte-t-il `delete_object` ?** — oui, par défaut. Pas de soft-delete bucket configuré (cf. §3.1) → `delete` est immédiat. Tests : utilise `moto` (mock S3) plutôt que MinIO réel pour la suite pytest (déjà pattern Story 1.13).
- ⚠️ **Atomicité de `request_export()`** — la création de `GdprExportRequest` + le `audit_action` + le `.delay()` Celery doivent être dans une `transaction.atomic()` pour éviter qu'un crash après `.delay()` laisse une `pending` en DB qu'aucune tâche ne picke. Utilise `transaction.on_commit(lambda: task.delay(...))` pour différer le dispatch jusqu'au commit (pattern Celery + Django standard).
- ⚠️ **Throttle / rate limit `POST` au-delà du métier** — le rate limit "1/24h" est applicatif (cf. AC2). Ajoute en plus le `django-ratelimit` HTTP IP (50 req/h sur cet endpoint) au cas où l'auth est compromise et qu'un attaquant force des erreurs 429 pour énumérer des userIDs (pas critique mais propre). Pattern déjà utilisé en Story 1.3 sur `/registration/`.

### 3.4 Stratégie de transition `pending` → `ready` 

Tu peux choisir entre 2 patterns (recommandation : **Pattern A** pour MVP) :

**Pattern A — Une tâche Celery par étape**
1. `request_export()` (service Django) → `transaction.on_commit(build_export.delay)`
2. `build_export(export_id)` (Celery) → produit le ZIP, upload S3, transition `in_progress → ready`, `transaction.on_commit(notify_export_ready.delay)`
3. `notify_export_ready(export_id)` (Celery) → envoie email 1, planifie email 2 avec countdown=30s
4. `send_gdpr_export_password_email(export_id, password)` (Celery) → envoie email 2

**Pattern B — Une seule tâche orchestratrice**
- `build_export(export_id)` (Celery) → tout en un, mais hard à tester (pas d'isolation des étapes).

**Pattern A** est plus testable, plus retry-friendly (chaque tâche a son contexte d'échec), et c'est le pattern qu'utilise Story 1.13 (`archive_old_logs`, `export_csv_to_s3` séparés).

**Note :** dans Pattern A, le mot de passe en clair est un argument de `notify_export_ready(export_id, password)` ET de `send_gdpr_export_password_email(export_id, password)`. Évite de le persister entre les deux — passe-le directement de tâche en tâche via `.apply_async(args=[...], countdown=30)`. Celery sérialise via JSON (broker Redis → string en transit, supprimé après ACK).

---

## 4. Architecture Compliance & File Locations

### 4.1 Arborescence à créer/modifier

```
apps/api/
├── apps/
│   └── accounts/
│       ├── models.py                       # MODIFY: ajoute GdprExportRequest + GdprExportStatus TextChoices
│       ├── serializers.py                  # MODIFY: ajoute GdprExportRequestSerializer
│       ├── views.py                        # MODIFY: ajoute GdprExportViewSet (5 actions)
│       ├── urls.py                         # MODIFY: ajoute routes /me/gdpr-exports
│       ├── apps.py                         # MODIFY: ajoute ready() qui charge tous les apps/*/exporters.py
│       ├── tasks.py                        # NEW: build_export, notify_export_ready, send_*_email, expire_old_exports
│       ├── gdpr_exceptions.py              # NEW: GdprExportError + 6 sous-classes
│       ├── services/
│       │   └── gdpr_service.py             # NEW: GdprExportService (request, build, notify, expire)
│       ├── exporters/                      # NEW: package
│       │   ├── __init__.py                 # NEW: register_exporter + ExporterEntry + iter_exporters
│       │   ├── accounts.py                 # NEW: @register_exporter("accounts")
│       │   └── audit.py                    # NEW: @register_exporter("audit")
│       ├── templates/accounts/email/
│       │   ├── gdpr_export_ready.html      # NEW: email 1 lien
│       │   ├── gdpr_export_ready.txt       # NEW: fallback texte
│       │   ├── gdpr_export_password.html   # NEW: email 2 mot de passe
│       │   ├── gdpr_export_password.txt    # NEW
│       │   ├── gdpr_export_failed.html     # NEW
│       │   └── gdpr_export_failed.txt      # NEW
│       ├── migrations/
│       │   └── 0004_gdpr_export_request.py # NEW (numéro selon état actuel — vérifier)
│       └── tests/
│           ├── test_gdpr_models.py         # NEW
│           ├── test_gdpr_exporters.py      # NEW
│           ├── test_gdpr_service.py        # NEW
│           ├── test_gdpr_views.py          # NEW
│           ├── test_gdpr_tasks.py          # NEW
│           ├── test_gdpr_emails.py         # NEW
│           └── test_gdpr_encryption.py     # NEW
├── path_advisor/
│   ├── celery.py                           # MODIFY: ajoute "gdpr-expire-old-exports" beat
│   └── settings/base.py                    # MODIFY: ajoute GDPR_EXPORT_DOWNLOAD_PRESIGNED_TTL_SECONDS, GDPR_EXPORTS_BUCKET alias, GDPR_EXPORT_MAX_DOWNLOADS, GDPR_EXPORT_RATE_LIMIT_HOURS
└── pyproject.toml                          # MODIFY: ajoute pyzipper>=0.3.6

apps/web/
├── src/
│   ├── app/[locale]/(authenticated)/parametres/
│   │   ├── confidentialite/
│   │   │   ├── page.tsx                    # NEW: page principale paramètres confidentialité
│   │   │   └── mes-donnees/
│   │   │       └── page.tsx                # NEW: page liste des exports
│   │   └── layout.tsx                      # MODIFY (si existe) ou NEW: layout authenticated
│   ├── components/features/gdpr/
│   │   ├── gdpr-export-button.tsx          # NEW: bouton "Exporter mes données"
│   │   ├── gdpr-export-card.tsx            # NEW: une ligne dans la liste
│   │   ├── gdpr-export-card.test.tsx       # NEW
│   │   ├── gdpr-export-list.tsx            # NEW
│   │   └── gdpr-export-list.test.tsx       # NEW
│   ├── lib/api/hooks/
│   │   └── use-gdpr-exports.ts             # NEW: hooks TanStack Query (list, get, create)
│   └── lib/api/
│       └── gdpr.ts                         # NEW: wrappers typés sur apiFetch
└── e2e/
    └── gdpr-export.spec.ts                 # NEW: parcours bout-en-bout

apps/web/messages/
└── fr.json                                 # MODIFY: ajoute namespace "gdpr"

docs/runbooks/
└── gdpr-request.md                         # NEW: runbook DPO + lien FAQ utilisateur final
```

### 4.2 Patterns à appliquer

- **Naming DB** (cf. `implementation-patterns-consistency-rules.md`) : `gdpr_export_requests` pluriel snake_case, `idx_<table>_<columns>`, `_at` pour timestamps, `_hash` pour hashs.
- **Naming Python** : classes `PascalCase` (`GdprExportRequest`, `GdprExportService`, `GdprExportInProgress`), fonctions `snake_case`, constantes `SCREAMING_SNAKE_CASE`.
- **Naming API REST** : `/api/v1/me/gdpr-exports` kebab-case pluriel, `{id}` path param, snake_case JSON.
- **Naming TS** : composants `PascalCase`, fichiers `kebab-case` (`gdpr-export-card.tsx`), hooks `useXxx` (`useGdprExports`).
- **Service layer** : `apps/accounts/services/gdpr_service.py` expose `GdprExportService` (classe) avec méthodes `request_export(user) → GdprExportRequest`, `build_export(export_id) → None`, `notify_export_ready(export_id, password) → None`, `expire_old_exports() → int`. La view DRF appelle uniquement `request_export`, jamais les autres (celles-là sont appelées depuis Celery).
- **Erreurs** : héritent de `DomainError` (cf. Story 1.13). Format RFC 7807 auto.
- **Audit** : décorateur `@audit_action` sur `request_export()`, helper `record_audit()` dans les tâches Celery.
- **i18n** : `next-intl` côté front (`useTranslations("gdpr")`), `gettext_lazy` côté Django pour les `detail` des `DomainError` (cf. NFR cross-cutting i18n).

### 4.3 Exemples de code (à respecter scrupuleusement)

**Service Django :**
```python
# apps/accounts/services/gdpr_service.py
from django.db import transaction
from apps.audit.decorators import audit_action

class GdprExportService:
    @staticmethod
    @audit_action(
        "gdpr.export_requested",
        subject_from=lambda kwargs, ret: ret.user_id,
        metadata_from=lambda kwargs, ret: {"export_id": ret.id},
    )
    @transaction.atomic
    def request_export(*, user: User) -> GdprExportRequest:
        # 1. Vérifier rate limit (cf. AC2)
        if _has_recent_active_export(user):
            raise GdprExportInProgress()
        if _has_recent_completed_export_within_24h(user):
            raise GdprExportRateLimited(retry_after_seconds=_compute_retry_after(user))

        # 2. Créer la ligne
        export = GdprExportRequest.objects.create(
            user_id=user.id,
            status=GdprExportStatus.PENDING,
        )

        # 3. Planifier la tâche APRÈS commit
        from apps.accounts.tasks import build_export
        transaction.on_commit(lambda: build_export.delay(export_id=export.id))
        return export
```

**Exporter registry :**
```python
# apps/accounts/exporters/__init__.py
from collections.abc import Callable, Iterable
from dataclasses import dataclass

@dataclass(frozen=True)
class ExporterEntry:
    archive_path: str
    content: bytes
    content_type: str

ExporterFn = Callable[["User"], Iterable[ExporterEntry]]

_REGISTRY: dict[str, ExporterFn] = {}

def register_exporter(domain: str) -> Callable[[ExporterFn], ExporterFn]:
    def decorator(fn: ExporterFn) -> ExporterFn:
        if domain in _REGISTRY:
            raise ValueError(f"Exporter for domain '{domain}' already registered")
        _REGISTRY[domain] = fn
        return fn
    return decorator

def iter_exporters() -> Iterable[tuple[str, ExporterFn]]:
    """Iteration in deterministic order (alphabetical by domain) for reproducible archives."""
    return tuple(sorted(_REGISTRY.items()))
```

**Exporter accounts :**
```python
# apps/accounts/exporters/accounts.py
import json
from collections.abc import Iterable
from apps.accounts.exporters import ExporterEntry, register_exporter
from apps.accounts.models import User

@register_exporter("accounts")
def export_account_profile(user: User) -> Iterable[ExporterEntry]:
    profile = {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "birth_date": user.birth_date.isoformat() if user.birth_date else None,
        "status": user.status,
        "email_verified_at": user.email_verified_at.isoformat() if user.email_verified_at else None,
        "consent_rgpd_at": user.consent_rgpd_at.isoformat() if user.consent_rgpd_at else None,
        "consent_cgu_version": user.consent_cgu_version,
        "tenant_id": str(user.tenant_id) if user.tenant_id else None,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
    }
    yield ExporterEntry(
        archive_path="profile/profile.json",
        content=json.dumps(profile, indent=2, ensure_ascii=False).encode("utf-8"),
        content_type="application/json",
    )
```

**Chargement automatique des exporters via AppConfig :**
```python
# apps/accounts/apps.py
from django.apps import AppConfig
from importlib import import_module

class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"

    def ready(self) -> None:
        super().ready()
        # Auto-load all apps/*/exporters.py modules so their @register_exporter
        # decorators run at Django startup. New domains drop a single file —
        # no central registration needed.
        from django.apps import apps
        for app_config in apps.get_app_configs():
            try:
                import_module(f"{app_config.name}.exporters")
            except ImportError:
                pass  # Apps without an exporters module are skipped silently.
```

⚠️ **Note** : ce mécanisme charge `apps/accounts/exporters.py` mais NOTRE structure est `apps/accounts/exporters/` (package). Django gère bien les packages — `import_module("apps.accounts.exporters")` chargera `apps/accounts/exporters/__init__.py`, qui doit importer ses sous-modules (`from . import accounts, audit`) pour déclencher les décorateurs `@register_exporter`. Crée donc `apps/accounts/exporters/__init__.py` qui termine par :
```python
from . import accounts as _accounts  # noqa: F401 — triggers @register_exporter
from . import audit as _audit  # noqa: F401
```

**ViewSet DRF :**
```python
# apps/accounts/views.py (extrait)
from rest_framework import status as drf_status
from rest_framework.decorators import action
from rest_framework.response import Response

class GdprExportViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    serializer_class = GdprExportRequestSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CursorPagination
    lookup_field = "id"

    def get_queryset(self):
        return GdprExportRequest.objects.filter(user_id=self.request.user.id)

    def create(self, request, *args, **kwargs):
        export = GdprExportService.request_export(user=request.user)
        serializer = self.get_serializer(export)
        return Response(serializer.data, status=drf_status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, id=None):
        export = self.get_object()
        if export.status == GdprExportStatus.EXPIRED:
            raise GdprExportExpired()
        if export.status != GdprExportStatus.READY:
            raise GdprExportNotReady()
        if export.download_count >= settings.GDPR_EXPORT_MAX_DOWNLOADS:
            raise GdprExportDownloadCap()

        presigned = _generate_presigned_url(
            key=export.archive_s3_key,
            ttl=settings.GDPR_EXPORT_DOWNLOAD_PRESIGNED_TTL_SECONDS,
        )
        # Incrémenter le compteur ET tracer l'audit AVANT la redirection (rien ne dit que l'utilisateur va vraiment suivre)
        GdprExportRequest.objects.filter(id=export.id).update(
            download_count=F("download_count") + 1,
            last_downloaded_at=timezone.now(),
        )
        record_audit(
            action="gdpr.export_downloaded",
            result=AuditResult.SUCCESS,
            actor=request.user,
            subject_id=request.user.id,
            metadata={"export_id": export.id, "download_count": export.download_count + 1},
        )
        return HttpResponseRedirect(presigned)
```

### 4.4 Migrations Django

Numéro de migration : vérifie l'état actuel avec `ls apps/api/apps/accounts/migrations/`. Probablement `0004_gdpr_export_request.py` (après `0001_initial`, `0002_*`, `0003_*`).

La migration crée :
- Table `gdpr_export_requests` avec tous les champs §AC1
- Index `idx_gdpr_exports_user_id_requested_at`, `idx_gdpr_exports_status_expires_at`
- **PAS de FK** vers `users` (FK logique uniquement — cf. §3.2)

Pas de RunPython data migration (table vierge).

### 4.5 Décision : bucket S3 partagé vs séparé

**Recommandation : bucket unique `exports-gdpr` avec préfixes distincts.**

| Aspect | Bucket partagé | Bucket séparé |
|---|---|---|
| **Coût opérationnel** | 1 bucket à provisioner, 1 policy | 2 buckets, 2 policies |
| **Isolation** | Préfixes `audit-exports/` vs `gdpr-exports/` lisibles | Stricte au niveau bucket |
| **Backup / lifecycle** | Une seule règle | Deux règles |
| **Risque** | Confusion potentielle si même clé | Aucun |
| **Growth migration** | Facile (renommer préfixes ou splitter) | N/A |

→ MVP : partage. Story 1.11 ajoute `GDPR_EXPORTS_BUCKET = os.environ.get("GDPR_EXPORTS_BUCKET", AUDIT_EXPORTS_BUCKET)` dans `settings/base.py` (alias mutualisé). En growth, on peut séparer via une simple variable env sans rien casser.

Clé S3 :
- Audit (Story 1.13) : `exports/{requested_by}/...csv` et `archive/{YYYY}/{MM}/...`
- GDPR (Story 1.11) : `gdpr-exports/{user_id}/{export_id}.zip`

Aucun chevauchement sur le préfixe.

### 4.6 Settings à ajouter (`apps/api/path_advisor/settings/base.py`)

```python
# --- GDPR portability (Story 1.11) ---
# Bucket S3 pour les archives. Partage avec AUDIT_EXPORTS_BUCKET en MVP (cf. Story 1.11 §4.5).
GDPR_EXPORTS_BUCKET = os.environ.get("GDPR_EXPORTS_BUCKET", AUDIT_EXPORTS_BUCKET)
# TTL du presigned URL généré au moment du clic "Télécharger". Court (5 min) car
# le frontend est authentifié — pas besoin d'un lien réutilisable.
GDPR_EXPORT_DOWNLOAD_PRESIGNED_TTL_SECONDS = int(
    os.environ.get("GDPR_EXPORT_DOWNLOAD_PRESIGNED_TTL_SECONDS", 300)
)
# Cap anti-abus : nombre de downloads autorisés par export ready.
GDPR_EXPORT_MAX_DOWNLOADS = int(os.environ.get("GDPR_EXPORT_MAX_DOWNLOADS", 10))
# Fenêtre rate limit applicatif (heures entre 2 exports `ready` pour un même user).
GDPR_EXPORT_RATE_LIMIT_HOURS = int(os.environ.get("GDPR_EXPORT_RATE_LIMIT_HOURS", 24))
# Durée de validité d'un export avant expiration et purge S3.
GDPR_EXPORT_VALIDITY_DAYS = int(os.environ.get("GDPR_EXPORT_VALIDITY_DAYS", 7))
# Bound sur le worker time max — un export coûteux > 25 min indique un bug.
GDPR_EXPORT_TASK_HARD_TIMEOUT_SECONDS = int(
    os.environ.get("GDPR_EXPORT_TASK_HARD_TIMEOUT_SECONDS", 25 * 60)
)
```

---

## 5. Libraries & Framework Requirements

### 5.1 Nouvelles dépendances Python

Ajoute dans `apps/api/pyproject.toml` section `[project.dependencies]` :

```toml
"pyzipper>=0.3.6,<0.4",   # AES-256 ZIP encryption (zipfile natif Python ne supporte que ZipCrypto vulnérable)
```

**Pourquoi pyzipper et pas alternative :**
- `zipfile` stdlib : pas d'AES, ZipCrypto cassé depuis 2003.
- `pycryptodome` + custom ZIP : trop bas-niveau, plus de surface bug.
- `python-zipfile` (alias) : n'existe pas comme distrib séparée.
- `pyzipper` : drop-in replacement, maintenu (dernière release récente), API identique `zipfile`, support AES-128/192/256. **Choix MVP.**

Pas d'autres nouvelles deps. `boto3` déjà présent, `celery` déjà présent, `django` 5.x déjà présent.

### 5.2 Pas de nouvelles dépendances front

shadcn/ui composants déjà installés (Button, Card, Badge, Skeleton, Tooltip). TanStack Query, React Hook Form, Zod, next-intl déjà en place. Pas d'ajout dans `apps/web/package.json`.

### 5.3 Versions à respecter

- Python : 3.12 (cf. ADR-0002)
- Django : ≥ 5.0 (déjà en place)
- DRF : standard
- Celery : 5.x
- boto3 : déjà pinned via existing config
- pyzipper : ≥ 0.3.6

---

## 6. Testing Requirements

### 6.1 Stratégie de test

**Backend (pytest + factory_boy + moto pour S3 mock) :**

| Fichier | Coverage |
|---|---|
| `test_gdpr_models.py` | Schéma table, ULID `gex_`, transitions valides, contraintes Django |
| `test_gdpr_exporters.py` | Registry register/duplicate-error, `iter_exporters` ordre déterministe, exporter `accounts` snapshot, exporter `audit` filtre subject+actor, empty user (no audit) |
| `test_gdpr_service.py` | `request_export` happy / rate-limited / in-progress, transactional dispatch (`on_commit` est appelé après commit), idempotence |
| `test_gdpr_views.py` | 4 endpoints REST : auth required (401), permissions (404 cross-user), 409, 429, 410, 302, audit emis, pagination |
| `test_gdpr_tasks.py` | `build_export` happy path (mock S3 via moto), `build_export` exporter individuel raise → continue + erreur dans ZIP, ZIP est bien chiffré, idempotence sur double-fire, `expire_old_exports` supprime S3 + transition status |
| `test_gdpr_emails.py` | 2 emails distincts, sujet/body, password présent uniquement dans email 2, failed → seul gdpr_export_failed envoyé |
| `test_gdpr_encryption.py` | Le ZIP généré est ouvrable avec le password généré ; refuse password vide / wrong password |

**Coverage cible :** ≥ 90 % sur les fichiers `services/gdpr_service.py`, `exporters/*.py`, `tasks.py` (sections gdpr), `views.py` (additions gdpr). Strict pour zone RGPD critique.

**Front (Vitest + Testing Library + Playwright) :**

| Fichier | Coverage |
|---|---|
| `gdpr-export-card.test.tsx` | Rendu des 5 statuts, accessibilité (badge text-not-color-only), boutons disabled selon status |
| `gdpr-export-list.test.tsx` | Empty state, list with mixed statuses, polling actif uniquement si pending |
| `e2e/gdpr-export.spec.ts` | Login → navigate → clic → polling jusqu'à ready (CELERY_TASK_ALWAYS_EAGER=True en test) → clic télécharger → vérif download |

### 6.2 Mocks et fixtures

- **S3 mock :** `moto` (déjà utilisé par Story 1.13 tests). Patch dans `conftest.py` ou fixture par test.
- **Celery synchrone :** `pytest.fixture(autouse=True, scope="session")` qui force `CELERY_TASK_ALWAYS_EAGER = True` + `CELERY_TASK_EAGER_PROPAGATES = True` en test settings (`apps/api/path_advisor/settings/test.py`).
- **Email backend :** `django.core.mail.backends.locmem.EmailBackend` en test → assertions sur `mail.outbox`.
- **Factory :** `GdprExportRequestFactory` dans `apps/accounts/tests/factories.py` ; user factory déjà présente.
- **`time-machine` ou `freezegun`** pour tester l'expiration sans attendre 7 jours réels.

### 6.3 Tests cross-story à NE PAS écrire

- ❌ Ne teste pas que l'audit log est immuable (déjà couvert Story 1.13).
- ❌ Ne teste pas que User signup marche (Story 1.3).
- ❌ Ne teste pas que `apiFetch` parse les RFC 7807 (Story 1.3).
- ❌ Ne teste pas les permissions DRF natives (Django).

### 6.4 Validation manuelle

Avant le merge :
1. `docker-compose up` local — créer un user via signup (Story 1.3 flow), naviguer `/parametres/confidentialite/mes-donnees`, déclencher un export, observer l'email dans Mailpit (port 8025), copier le mot de passe, télécharger le ZIP, l'ouvrir avec 7-Zip / Keka, vérifier que `profile/profile.json` et `audit/audit-log.jsonl` sont conformes.
2. Tester un 2e export immédiat → doit retourner 429.
3. Attendre 24h (ou tweaker `GDPR_EXPORT_RATE_LIMIT_HOURS=0`) et retenter → doit marcher.
4. Forcer `expires_at` à il y a 1 minute et lancer `python manage.py shell` → `from apps.accounts.tasks import expire_old_exports; expire_old_exports()` → vérifier que le statut passe à `expired` et que le fichier S3 (MinIO console http://localhost:9001) a disparu.

---

## 7. Tasks Décomposition

### T1. Setup dépendances & settings (S — 15 min)
- T1.1 Ajouter `pyzipper>=0.3.6` à `apps/api/pyproject.toml`, lancer `uv sync`
- T1.2 Ajouter les 6 settings de §4.6 dans `path_advisor/settings/base.py`
- T1.3 Ajouter `"gdpr-expire-old-exports"` au `beat_schedule` dans `path_advisor/celery.py`
- T1.4 Vérifier que `gex_` n'est pas déjà réservé dans `apps/core/ids.py` ; choisir un préfixe libre

### T2. Modèle + migration (S — 30 min)
- T2.1 Définir `GdprExportStatus(models.TextChoices)` dans `apps/accounts/models.py`
- T2.2 Définir `GdprExportRequest` (Meta : `db_table="gdpr_export_requests"`, indexes, `ordering=["-requested_at"]`)
- T2.3 Générer migration : `python manage.py makemigrations accounts --name gdpr_export_request`
- T2.4 Vérifier la migration : pas de FK contrainte, indexes nommés correctement, snake_case
- T2.5 Test `test_gdpr_models.py` : création, ULID `gex_`, transitions

### T3. Exporter registry + 2 exporters initiaux (M — 1 h)
- T3.1 Créer le package `apps/accounts/exporters/`
- T3.2 `__init__.py` : `ExporterEntry` dataclass, `register_exporter` decorator, `iter_exporters` (ordre alpha déterministe)
- T3.3 `__init__.py` (fin) : `from . import accounts as _accounts, audit as _audit` pour trigger les décorateurs
- T3.4 `accounts.py` : `@register_exporter("accounts")` → `profile/profile.json`
- T3.5 `audit.py` : `@register_exporter("audit")` → `audit/audit-log.jsonl`, requête `Q(subject_id=user.id) | Q(actor_id=user.id)`
- T3.6 Modifier `apps/accounts/apps.py` : `ready()` qui charge `apps/*/exporters` dynamiquement (cf. §4.3)
- T3.7 Test `test_gdpr_exporters.py` : registry tests, snapshot JSON exporter accounts, audit exporter filtre + ordre chronologique

### T4. Service + exceptions (M — 1 h)
- T4.1 Créer `apps/accounts/gdpr_exceptions.py` : 6 classes (`GdprExportError` base, 5 sous-classes) avec `default_type` URL et `default_detail` gettext_lazy
- T4.2 Créer `apps/accounts/services/gdpr_service.py` : `GdprExportService` avec `request_export`, helpers `_has_recent_active_export`, `_has_recent_completed_export_within_24h`, `_compute_retry_after`
- T4.3 Décorer `request_export` avec `@audit_action("gdpr.export_requested", ...)`
- T4.4 Utiliser `transaction.on_commit(lambda: build_export.delay(...))` pour le dispatch
- T4.5 Test `test_gdpr_service.py` : happy, in_progress, rate_limited, on_commit pattern

### T5. Tâches Celery (L — 2 h)
- T5.1 `apps/accounts/tasks.py` : `build_export(export_id)` — orchestrateur ZIP + S3 + transition (cf. AC5 §1-8)
- T5.2 Génération password : `secrets.token_urlsafe(24)`, hash via `make_password`
- T5.3 ZIP via `pyzipper.AESZipFile` (WZ_AES, ZIP_DEFLATED), streaming write par entry, fichier `manifest.json` + `README.txt` à la racine
- T5.4 Upload S3 via `boto3` (ServerSideEncryption=AES256, ContentType=application/zip, Metadata user_id+export_id)
- T5.5 `notify_export_ready(export_id, password)` : envoie email 1, planifie email 2 avec `countdown=30`
- T5.6 `send_gdpr_export_link_email(export_id)` : template `gdpr_export_ready.html`
- T5.7 `send_gdpr_export_password_email(export_id, password)` : template `gdpr_export_password.html`
- T5.8 `send_gdpr_export_failed_email(export_id)` : template `gdpr_export_failed.html`
- T5.9 `expire_old_exports()` : balayage `status=ready AND expires_at < now()`, suppression S3, transition
- T5.10 Retry config Celery : `autoretry_for=(boto3.exceptions.Boto3Error,)` sur les 3 send_*_email, `max_retries=3`, `default_retry_delay=60`
- T5.11 Test `test_gdpr_tasks.py` : moto S3, happy + each failure mode, idempotence, expire

### T6. Templates email (S — 30 min)
- T6.1 6 fichiers `.html` + `.txt` dans `apps/accounts/templates/accounts/email/` (cf. §4.1 arbo)
- T6.2 Tous les templates en français (langue MVP), conformes pattern Story 1.3 (`email_confirmation.html`)
- T6.3 Test `test_gdpr_emails.py` : `mail.outbox` assertions, contenus, séparation password

### T7. Views + serializers + URLs (M — 1 h)
- T7.1 `apps/accounts/serializers.py` : `GdprExportRequestSerializer` avec champs read-only (status, dates, error_*, download_count, expires_at)
- T7.2 `apps/accounts/views.py` : `GdprExportViewSet` avec `create`, `list`, `retrieve`, `download` (cf. §4.3)
- T7.3 `apps/accounts/urls.py` : router DRF, préfixe `me/gdpr-exports` sous le path déjà existant `api/v1/auth/` → préférer ajouter directement dans `path_advisor/urls.py` un mount séparé `path("api/v1/me/", include("apps.accounts.gdpr_urls"))` pour ne pas mélanger `auth/` (dj-rest-auth) et `me/` (custom)
- T7.4 Throttle DRF `UserRateThrottle` à 50/h sur l'endpoint POST (cf. §3.3)
- T7.5 Test `test_gdpr_views.py` : auth, 4 endpoints, codes erreur, audit emis

### T8. Frontend (M — 1 h 30)
- T8.1 `apps/web/messages/fr.json` : ajouter namespace `gdpr` (titres, textes, boutons, statuts)
- T8.2 `apps/web/src/lib/api/gdpr.ts` : types TS depuis OpenAPI, wrappers `listGdprExports`, `createGdprExport`, `getGdprExport`
- T8.3 `apps/web/src/lib/api/hooks/use-gdpr-exports.ts` : hooks TanStack Query `useGdprExportsList`, `useCreateGdprExport`, `useGdprExport(id)` avec `refetchInterval` conditionnel
- T8.4 `components/features/gdpr/gdpr-export-button.tsx` : bouton avec disabled si pending/in_progress en cours
- T8.5 `components/features/gdpr/gdpr-export-card.tsx` : carte par export avec badge statut + download button
- T8.6 `components/features/gdpr/gdpr-export-list.tsx` : liste
- T8.7 `app/[locale]/(authenticated)/parametres/confidentialite/page.tsx` : page paramètres avec bouton
- T8.8 `app/[locale]/(authenticated)/parametres/confidentialite/mes-donnees/page.tsx` : liste
- T8.9 Tests Vitest co-located sur composants
- T8.10 Playwright `e2e/gdpr-export.spec.ts`

### T9. Documentation runbook (S — 15 min)
- T9.1 `docs/runbooks/gdpr-request.md` : runbook DPO (comment répondre à une demande Art. 20 manuelle si l'utilisateur n'a plus accès à son compte, comment auditer un export, comment forcer une expiration)
- T9.2 FAQ section pour les utilisateurs finaux (comment ouvrir un ZIP AES-256, que faire si mot de passe perdu, etc.)

### T10. CI / lint / type-check (S — 15 min)
- T10.1 `ruff check apps/accounts/` doit passer
- T10.2 `mypy apps/accounts/` doit passer (strict si déjà configuré)
- T10.3 `npm run lint` côté `apps/web` doit passer
- T10.4 `npm run typecheck` doit passer
- T10.5 Lancer `make openapi` pour régénérer les types TS générés depuis OpenAPI
- T10.6 Vérifier la couverture pytest ≥ 90 % sur les fichiers gdpr*

**Estimation totale : ~ 9 h** (M+).

---

## 8. Previous Story Intelligence (Story 1.13)

**Patterns posés par 1.13 à réutiliser directement :**

1. **Boto3 client helper** ([apps/audit/services/archive_service.py:42-49](apps/api/apps/audit/services/archive_service.py#L42-L49)) — `_s3_client()` factory. **Duplique-le** dans `gdpr_service.py` (pas de refactor cross-app prématuré).
2. **Pattern S3 streaming put_object** ([apps/audit/services/archive_service.py:86-99](apps/api/apps/audit/services/archive_service.py#L86-L99)) — `ServerSideEncryption="AES256"`, `ContentType=...`. Adapte pour `application/zip`.
3. **Presigned URL generation** ([apps/audit/tasks.py:144-149](apps/api/apps/audit/tasks.py#L144-L149)) — `s3.generate_presigned_url("get_object", Params={...}, ExpiresIn=ttl)`.
4. **CSV/JSONL streaming via `qs.iterator(chunk_size=500)`** ([apps/audit/services/archive_service.py:73-82](apps/api/apps/audit/services/archive_service.py#L73-L82)) — réplique pour l'exporter `audit`.
5. **`record_audit` ad-hoc** ([apps/audit/decorators.py:94-156](apps/api/apps/audit/decorators.py#L94-L156)) — utilise pour les transitions Celery (pas `@audit_action`).
6. **`@audit_action` décorateur** — utilise sur `request_export` du service.
7. **Beat schedule pattern** ([path_advisor/celery.py:16-25](apps/api/path_advisor/celery.py#L16-L25)) — copie le pattern crontab.
8. **Pre/postrun signals** pour `request_context.clear()` — déjà en place, ne re-définis pas.

**Bugs résolus par la review 1.13 à éviter :**
- `record_audit` ne doit pas lever d'exception (swallow + Sentry).
- Sentry capture via `try: import sentry_sdk; except Exception: pass` (cf. deferred work : à refactor plus tard).
- Hash chain `prev_hash`/`row_hash` est interne audit → **ne réexpose pas** dans l'exporter `audit`.
- Boto3 client a `connect_timeout=5, read_timeout=30, retries={"max_attempts": 3}` ([tasks.py:130-131](apps/api/apps/audit/tasks.py#L130-L131)) — réutilise cette config.

**Files modifiés par 1.13 pertinents :**
- [apps/api/apps/audit/decorators.py](apps/api/apps/audit/decorators.py) — décorateur + helper
- [apps/api/apps/audit/models.py](apps/api/apps/audit/models.py) — `AuditLog`, `AuditResult`
- [apps/api/path_advisor/settings/base.py](apps/api/path_advisor/settings/base.py) — settings audit (modèle pour les settings GDPR)
- [apps/api/path_advisor/celery.py](apps/api/path_advisor/celery.py) — beat + signals

**Deferred work 1.13 pertinent pour 1.11 :**
- "Email DPO on chain-break detection" — pas concerné par 1.11.
- "AuditLogImmutable HTTP status 409" — l'export ne mute pas l'audit, donc N/A.

---

## 9. Git Intelligence

**Branche actuelle worktree :** `worktree-story-1-11-export-rgpd` (depuis `main`).

**Commits récents pertinents (`git log -10 --oneline`) :**
```
3195246 chore(sprint-status): mark 1.13 done after PR #1 merge
dc1eccd story 1.14: ConsentDialog + design-system showcase + logo (#2)
7470979 Story 1.3 — Inscription élève ≥ 15 ans avec consentement RGPD (#4)
d207a4c story 1.13: immutable audit log + REST endpoints + Celery beat
8d4a5c8 Story 1.2 done front and design init
```

**Patterns observés :**
- Format de message : `story X.Y: <résumé court>` ou `Story X.Y — <résumé long>` (ces deux variantes coexistent, peu importe — reste cohérent dans la PR).
- Une PR ⇔ une story, mergée via squash (cf. PR #4, #2, #1).
- Co-author tag `Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>` sur les commits Claude.
- Branche : tu es déjà dans un git worktree (`worktree-story-1-11-export-rgpd`) → tu peux commiter directement et pousser ; ouvre la PR depuis cette branche.

---

## 10. Open Questions

À résoudre AVANT de commencer l'implémentation (poser à l'utilisateur si bloquant, sinon documenter la décision dans le PR description) :

1. **Adresse email DPO ?** L'AC6 mentionne `dpo@path-advisor.fr` dans les templates email. Si cette adresse n'est pas réservée, utiliser `support@path-advisor.fr` ou laisser un placeholder configurable via env `DPO_EMAIL`.
2. **Format de manifest : JSON ou XML ?** L'Art. 20 RGPD demande "structuré, communément utilisé, machine-readable" — JSON est largement accepté en pratique. Décision : JSON. Justifier dans le PR description.
3. **Permissions cross-role : un parent peut-il exporter les données de son enfant ?** Réponse : non en MVP. La portabilité est un droit personnel. Le parent peut demander un export de SON propre compte parent (qui contient les liens, motivations, etc. de son point de vue), mais pas celui de l'enfant. L'enfant exporte lui-même. Ce comportement découle naturellement du `permission_classes = [IsAuthenticated]` + `filter(user_id=request.user.id)` — pas besoin de gestion spéciale.
4. **L'export inclut-il les données pseudonymisées d'audit après hard-delete du compte (Story 1.12) ?** Décision : non. Une fois le compte hard-deleted, les audit entries persistent 3 ans (NFR-S4) mais ne sont plus rattachables à l'utilisateur. Les exports existants déjà générés restent téléchargeables 7 jours (cf. §3.2). Pas de nouvel export possible après hard-delete (l'utilisateur n'a plus de session).

---

## 11. Project Context Reference

- **Architecture :** [_bmad-output/planning-artifacts/architecture/core-architectural-decisions.md](_bmad-output/planning-artifacts/architecture/core-architectural-decisions.md)
- **Project structure :** [_bmad-output/planning-artifacts/architecture/project-structure-boundaries.md](_bmad-output/planning-artifacts/architecture/project-structure-boundaries.md)
- **Patterns :** [_bmad-output/planning-artifacts/architecture/implementation-patterns-consistency-rules.md](_bmad-output/planning-artifacts/architecture/implementation-patterns-consistency-rules.md)
- **PRD FRs :** [_bmad-output/planning-artifacts/prd/functional-requirements.md](_bmad-output/planning-artifacts/prd/functional-requirements.md) (FR10)
- **PRD NFRs :** [_bmad-output/planning-artifacts/prd/non-functional-requirements.md](_bmad-output/planning-artifacts/prd/non-functional-requirements.md) (NFR-S6, NFR-S1, NFR-S4, NFR-R4, NFR-M2)
- **Epic 1 :** [_bmad-output/planning-artifacts/epics/epic-1-foundation-auth-multi-role-rbac-conformite-rgpd-infra-technique.md](_bmad-output/planning-artifacts/epics/epic-1-foundation-auth-multi-role-rbac-conformite-rgpd-infra-technique.md) (§Story 1.11)
- **Story 1.13 (audit) :** [_bmad-output/implementation-artifacts/1-13-journal-audit-acces.md](_bmad-output/implementation-artifacts/1-13-journal-audit-acces.md)
- **Story 1.3 (signup) :** [_bmad-output/implementation-artifacts/1-3-inscription-eleve-15-ans-rgpd.md](_bmad-output/implementation-artifacts/1-3-inscription-eleve-15-ans-rgpd.md)
- **Deferred work :** [_bmad-output/implementation-artifacts/deferred-work.md](_bmad-output/implementation-artifacts/deferred-work.md)

---

## 12. Dev Agent Record

### Agent Model Used

claude-opus-4-7 (1M context)

### Debug Log References

- `transaction.on_commit` ne se déclenche pas dans une transaction pytest-django ; le test `test_request_export_creates_pending_row_and_dispatches_task` utilise `TestCase().captureOnCommitCallbacks(execute=True)` pour forcer le flush.
- L'audit decorator passe `ret=None` sur le chemin failure ; les lambdas `subject_from`/`metadata_from` ont été rendues `None`-safe (`getattr(kwargs.get("user"), "id", None)`).
- DRF `CursorPagination` par défaut trie sur `created` qui n'existe pas sur `GdprExportRequest` → sous-classe `_GdprExportCursorPagination` qui ordonne par `-requested_at`.
- Next.js `<Link>` retire le trailing slash lors du rendu en `<a>` ; DRF redirige `/download` → `/download/` donc le clic reste fonctionnel. Le test asserte les deux variantes via regex.
- ESLint rule `react-hooks/set-state-in-effect` est sur-stricte avec `void refresh()` (refresh résout en microtask) ; suppression locale documentée sur le initial-fetch effect.
- `pyzipper` (et non `zipfile` stdlib) est obligatoire pour AES-256 — `zipfile` ne supporte que ZipCrypto cassé depuis 2003.
- `timezone.timedelta` n'est pas exporté par django.utils.timezone (mypy strict catch) → utilisation de `datetime.timedelta`.

### Completion Notes List

**Backend (apps/api) — 39 tests passent + lint clean :**
- Modèle `GdprExportRequest` + migration 0003, ULID préfixe `gex_`, FK logique (pas de contrainte DB pour survivre au hard-delete 1.12).
- Service `GdprExportService.request_export()` décoré `@audit_action("gdpr.export_requested")`, dispatch Celery via `transaction.on_commit`.
- 6 exceptions `Gdpr*Error` héritant de `DomainError` (RFC 7807 auto via handler 1.13).
- Exporter registry extensible : `register_exporter("<domain>")` + autoload via `AccountsConfig.ready()`. Initial : `accounts` (profile.json) + `audit` (audit-log.jsonl filtré subject OU actor, sans hash chain).
- Pipeline Celery 4 tâches : `build_export` (ZIP AES-256 pyzipper + upload S3 SSE-AES256), `notify_export_ready` (idempotent via `emails_sent_at` guard), `send_gdpr_export_password_email` (countdown=30s), `send_gdpr_export_failed_email`, `expire_old_exports` (beat quotidien 04:00 UTC).
- 4 endpoints REST : POST 202 (rate-limit 24h applicatif + UserRateThrottle 50/h défense en profondeur), GET liste paginée, GET détail (404 cross-user), GET download (302 vers presigned URL S3 5 min + audit + counter F-expression).
- 6 templates email FR (3 paires .html/.txt) ; password jamais en clair dans email 1 ni dans email failed.
- 6 settings configurables (`GDPR_EXPORTS_BUCKET` aliasé sur `AUDIT_EXPORTS_BUCKET` MVP, `GDPR_EXPORT_DOWNLOAD_PRESIGNED_TTL_SECONDS=300`, `GDPR_EXPORT_MAX_DOWNLOADS=10`, `GDPR_EXPORT_RATE_LIMIT_HOURS=24`, `GDPR_EXPORT_VALIDITY_DAYS=7`, `GDPR_EXPORT_TASK_HARD_TIMEOUT_SECONDS=1500`).

**Frontend (apps/web) — 5 nouveaux tests + 34 total passent, lint + typecheck clean :**
- `lib/api/gdpr.ts` : types + wrappers `apiFetch` + `buildGdprDownloadUrl`.
- `components/features/gdpr/` : badge statut (text + couleur, conforme RGAA NFR-A1), card par export (5 statuts), list avec polling 5s conditionnel.
- Pages : `/parametres/confidentialite` (settings) + `/parametres/confidentialite/mes-donnees` (liste).

**Audit (Story 1.13) :** 5 événements émis (`gdpr.export_requested`, `_ready`, `_downloaded`, `_expired`, `_failed`).

**Décisions documentées dans la story :**
- Bucket S3 mutualisé `exports-gdpr` avec préfixes distincts (`audit-exports/` vs `gdpr-exports/`) — séparable en growth via env var sans casser le code (§4.5).
- Mot de passe en clair transite par les kwargs Celery (broker Redis local-only en MVP) ; jamais persisté ; hash Argon2 conservé pour traçabilité support (§3.4).
- Logique d'export dans `apps/accounts/` (cluster FR1-FR12) — pas d'app `apps/gdpr/` séparée. Exporters cross-app vivent dans `apps/<their_app>/exporters.py` (§3.2).

**Runbook DPO :** `docs/runbooks/gdpr-request.md` — workflow user, troubleshooting, manual export, force-expiration, inspection ZIP locale, audit trail.

**Open items (laissés en deferred-work pour code-review) :**
- Pas de notification in-app — Story 8.x notifications.
- Manifest/README FR-only — i18n Epic 7+.
- Pas de retry idempotent sur `build_export` (un échec = `failed`, l'user retente) — décision MVP §AC5.
- 2 mypy errors pré-existants dans `apps/accounts/managers.py` (Story 1.3), pas régressés par 1.11.

### Review Findings

**Decision-needed (4) — résolues + appliquées en patch :**

- [x] [Review][Decision] D1 password broker — **résolue : pipeline single-task**. `notify_export_ready` envoie maintenant les 2 emails dans le même worker (`time.sleep(30)` in-process), le password ne quitte jamais une seule task. Élimine la fenêtre d'exposition broker.
- [x] [Review][Decision] D2 audit exporter actor leakage — **résolue : filter `subject_id=user.id` uniquement**. Les rows où user = actor sur tiers sont exclues (élimine fuite cross-tenant + tiers PII).
- [x] [Review][Decision] D3 system actor — **résolue : `actor_role="system"` explicite**. Helper `_SYSTEM_ACTOR = SimpleNamespace(id=None, role="system")` passé à tous les `record_audit` Celery-side.
- [x] [Review][Decision] D4 double-POST race — **résolue : partial unique index migration 0004**. `IntegrityError` translaté en `GdprExportInProgress` (409) côté service.

**Patch (14) — appliqués :**

- [x] [Review][Patch] TOCTOU `download_count` cap → `.update(filter=download_count__lt=MAX, F+1)` atomic guard [apps/api/apps/accounts/views.py:download]
- [x] [Review][Patch] `download_count` incrémenté avant presign → presign d'abord + counter rollback sur échec [apps/api/apps/accounts/views.py:download]
- [x] [Review][Patch] Lazy-expiry bypass → check `expires_at < now()` ajouté avant download [apps/api/apps/accounts/views.py:download]
- [x] [Review][Patch] `_mark_failed` orphan S3 → cleanup `archive_s3_key_to_purge` ajouté à la signature, best-effort delete avant flip status [apps/api/apps/accounts/tasks.py:_mark_failed]
- [x] [Review][Patch] `error_message` sanitize → ne contient plus que `<ExcClass>: see Sentry for details.` (raw `str(exc)` log Sentry uniquement) [apps/api/apps/accounts/tasks.py:_mark_failed + serializers.py]
- [x] [Review][Patch] `notify_export_ready` autoretry `_EMAIL_RETRY_EXC` (SMTP/Connection/Timeout/OSError) + single-task pipeline [apps/api/apps/accounts/tasks.py:notify_export_ready]
- [x] [Review][Patch] `emails_sent_at` set AVANT le 1er email (idempotence stricte) [apps/api/apps/accounts/tasks.py:notify_export_ready]
- [x] [Review][Patch] `send_gdpr_export_password_email` retry narrow → `_EMAIL_RETRY_EXC` au lieu de `Exception` [apps/api/apps/accounts/tasks.py]
- [x] [Review][Patch] `soft_time_limit` au décoration time (`@shared_task(soft_time_limit=..., time_limit=...)`) [apps/api/apps/accounts/tasks.py:build_export]
- [x] [Review][Patch] Lien email deep-link `#{export.id}` + `scroll-mt-24 target:ring-2 target:ring-brand` sur la card [templates + gdpr-export-card.tsx]
- [x] [Review][Patch] `rel="noopener noreferrer"` [apps/web/src/components/features/gdpr/gdpr-export-card.tsx]
- [x] [Review][Patch] Polling stop sur ApiError 401 via `state.authLost` flag [apps/web/src/components/features/gdpr/gdpr-export-list.tsx]
- [x] [Review][Patch] `no_email` → `record_audit("gdpr.notify_skipped")` + `sentry_sdk.capture_message` [apps/api/apps/accounts/tasks.py:notify_export_ready]
- [x] [Review][Patch] `apps.py` autoloader narrow → catch `ModuleNotFoundError` uniquement si `exc.name == "<app>.exporters"`, propagate transitive failures [apps/api/apps/accounts/apps.py]

**Defer (6) — pré-existants ou hors scope :**

- [x] [Review][Defer] `_build_zip` charge l'archive entière en BytesIO (viole anti-pattern §3.2 streaming) — non bloquant tant qu'aucun exporter n'envoie 100+ MB ; tracking pour Story 2.3 (bulletins) qui ajoutera l'exporter volumineux [apps/api/apps/accounts/tasks.py:_build_zip]
- [x] [Review][Defer] `[locale]` routing + next-intl namespace `gdpr` non câblés — cohérent avec l'état actuel (Story 1.3/1.14 n'utilisent pas non plus). Cross-cutting i18n en Epic 7 [apps/web/src/app/(authenticated)/]
- [x] [Review][Defer] Relative timestamps + tooltip absolu manquants (UX polish AC8) — non bloquant, à reprendre quand le design-system livre un `<RelativeTime>` component [apps/web/src/components/features/gdpr/gdpr-export-card.tsx]
- [x] [Review][Defer] Playwright `e2e/gdpr-export.spec.ts` manquant — infra Playwright non bootstrapée pour 1.x ; cross-cutting story dédiée [apps/web/e2e/]
- [x] [Review][Defer] `build_export` sans `transaction.atomic` global + pas de reaper task pour `in_progress` stuck (DB connection drop scenario) — risque faible MVP, ajouter un reaper Celery beat en growth [apps/api/apps/accounts/tasks.py:build_export]
- [x] [Review][Defer] CSRF token silently optional sur POST (`readCsrfCookie() ?? undefined`) — pattern à harmoniser avec Story 1.5 login flow [apps/web/src/lib/api/gdpr.ts]

### File List

**Backend (apps/api) — créés :**
- `apps/accounts/exporters/__init__.py`
- `apps/accounts/exporters/accounts.py`
- `apps/accounts/exporters/audit.py`
- `apps/accounts/gdpr_exceptions.py`
- `apps/accounts/services/gdpr_service.py`
- `apps/accounts/tasks.py`
- `apps/accounts/gdpr_urls.py`
- `apps/accounts/migrations/0003_gdpr_export_request.py`
- `apps/accounts/templates/accounts/email/gdpr_export_ready.html`
- `apps/accounts/templates/accounts/email/gdpr_export_ready.txt`
- `apps/accounts/templates/accounts/email/gdpr_export_password.html`
- `apps/accounts/templates/accounts/email/gdpr_export_password.txt`
- `apps/accounts/templates/accounts/email/gdpr_export_failed.html`
- `apps/accounts/templates/accounts/email/gdpr_export_failed.txt`
- `apps/accounts/tests/conftest.py`
- `apps/accounts/tests/test_gdpr_models.py`
- `apps/accounts/tests/test_gdpr_exporters.py`
- `apps/accounts/tests/test_gdpr_service.py`
- `apps/accounts/tests/test_gdpr_tasks.py`
- `apps/accounts/tests/test_gdpr_views.py`

**Backend (apps/api) — modifiés :**
- `apps/accounts/apps.py` (autoload exporters cross-app)
- `apps/accounts/models.py` (ajout `GdprExportStatus` + `GdprExportRequest`)
- `apps/accounts/serializers.py` (ajout `GdprExportRequestSerializer`)
- `apps/accounts/views.py` (ajout `GdprExportViewSet` + throttle + pagination)
- `apps/accounts/tests/factories.py` (ajout `GdprExportRequestFactory` + `ReadyGdprExportFactory`)
- `path_advisor/celery.py` (beat `gdpr-expire-old-exports`)
- `path_advisor/settings/base.py` (6 settings GDPR + `DEFAULT_THROTTLE_RATES`)
- `path_advisor/urls.py` (mount `/api/v1/me/`)
- `pyproject.toml` (ajout `pyzipper`)

**Frontend (apps/web) — créés :**
- `src/lib/api/gdpr.ts`
- `src/components/features/gdpr/gdpr-export-status-badge.tsx`
- `src/components/features/gdpr/gdpr-export-card.tsx`
- `src/components/features/gdpr/gdpr-export-card.test.tsx`
- `src/components/features/gdpr/gdpr-export-list.tsx`
- `src/app/(authenticated)/parametres/confidentialite/page.tsx`
- `src/app/(authenticated)/parametres/confidentialite/mes-donnees/page.tsx`

**Docs — créés :**
- `docs/runbooks/gdpr-request.md`

**Story tracking — modifiés :**
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `_bmad-output/implementation-artifacts/1-11-export-portabilite-rgpd.md`
