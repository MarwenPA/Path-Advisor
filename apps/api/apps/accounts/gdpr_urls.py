"""URL routing for GDPR Article 20 exports — mounted under /api/v1/me/.

Kept separate from `accounts/urls.py` (which sits under /api/v1/auth/) so the
two URL namespaces — auth bootstrap and "my account" surface — stay clearly
distinct. Future "me/*" endpoints (consents, deletion, settings) join this
file.
"""

from __future__ import annotations

from rest_framework.routers import DefaultRouter

from apps.accounts.views import GdprExportViewSet

router = DefaultRouter()
router.register(
    r"gdpr-exports",
    GdprExportViewSet,
    basename="gdpr-exports",
)

app_name = "me"

urlpatterns = router.urls
