# Non-Functional Requirements

## Performance

- **NFR-P1 :** Une recommandation vocationnelle complète (top 8 métiers + explicabilité) doit être servie en **< 3 secondes** au P95 en MVP, **< 1,5 seconde** au P95 en growth
- **NFR-P2 :** Un graphe de parcours avec stats d'admission personnalisées doit s'afficher en **< 2 secondes** au P95
- **NFR-P3 :** Une page publique métier/formation (SEO) doit avoir un **TTFB < 1 seconde** et un **LCP mobile < 2,5 secondes** (cible Core Web Vitals)
- **NFR-P4 :** L'OCR d'un bulletin standard doit aboutir en **< 30 secondes** au P95
- **NFR-P5 :** Une mise à jour de statistique d'admission suite à une réponse école doit être propagée à l'élève (push + email) en **< 5 minutes**
- **NFR-P6 :** L'authentification d'un utilisateur (élève, parent, conseiller, école) doit aboutir en **< 1 seconde** au P95

## Security

- **NFR-S1 :** Toutes les données personnelles (profil, bulletins, communications) doivent être **chiffrées au repos en AES-256** et **en transit via TLS 1.3 minimum**
- **NFR-S2 :** L'accès aux comptes conseiller, école et admin doit imposer une **MFA obligatoire** (TOTP ou WebAuthn), l'accès B2C peut activer la MFA en option
- **NFR-S3 :** Les bulletins scolaires PDF doivent être stockés dans un bucket S3-compatible chiffré (clé de chiffrement gérée par hébergeur ou KMS dédié), région UE obligatoire
- **NFR-S4 :** Le système doit produire un **journal d'audit immuable** de tout accès aux données personnelles d'un élève par un tiers (parent, conseiller, école, admin), conservé 3 ans
- **NFR-S5 :** Les secrets applicatifs (clés API, tokens, mots de passe DB) doivent être stockés dans un coffre dédié (HashiCorp Vault, AWS Secrets Manager, ou équivalent self-hosted en PoC)
- **NFR-S6 :** Le système doit respecter les **délais légaux RGPD** : notification d'incident à la CNIL **< 72 heures**, réponse à une demande d'accès / suppression **< 30 jours**
- **NFR-S7 :** Une DPIA documentée doit exister et être à jour avant tout déploiement en production
- **NFR-S8 :** Le système doit prévenir les attaques OWASP Top 10 (injection, XSS, CSRF, broken auth, SSRF, etc.), validé par un audit interne en MVP et **pen-test annuel externe** en growth
- **NFR-S9 :** Un consentement parental email vérifié doit être obtenu avant toute création de compte pour un utilisateur **< 15 ans**, et tracé avec horodatage immuable

## Scalability

- **NFR-SC1 :** Le système doit supporter **500 MAU en MVP** (production-ready) et permettre une montée en charge jusqu'à **10 000 MAU en growth** sans refonte architecturale majeure
- **NFR-SC2 :** Le système doit supporter **500 utilisateurs concurrents** lors des pics saisonniers (janvier-mars, mai-juillet) sans dégradation perçue
- **NFR-SC3 :** L'auto-scaling de l'infrastructure doit pouvoir **multiplier x3 la capacité** en moins de 10 minutes sur déclencheur de charge
- **NFR-SC4 :** Le moteur de recommandation doit pouvoir être déployé indépendamment du back applicatif (scaling horizontal séparé)
- **NFR-SC5 :** Le référentiel de professions et formations doit pouvoir croître de **50 → 500 entrées** sans dégradation de la latence de recommandation
- **NFR-SC6 :** La base de données doit supporter au minimum **100 000 profils élèves** en production (objectif vision long terme)

## Reliability

