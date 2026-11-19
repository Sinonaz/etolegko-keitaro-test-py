"""Keitaro Admin API client (admin_api/v1)."""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import Settings, get_settings
from app.services.keitaro.exceptions import (
    KeitaroAPIError,
    KeitaroNotConfiguredError,
)

JsonDict = dict[str, Any]
JsonValue = Any


class KeitaroClient:
    """Thin HTTP wrapper around Keitaro Admin API.

    Docs: https://admin-api.docs.keitaro.io/
    Auth header: ``Api-Key: <key>``
    Base path: ``{KEITARO_URL}/admin_api/v1``
    """

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        timeout: float = 30.0,
    ) -> None:
        self.settings = settings or get_settings()
        self.base_url = self.settings.keitaro_url.rstrip("/")
        self.api_key = self.settings.keitaro_api_key
        self._timeout = timeout
        self._client: httpx.Client | None = None

    @property
    def is_configured(self) -> bool:
        return bool(self.base_url and self.api_key)

    def _ensure_configured(self) -> None:
        if not self.is_configured:
            raise KeitaroNotConfiguredError(
                "Set KEITARO_URL and KEITARO_API_KEY in backend/.env"
            )

    def _get_http(self) -> httpx.Client:
        self._ensure_configured()
        if self._client is None:
            self._client = httpx.Client(
                base_url=f"{self.base_url}/admin_api/v1",
                headers={
                    "Api-Key": self.api_key,
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                timeout=self._timeout,
            )
        return self._client

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> KeitaroClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: JsonValue | None = None,
    ) -> JsonValue:
        http = self._get_http()
        try:
            response = http.request(method, path, params=params, json=json)
        except httpx.HTTPError as exc:
            raise KeitaroAPIError(
                f"Keitaro {method} {path} unreachable: {exc}",
                status_code=None,
                payload={"url": self.base_url},
            ) from exc

        if response.status_code >= 400:
            payload: object
            try:
                payload = response.json()
            except ValueError:
                payload = response.text
            raise KeitaroAPIError(
                f"Keitaro {method} {path} failed with HTTP {response.status_code}",
                status_code=response.status_code,
                payload=payload,
            )

        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    # --- health / ping ---

    def ping(self) -> bool:
        """Lightweight auth check: list campaigns with limit=1."""
        self.list_campaigns(limit=1)
        return True

    # --- campaigns ---

    def list_campaigns(
        self,
        *,
        offset: int | None = None,
        limit: int | None = None,
    ) -> list[JsonDict]:
        params: dict[str, Any] = {}
        if offset is not None:
            params["offset"] = offset
        if limit is not None:
            params["limit"] = limit
        data = self._request("GET", "/campaigns", params=params or None)
        return _as_list(data)

    def get_campaign(self, campaign_id: int) -> JsonDict:
        return _as_dict(self._request("GET", f"/campaigns/{campaign_id}"))

    def create_campaign(self, payload: JsonDict) -> JsonDict:
        return _as_dict(self._request("POST", "/campaigns", json=payload))

    def update_campaign(self, campaign_id: int, payload: JsonDict) -> JsonDict:
        return _as_dict(self._request("PUT", f"/campaigns/{campaign_id}", json=payload))

    # --- streams (flows) ---

    def list_campaign_streams(self, campaign_id: int) -> list[JsonDict]:
        data = self._request("GET", f"/campaigns/{campaign_id}/streams")
        return _as_list(data)

    def get_stream(self, stream_id: int) -> JsonDict:
        return _as_dict(self._request("GET", f"/streams/{stream_id}"))

    def create_stream(self, payload: JsonDict) -> JsonDict:
        return _as_dict(self._request("POST", "/streams", json=payload))

    def update_stream(self, stream_id: int, payload: JsonDict) -> JsonDict:
        return _as_dict(self._request("PUT", f"/streams/{stream_id}", json=payload))

    # --- offers ---

    def list_offers(self) -> list[JsonDict]:
        return _as_list(self._request("GET", "/offers"))

    def get_offer(self, offer_id: int) -> JsonDict:
        return _as_dict(self._request("GET", f"/offers/{offer_id}"))

    def search_offers(self, query: str, *, limit: int = 20) -> list[JsonDict]:
        """Client-side filter: Admin API has no dedicated offer search."""
        q = query.strip().lower()
        if not q:
            return []

        matched: list[JsonDict] = []
        for offer in self.list_offers():
            haystack = " ".join(
                str(offer.get(key, ""))
                for key in ("id", "name", "group", "notes", "offer_type")
            ).lower()
            if q in haystack:
                matched.append(offer)
            if len(matched) >= limit:
                break
        return matched

    # --- domains / groups / traffic sources ---

    def list_domains(self) -> list[JsonDict]:
        return _as_list(self._request("GET", "/domains"))

    def list_groups(self, group_type: str = "campaigns") -> list[JsonDict]:
        return _as_list(
            self._request("GET", "/groups", params={"type": group_type})
        )

    def list_traffic_sources(self) -> list[JsonDict]:
        return _as_list(self._request("GET", "/traffic_sources"))


def _as_list(data: JsonValue) -> list[JsonDict]:
    if data is None:
        return []
    if isinstance(data, list):
        return data
    raise KeitaroAPIError("Expected a JSON array from Keitaro", payload=data)


def _as_dict(data: JsonValue) -> JsonDict:
    if isinstance(data, dict):
        return data
    raise KeitaroAPIError("Expected a JSON object from Keitaro", payload=data)
