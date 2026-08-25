"""``IsLinkedParent`` — Story 6.1 §AC7 / §4.5.

The RBAC building block future stories (6.2 parent dashboard, 6.3
confidentiality frontier) compose to gate parent access to a specific
student's endpoints. `ParentStudentLink` (non-revoked) is the SOLE source of
authorization — no fallback on email or any other heuristic.

Story 6.1 does not ship any parent-facing data endpoint itself (that's 6.2) —
this class exists so the invariant is testable now and reusable without
re-deriving the query later.
"""

from __future__ import annotations

from apps.accounts.models import User, UserRole
from apps.core.permissions import PathAdvisorPermission
from apps.family.models import ParentStudentLink


class IsLinkedParent(PathAdvisorPermission):
    """`request.user` must be `role="parent"` AND hold a non-revoked
    `ParentStudentLink` to the student identified by `obj` (a `User` or any
    object exposing `.student_id` / `.student`).
    """

    allowed_roles = frozenset({UserRole.PARENT.value})

    def has_object_permission(self, request, view, obj) -> bool:
        if not super().has_permission(request, view):
            return False
        student_id = getattr(obj, "student_id", None) or getattr(obj, "id", None)
        if isinstance(obj, User):
            student_id = obj.id
        return ParentStudentLink.objects.filter(
            parent=request.user,
            student_id=student_id,
            revoked_at__isnull=True,
        ).exists()
