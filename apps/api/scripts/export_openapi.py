"""Export the live OpenAPI schema to packages/openapi/openapi.json.

Run via `make openapi` from the repo root, or `uv run python scripts/export_openapi.py`.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "path_advisor.settings.local")
    # Add repo root to sys.path so `import django` and `apps.*` resolve.
    api_root = Path(__file__).resolve().parent.parent
    if str(api_root) not in sys.path:
        sys.path.insert(0, str(api_root))

    import django

    django.setup()

    from drf_spectacular.generators import SchemaGenerator

    schema = SchemaGenerator().get_schema(request=None, public=True)

    repo_root = api_root.parent.parent
    out = repo_root / "packages" / "openapi" / "openapi.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"OpenAPI schema written to {out.relative_to(repo_root)}")


if __name__ == "__main__":
    main()
