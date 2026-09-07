"""In-process log tail, so a reviewer without a Fly organisation seat can read the
request log over HTTP instead of installing flyctl. Bounded ring buffer: the last
LINES records only, held in memory, lost when the machine stops."""

import logging
import os
import re
import secrets
from collections import deque

LINES = 500
TOKEN_IN_URL = re.compile(r"token=[^&\s\"']+")


class RingHandler(logging.Handler):
    """Keeps the most recent formatted records; oldest is dropped first."""

    def __init__(self, capacity: int = LINES):
        super().__init__()
        self.records: deque[str] = deque(maxlen=capacity)

    def emit(self, record: logging.LogRecord) -> None:
        # An access log would otherwise store ?token=... in the very buffer it serves.
        self.records.append(TOKEN_IN_URL.sub("token=***", self.format(record)))

    def tail(self, limit: int) -> list[str]:
        return list(self.records)[-limit:]


def install(capacity: int = LINES) -> RingHandler:
    """Attach one buffer to the root logger; replaces a previous one on app rebuild."""
    root = logging.getLogger()
    for h in list(root.handlers):
        if isinstance(h, RingHandler):
            root.removeHandler(h)
    # The request logger, not the root: basicConfig() is a no-op under pytest and an
    # INFO record would never be emitted. Raising the root level would also un-silence
    # every library logger, which the buffer does not want.
    logging.getLogger("app.request").setLevel(logging.INFO)
    handler = RingHandler(capacity)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    root.addHandler(handler)
    return handler


def authorised(token: str | None, header: str | None, expected: str) -> bool:
    """Bearer header or ?token=; constant-time compare so the endpoint cannot be probed."""
    given = token
    if header and header.lower().startswith("bearer "):
        given = header[7:]
    return given is not None and secrets.compare_digest(given, expected)


def machine() -> dict[str, str]:
    """Whatever the host tells the container about itself; "local" off a host.
    Render names the instance and the deployed commit but exposes no region, so the
    region it was created in is passed as REGION in render.yaml. Fly is kept because
    fly.toml is still committed and the image is identical on both."""
    return {
        "id": os.environ.get("RENDER_INSTANCE_ID") or os.environ.get("FLY_MACHINE_ID", "local"),
        "region": os.environ.get("REGION") or os.environ.get("FLY_REGION", "local"),
        "release": os.environ.get("RENDER_GIT_COMMIT")
        or os.environ.get("FLY_MACHINE_VERSION", "unknown"),
    }
