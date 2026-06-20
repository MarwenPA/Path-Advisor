# ADR 0011 — Séparation Django (app) vs FastAPI (scoring IA)

**Date :** 2026-06-20
**Status :** Accepted
**Story :** 3.1 — Service IA activé pour le scoring vocationnel

---

## Context

Path-Advisor nécessite un moteur de recommandation vocationnel capable de scorer 50+ métiers par profil élève en < 3 s P95. Ce moteur utilise des bibliothèques Python ML/DL (scikit-learn, sentence-transformers, pandas) et doit pouvoir scaler indépendamment des pics saisonniers (janvier–mars pour Parcoursup).

Django 5 + DRF gère déjà l'auth, le multi-tenant, la persistance et l'API REST. Deux options ont été évaluées :

1. Intégrer le scoring directement dans Django (même conteneur)
2. Dédier FastAPI dans un conteneur séparé pour le scoring IA

## Decision

**FastAPI déployé comme microservice séparé** (`apps/ai-service`), communiquant avec Django via HTTP synchrone pour le scoring on-demand.

## Rationale

| Critère | Django intégré | FastAPI séparé |
|---|---|---|
| Scaling indépendant | ❌ Couplé au web | ✅ Réplicas séparés |
| Écosystème ML | ⚠️ Compatible mais lourd | ✅ Natif Python/ML |
| Déploiement MVP | ✅ Simple | ✅ Docker Compose suffit |
| Latence réseau | 0 ms | +5–15 ms (réseau Docker) |
| Isolation des pannes | ❌ OOM = down web | ✅ Séparé |

L'ajout de bibliothèques ML dans le conteneur Django aurait alourdi l'image (+ ~2 Go) et empêché le scaling horizontal indépendant du scoring lors des pics saisonniers (NFR-SC4).

## Protocol de communication

```
Django (pa-api:8000)
  └─ POST http://ai-service:8001/v1/score-metiers
       Authorization: Bearer <JWT HS256 court TTL>
```

- **Authentification service-to-service** : JWT HS256 signé par Django, vérifié par FastAPI
- **Secret partagé** : `AI_SERVICE_JWT_SECRET` (variable d'env, jamais hardcodé)
- **TTL JWT** : 5 minutes (`AI_SERVICE_JWT_TTL_SECONDS=300`)
- **Timeout HTTP** : 5 secondes côté Django (`AIClient`)
- **Format d'erreur sur timeout/5xx** : `AIServiceUnavailableError` (hérite de `DomainError`)

## Façade unique

Django ne connaît le ai-service que via `apps.recommendations.services.ai_client.AIClient`.  
Aucun autre module Django ne doit importer ou appeler directement le ai-service.

## Limitations MVP

- **1 seule VM** Docker Compose : le "scaling indépendant" est configuré mais pas activé en production MVP. La valeur réelle arrive en growth (Scaleway K8s ou Functions).
- **Synchrone uniquement** pour cette story : pas de batch Celery. Le recalcul async (lors d'un changement de profil) sera implémenté en Story 3.3+.
- **Stateless côté IA** : le ai-service ne lit pas la DB directement — Django lui passe le profil sérialisé dans le body. Cela simplifie les tests et la montée en charge.

## Stateless design du ai-service

Le service IA est stateless côté données en MVP :
- Le profil élève est passé intégralement par Django dans le request body
- Le ai-service ne lit jamais directement PostgreSQL pour les données métier
- Seule exception prévue : lecture du référentiel professions en DB (Story 3.3) — accès lecture seule, cacheable

## Évolutions futures

- **Story 3.3** : ajout du vrai scorer statistique + content-based dans `domain/recommendation/statistical_scorer.py`
- **Story 3.3+** : batch Celery pour recalcul cohorte (async, découplé du chemin critique)
- **Growth** : MLflow pour le versioning modèles, K8s Scaleway pour l'autoscaling horizontal
