"""Audit hash chain MUST survive a user hard-delete (Story 1.12 §AC7).

`AuditLog.actor_id` and `subject_id` are CharField (not FK), so the rows
referencing a hard-deleted user persist with valid hash linkage. The chain
integrity check (`audit.verify_chain_integrity`) must keep returning zero
broken rows even after the user row that originated the audit entries is
gone.
"""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.accounts.services import account_deletion as deletion_service
from apps.accounts.tests.factories import UserFactory
from apps.audit.decorators import record_audit
from apps.audit.models import AuditLog, AuditResult
from apps.audit.services.hash_chain import verify_chain

pytestmark = pytest.mark.django_db


_PWD = "Path-Advisor-2026!"


def test_audit_chain_intact_after_user_hard_delete():
    user = UserFactory()
    user_id = user.id

    # Generate a handful of audit rows referencing this user as actor and subject.
    for i in range(5):
        record_audit(
            action=f"test.action_{i}",
            result=AuditResult.SUCCESS,
            actor=user,
            subject_id=user.id,
            metadata={"i": i},
        )

    # Snapshot the chain state BEFORE the hard-delete.
    rows_before = list(AuditLog.objects.filter(subject_id=user_id).order_by("created_at"))
    assert len(rows_before) >= 5

    # Request + hard-delete the user.
    deletion = deletion_service.request_deletion(user=user, password=_PWD)
    deletion.hard_delete_after = timezone.now() - timedelta(seconds=1)
    deletion.save(update_fields=["hard_delete_after"])
    with patch(
        "apps.accounts.services.account_deletion._purge_s3_prefixes",
        return_value=(0, []),
    ):
        deletion_service.hard_delete(deletion)

    # The user row is gone but the audit rows persist (CharField subject_id).
    rows_after = list(AuditLog.objects.filter(subject_id=user_id).order_by("created_at"))
    assert len(rows_after) >= len(rows_before)  # plus the deletion / hard-delete rows

    # Chain integrity over the whole table — no breaks introduced by the cascade.
    all_rows = list(AuditLog.objects.all().order_by("created_at"))
    broken = verify_chain(all_rows)
    assert broken == [], f"chain broke after hard_delete: {broken}"
