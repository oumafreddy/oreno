import json
import os
import uuid
from datetime import datetime, timezone

import requests
from django.core.management.base import BaseCommand, CommandError


TIKTOK_ENDPOINT = "https://business-api.tiktok.com/open_api/v1.3/pixel/track/"


class Command(BaseCommand):
    help = (
        "Send a TikTok Events API test event (server-side) with test_event_code to validate delivery."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "pixel_code", help="TikTok Pixel ID (aka sdkid/pixel_code from Events Manager)")
        parser.add_argument(
            "test_event_code", help="Test Event Code from the Pixel Test Events tab")
        parser.add_argument(
            "--event", default="CompleteRegistration", help="Event name to send (default: CompleteRegistration)")
        parser.add_argument(
            "--value", type=float, default=1.0, help="Numeric value for properties.value (default: 1.0)")
        parser.add_argument(
            "--currency", default="USD", help="Currency code for properties.currency (default: USD)")

    def handle(self, *args, **options):
        pixel_code = options["pixel_code"]
        test_event_code = options["test_event_code"]
        event_name = options["event"]
        value = options["value"]
        currency = options["currency"]

        access_token = os.getenv("TIKTOK_ACCESS_TOKEN")
        if not access_token:
            raise CommandError("TIKTOK_ACCESS_TOKEN env var is not set.")

        payload = {
            "pixel_code": pixel_code,
            "event": event_name,
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "test_event_code": test_event_code,
            # Minimal context; IP and UA help attribution in tests
            "context": {
                "ip": "8.8.8.8",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            },
            # Dummy SHA-256 hashes (empty-string hash) for testing
            "user": {
                "external_id": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "email": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            },
            "properties": {
                "value": value,
                "currency": currency
            }
        }

        headers = {
            "Content-Type": "application/json",
            "Access-Token": access_token,
        }

        response = requests.post(TIKTOK_ENDPOINT, headers=headers, data=json.dumps(payload), timeout=30)
        try:
            body = response.json()
        except Exception:
            body = {"text": response.text}

        if response.status_code >= 400:
            raise CommandError(f"TikTok API error {response.status_code}: {body}")

        self.stdout.write(self.style.SUCCESS("TikTok test event sent successfully."))
        self.stdout.write(json.dumps(body, indent=2))


