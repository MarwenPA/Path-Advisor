"""Celery tasks for billing — Story 5.2.

`process_dunning` runs daily (beat) to send J+0/J+3/J+7 dunning emails and
downgrade grace-expired past_due subscriptions to free.
"""

from __future__ import annotations

from celery import shared_task

from apps.billing.services.subscription_service import SubscriptionService


@shared_task(name="billing.process_dunning")
def process_dunning() -> int:
    return SubscriptionService.process_dunning()
