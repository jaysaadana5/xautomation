from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from .oauth1 import authorization_header


class ActionError(RuntimeError):
    pass


def _request(request: Request) -> dict:
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode())
    except HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:1000]
        raise ActionError(f"HTTP {exc.code}: {detail}") from exc


@dataclass
class XPoster:
    endpoint: str = "https://api.x.com/2/tweets"

    def run(self, payload: dict) -> dict:
        text = payload.get("text", "").strip()
        if not text or len(text) > 280:
            raise ActionError("X post text must contain 1 to 280 characters")
        names = (
            "X_API_KEY",
            "X_API_SECRET",
            "X_ACCESS_TOKEN",
            "X_ACCESS_TOKEN_SECRET",
        )
        values = [os.environ.get(name) for name in names]
        missing = [name for name, value in zip(names, values) if not value]
        if missing:
            raise ActionError(f"Missing secrets: {', '.join(missing)}")
        body = json.dumps({"text": text}).encode()
        header = authorization_header("POST", self.endpoint, *values)  # type: ignore[arg-type]
        return _request(
            Request(
                self.endpoint,
                data=body,
                method="POST",
                headers={"Authorization": header, "Content-Type": "application/json"},
            )
        )


@dataclass
class Webhook:
    def run(self, payload: dict) -> dict:
        url = payload.get("url") or os.environ.get("AUTOMATION_WEBHOOK_URL")
        if not url or not url.startswith("https://"):
            raise ActionError("Webhook requires an https URL")
        token = os.environ.get("AUTOMATION_WEBHOOK_TOKEN")
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        body = json.dumps(payload.get("body", {})).encode()
        return _request(Request(url, data=body, method="POST", headers=headers))


ACTIONS = {"x_post": XPoster(), "webhook": Webhook()}