- **NFR-R1 :** La disponibilité de la plateforme doit être **≥ 99 %** en MVP (downtime ≤ 7h/mois) et **≥ 99,5 %** en growth
- **NFR-R2 :** Le système doit disposer d'une **sauvegarde quotidienne** des données de production avec rétention de 30 jours minimum, **testée mensuellement** par restauration partielle
- **NFR-R3 :** Le **Recovery Time Objective (RTO)** doit être **< 4 heures**, le **Recovery Point Objective (RPO) < 1 heure**
- **NFR-R4 :** Le système doit dégrader gracieusement en cas de panne d'un service tiers (OCR indisponible → fallback saisie manuelle ; Stripe indisponible → file d'attente paiement ; email indisponible → retry asynchrone)
- **NFR-R5 :** Le système doit disposer d'une observabilité production complète (logs centralisés, métriques, alerting) avec un **MTTR cible < 1 heure** sur incident critique

## Accessibility

- **NFR-A1 :** Les **parcours utilisateurs critiques** (inscription, onboarding, consultation recommandation, consultation graphe de parcours, déclenchement envoi anticipé) doivent être conformes **RGAA 4.1 niveau AA** dès le MVP
- **NFR-A2 :** L'ensemble du produit doit atteindre la conformité **RGAA 4.1 niveau AA** en growth (prérequis B2B Éducation Nationale)
- **NFR-A3 :** L'interface doit être pleinement utilisable au clavier seul (navigation, sélections, validation de formulaire)
- **NFR-A4 :** Les contrastes texte/fond doivent respecter un ratio **≥ 4,5:1** pour le texte normal et **≥ 3:1** pour le texte large
- **NFR-A5 :** Les graphes de parcours doivent fournir une **alternative textuelle structurée** (tableau, liste séquentielle) accessible aux lecteurs d'écran
- **NFR-A6 :** Le produit doit être utilisable sur écrans mobiles dès **320 px de largeur** (cible smartphones bas de gamme)

## Integration

- **NFR-I1 :** L'intégration avec **Stripe** (paiement B2C) doit supporter le mode test local (clés sandbox) en PoC et le mode production en cloud
- **NFR-I2 :** L'intégration avec un service email transactionnel (Postmark, SendGrid) doit pouvoir être substituée par **Mailpit local** en PoC sans modification du code applicatif (couche d'abstraction)
- **NFR-I3 :** L'intégration OCR (AWS Textract / Mindee en production) doit pouvoir être substituée par **Tesseract OCR local** en PoC avec une dégradation acceptable de précision
- **NFR-I4 :** L'analytique produit (PostHog / Amplitude) doit respecter le **hébergement EU** ou être **self-hosted**
- **NFR-I5 :** Le système doit exposer des **données ouvertes anonymisées** (référentiel formations enrichi, tendances orientation) sous licence Etalab en growth (positionnement institutionnel)
- **NFR-I6 :** L'intégration ENT/Pronote en growth doit être **opt-in côté établissement** et **opt-in côté élève** (double consentement RGPD)
- **NFR-I7 :** Le système doit pouvoir consommer les **datasets open data Parcoursup** (CSV mis à jour annuellement par le MENJS) pour alimenter les stats d'admission

## Maintenability & Evolvability (équipe restreinte)

- **NFR-M1 :** L'ensemble de la stack (front, back, IA, DB, cache, queue, OCR, mail, monitoring, analytics, stockage) doit pouvoir être lancée localement par **`docker-compose up` en moins de 5 minutes**, avec données de seed pour un produit utilisable end-to-end
- **NFR-M2 :** Le code doit respecter une **couverture de tests automatisés ≥ 70 %** sur les zones critiques (auth, RBAC, moteur reco, paiement, RGPD)
- **NFR-M3 :** Toute modification du **modèle de recommandation IA** doit être versionnée avec dataset d'entraînement, hyperparamètres et métriques d'évaluation tracés
- **NFR-M4 :** L'architecture doit être documentée via **Architecture Decision Records (ADR)** versionnés en git, mis à jour à chaque choix structurant
- **NFR-M5 :** Le système doit pouvoir être maintenu et opéré par **1 à 2 personnes** sans dépendance critique à un savoir tacite — toute opération critique (déploiement, restauration, modération) doit être documentée sous forme de runbook
