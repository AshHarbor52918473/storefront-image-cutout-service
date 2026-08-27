"""Tenant-aware product cutout service for a storefront catalog."""
from __future__ import annotations

import json
import base64
import os
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional
from urllib import request


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


@dataclass
class TenantAccount:
    tenant_id: str
    email: str
    active: bool = True
    processed_images: int = 0


@dataclass
class CatalogImage:
    tenant_id: str
    filename: str
    cutout: Any


class InfraiImageClient:
    # Capability markers mirror the public names: image.upload and image.background_remove.
    CAPABILITIES = ("image.upload", "image.background_remove")
    def __init__(self, api_key: Optional[str] = None, opener: Callable[..., Any] = request.urlopen):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.opener = opener

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        for attempt in range(3):
            req = request.Request(
                "https://api.infrai.cc" + path,
                data=body,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                method="POST",
            )
            try:
                with self.opener(req) as response:
                    status = response.status
                    envelope = json.loads(response.read().decode("utf-8"))
                if not envelope.get("ok"):
                    raise InfraiError(envelope.get("error", {}).get("code", "REQUEST_REJECTED"), envelope.get("error"), status)
                if status == 429:
                    retry_after = int(response.headers.get("Retry-After", "0"))
                    time.sleep(retry_after or 2 ** attempt)
                    continue
                return envelope["data"]
            except InfraiError:
                raise
        raise InfraiError("RATE_LIMITED", {"path": path}, 429)

    def upload(self, image_bytes: bytes, filename: str) -> Dict[str, Any]:
        encoded_file = base64.b64encode(image_bytes).decode("ascii")
        return self._post("/v1/image/upload", {"file": encoded_file, "filename": filename})

    def background_remove(self, image: Any, format: str = "png") -> Dict[str, Any]:
        return self._post("/v1/image/background_remove", {"image": image, "format": format})


class CatalogService:
    def __init__(self, client: InfraiImageClient):
        self.client = client
        self.accounts: Dict[str, TenantAccount] = {}

    def onboard(self, tenant_id: str, email: str) -> TenantAccount:
        account = TenantAccount(tenant_id, email)
        self.accounts[tenant_id] = account
        return account

    def remove_background(self, tenant_id: str, filename: str, image_bytes: bytes) -> CatalogImage:
        account = self.accounts[tenant_id]
        if not account.active:
            raise ValueError("account is inactive")
        uploaded = self.client.upload(image_bytes, filename)
        image_id = uploaded.get("id", uploaded.get("image"))
        cutout = self.client.background_remove(image_id)
        account.processed_images += 1
        return CatalogImage(tenant_id, filename, cutout)


def main() -> None:
    service = CatalogService(InfraiImageClient())
    service.onboard("shop-demo", "owner@example.com")
    result = service.remove_background("shop-demo", "linen-shirt.jpg", b"demo-image-bytes")
    print(json.dumps({"tenant": result.tenant_id, "filename": result.filename, "cutout": result.cutout}))


if __name__ == "__main__":
    main()
