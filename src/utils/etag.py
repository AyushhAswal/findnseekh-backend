import hashlib
from typing import Optional
from starlette.types import ASGIApp, Receive, Scope, Send


def compute_etag(content: bytes) -> str:
    """Compute a weak ETag from response content bytes."""
    digest = hashlib.sha256(content).hexdigest()[:16]
    return f'W/"{digest}"'


class ETagMiddleware:
    """ASGI middleware that adds ETag and Cache-Control headers to GET/HEAD responses,
    and returns 304 Not Modified when the client's If-None-Match matches.
    """

    def __init__(
        self,
        app: ASGIApp,
        cache_control: str = "public, max-age=60, must-revalidate",
    ) -> None:
        self.app = app
        self.cache_control = cache_control

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] not in ("GET", "HEAD"):
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        if_none_match = headers.get(b"if-none-match", b"").decode("latin-1").strip()

        response_status = 200
        response_headers = []
        body_chunks = []

        async def send_wrapper(message: dict) -> None:
            nonlocal response_status, response_headers
            if message["type"] == "http.response.start":
                response_status = message["status"]
                response_headers = list(message.get("headers", []))
            elif message["type"] == "http.response.body":
                body_chunks.append(message.get("body", b""))
                if not message.get("more_body", False):
                    full_body = b"".join(body_chunks)

                    # Only process successful 200 OK responses
                    if response_status == 200:
                        computed_etag = compute_etag(full_body)
                        header_dict = {k.lower(): v for k, v in response_headers}

                        if b"etag" in header_dict:
                            etag_val = header_dict[b"etag"].decode("latin-1")
                        else:
                            etag_val = computed_etag
                            response_headers.append((b"etag", etag_val.encode("latin-1")))

                        if b"cache-control" not in header_dict and self.cache_control:
                            response_headers.append(
                                (b"cache-control", self.cache_control.encode("latin-1"))
                            )

                        # Check If-None-Match header
                        if if_none_match:
                            client_tags = [t.strip() for t in if_none_match.split(",")]
                            clean_etag = etag_val.strip()
                            clean_raw = clean_etag.lstrip("W/").strip('"')

                            matches = False
                            for tag in client_tags:
                                tag_raw = tag.lstrip("W/").strip('"')
                                if (
                                    tag == "*"
                                    or tag == clean_etag
                                    or tag_raw == clean_raw
                                ):
                                    matches = True
                                    break

                            if matches:
                                filtered_headers = [
                                    (k, v)
                                    for k, v in response_headers
                                    if k.lower()
                                    not in (b"content-length", b"content-type")
                                ]
                                filtered_headers.append((b"content-length", b"0"))
                                await send(
                                    {
                                        "type": "http.response.start",
                                        "status": 304,
                                        "headers": filtered_headers,
                                    }
                                )
                                await send(
                                    {
                                        "type": "http.response.body",
                                        "body": b"",
                                        "more_body": False,
                                    }
                                )
                                return

                    await send(
                        {
                            "type": "http.response.start",
                            "status": response_status,
                            "headers": response_headers,
                        }
                    )
                    await send(
                        {
                            "type": "http.response.body",
                            "body": full_body,
                            "more_body": False,
                        }
                    )
            else:
                await send(message)

        await self.app(scope, receive, send_wrapper)

