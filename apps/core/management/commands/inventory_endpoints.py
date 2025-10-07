from django.core.management.base import BaseCommand
from django.urls import get_resolver, URLPattern, URLResolver
from django.conf import settings
import json
import csv
from pathlib import Path

class Command(BaseCommand):
    help = "Inventory all URL endpoints (path, name, view, methods), flag likely API routes and auth requirements."

    def add_arguments(self, parser):
        parser.add_argument("--format", choices=["json", "csv"], default="json")
        parser.add_argument("--output", type=str, default="endpoint_inventory.json")

    def handle(self, *args, **options):
        fmt = options["format"]
        output = Path(options["output"]).resolve()

        resolver = get_resolver()
        records = []

        def walk_patterns(patterns, prefix="", namespace=None):
            for p in patterns:
                if isinstance(p, URLPattern):
                    path = f"{prefix}{p.pattern}"
                    name = p.name or ""
                    view = getattr(p.callback, "__name__", str(p.callback))
                    app_ns = namespace or getattr(p, "namespace", "")
                    is_api = path.startswith("api/") or "/api/" in path
                    is_public = path.startswith("public/") or "/public/" in path
                    # Methods are not directly available for CBVs; mark unknown
                    methods = getattr(p.callback, "allowed_methods", ["GET","POST","PUT","PATCH","DELETE","HEAD","OPTIONS"])
                    requires_auth = not is_public

                    records.append({
                        "path": f"/{path}",
                        "name": name,
                        "view": view,
                        "namespace": app_ns,
                        "methods": list(methods),
                        "is_api": bool(is_api),
                        "requires_auth": bool(requires_auth),
                    })
                elif isinstance(p, URLResolver):
                    ns = p.namespace or namespace
                    walk_patterns(p.url_patterns, prefix=f"{prefix}{p.pattern}", namespace=ns)

        walk_patterns(resolver.url_patterns)

        output.parent.mkdir(parents=True, exist_ok=True)
        if fmt == "json":
            output.write_text(json.dumps(records, indent=2))
        else:
            with output.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(records[0].keys()) if records else ["path"]) 
                writer.writeheader()
                for r in records:
                    writer.writerow(r)

        self.stdout.write(self.style.SUCCESS(f"Wrote {len(records)} endpoints to {output}"))
