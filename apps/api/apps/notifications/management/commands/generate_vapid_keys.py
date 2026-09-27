"""Story 10.2 — `manage.py generate_vapid_keys`.

Prints a FRESH VAPID keypair as env lines to copy into the gitignored
`.env` (dev) or the secrets manager (staging/prod). The private key is a
secret from the moment it is used: never commit it, never log it — rotate
by generating a new pair (browsers re-subscribe transparently on next
visit because the settings toggle re-reads the public key).
"""

from __future__ import annotations

from cryptography.hazmat.primitives import serialization
from django.core.management.base import BaseCommand
from py_vapid import Vapid02, b64urlencode


class Command(BaseCommand):
    help = "Génère une paire de clés VAPID (Web Push) à copier dans .env — jamais commitée."

    def handle(self, *args: object, **options: object) -> None:
        vapid = Vapid02()
        vapid.generate_keys()
        public = b64urlencode(
            vapid.public_key.public_bytes(
                serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
            )
        )
        private = b64urlencode(
            vapid.private_key.private_numbers().private_value.to_bytes(32, "big")
        )
        self.stdout.write(f"WEBPUSH_VAPID_PUBLIC_KEY={public}")
        self.stdout.write(f"WEBPUSH_VAPID_PRIVATE_KEY={private}")
