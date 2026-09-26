"""Story 8.3 — the calendar notifications' copy, in ONE reviewable place.

UX-DR28 is enforced by test, not by intention: everything below is rendered
and linted against urgency markers (see `tests/test_parcoursup_calendar.py`).
The stance for every milestone: « Voici où on en est. Voici ce que tu peux
préparer d'ici là. » Checklists are non-blocking suggestions, CTAs are calm.
"""

from __future__ import annotations

from .models import MilestoneKind

#: Per-kind copy. `subject`/`intro` accept {date} (formatted, French).
MILESTONE_COPY: dict[str, dict[str, object]] = {
    MilestoneKind.OUVERTURE: {
        "subject": "Parcoursup : la plateforme ouvre le {date}",
        "intro": (
            "La plateforme Parcoursup ouvre le {date}. D'ici là, rien d'obligatoire — "
            "voici ce que tu peux préparer tranquillement si tu le souhaites."
        ),
        "checklist": [
            "Relire tes métiers recommandés et tes paris enregistrés",
            "Vérifier que ton profil est à jour (spécialités, notes récentes)",
            "Repérer les formations qui t'intéressent et leurs attendus",
        ],
        "cta_label": "Revoir mes paris",
        "cta_path": "/mes-paris",
    },
    MilestoneKind.J30_FERMETURE_VOEUX: {
        "subject": "Parcoursup : la fermeture des vœux approche ({date})",
        "intro": (
            "Les vœux Parcoursup peuvent être formulés jusqu'au {date}. Il reste du temps — "
            "voici où tu peux en être aujourd'hui, et ce que tu peux préparer d'ici là."
        ),
        "checklist": [
            "Passer en revue la liste de tes vœux envisagés",
            "Comparer tes paris avec tes chances d'admission estimées",
            "Noter les questions à poser à un professeur ou une conseillère",
        ],
        "cta_label": "Revoir mes paris",
        "cta_path": "/mes-paris",
    },
    MilestoneKind.FERMETURE_VOEUX: {
        "subject": "Parcoursup : les vœux ferment le {date}",
        "intro": (
            "La saisie des vœux se termine le {date}. Si tes vœux sont déjà posés, "
            "tout est en ordre — sinon, voici de quoi finaliser sereinement."
        ),
        "checklist": [
            "Confirmer la liste de tes vœux sur Parcoursup",
            "Relire tes projets de formation motivés",
            "Garder une copie de tes vœux pour en parler autour de toi",
        ],
        "cta_label": "Revoir mes paris",
        "cta_path": "/mes-paris",
    },
    MilestoneKind.RESULTATS_PRINCIPALE: {
        "subject": "Parcoursup : les premières réponses arrivent le {date}",
        "intro": (
            "Les réponses de la phase principale commencent le {date}. Quel que soit le "
            "résultat, des options existent — voici comment t'y préparer calmement."
        ),
        "checklist": [
            "Relire le fonctionnement des réponses (oui, oui-si, en attente)",
            "Réfléchir à ton ordre de préférence si plusieurs oui arrivent",
            "Repérer les formations de la phase complémentaire au cas où",
        ],
        "cta_label": "Compléter mon profil",
        "cta_path": "/profile",
    },
    MilestoneKind.RESULTATS_COMPLEMENTAIRE: {
        "subject": "Parcoursup : la phase complémentaire s'ouvre le {date}",
        "intro": (
            "La phase complémentaire ouvre le {date} : des places restent disponibles dans "
            "de nombreuses formations. Voici comment l'aborder posément."
        ),
        "checklist": [
            "Explorer les formations avec des places disponibles",
            "Vérifier lesquelles correspondent à tes métiers recommandés",
            "Préparer un projet de formation motivé réutilisable",
        ],
        "cta_label": "Revoir mes paris",
        "cta_path": "/mes-paris",
    },
}
