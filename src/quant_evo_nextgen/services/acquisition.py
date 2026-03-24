from __future__ import annotations

from dataclasses import dataclass
import socket
import time
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from quant_evo_nextgen.config import Settings
from quant_evo_nextgen.services.skill_catalog import SkillCatalogService


@dataclass(slots=True)
class AcquisitionLayerStatus:
    key: str
    label: str
    status: str
    message: str
    details: dict[str, object] | None = None


@dataclass(slots=True)
class AcquisitionStackSummary:
    status: str
    primary_mode: str
    layers: list[AcquisitionLayerStatus]


class AcquisitionStackService:
    def __init__(
        self,
        settings: Settings,
        *,
        endpoint_probe_timeout_seconds: float = 2.5,
    ) -> None:
        self.settings = settings
        self.endpoint_probe_timeout_seconds = endpoint_probe_timeout_seconds
        self.skill_catalog = SkillCatalogService(
            settings.resolved_repo_root,
            skill_root=settings.skill_library_root,
        )

    def build_summary(self, *, probe_endpoints: bool = False) -> AcquisitionStackSummary:
        layers = [
            self._official_api_layer(),
            self._hosted_search_layer(),
            self._search_scrape_layer(probe_endpoints=probe_endpoints),
            self._feed_router_layer(probe_endpoints=probe_endpoints),
            self._skill_pack_layer(),
            self._browser_fallback_layer(probe_endpoints=probe_endpoints),
        ]
        if any(layer.status == "fail" for layer in layers[:2]):
            overall = "fail"
        elif all(layer.status == "warn" for layer in layers):
            overall = "warn"
        elif any(layer.status == "warn" for layer in layers):
            overall = "warn"
        else:
            overall = "ok"

        primary_mode = "hosted_web_search"
        if layers[1].status != "ok" and layers[2].status == "ok":
            primary_mode = "self_hosted_metasearch"
        elif layers[1].status == "ok" and layers[2].status == "ok" and layers[3].status == "ok":
            primary_mode = "hosted_web_search_plus_local_fallbacks"
        elif layers[1].status == "ok" and layers[2].status == "ok":
            primary_mode = "hosted_web_search_plus_local_metasearch"
        if layers[0].status == "ok":
            primary_mode = f"official_apis_plus_{primary_mode}"
        return AcquisitionStackSummary(status=overall, primary_mode=primary_mode, layers=layers)

    def prompt_guidance(self) -> str:
        summary = self.build_summary()
        skill_guidance = self.skill_catalog.build_acquisition_guidance(
            include_playwright=self._playwright_enabled()
        )
        market_mode = (self.settings.deployment_market_mode or "us").strip().lower() or "us"
        active_sleeves = self._active_sleeves_for_market_mode(market_mode)
        sleeve_text = ", ".join(active_sleeves) if active_sleeves else "unconfigured"
        lines = [
            f"Deployment market mode: {market_mode}; active sleeves: {sleeve_text}.",
            "Use the governed layered acquisition stack in this order:",
            "1. Official APIs and broker/provider truth when they answer the question.",
            "2. Hosted web search through the configured Codex-compatible search path.",
            "3. Self-hosted metasearch or search/scrape fallback, preferably through SearXNG, only when the first two layers are insufficient.",
            "4. Feed-first collection through official RSS/Atom feeds or RSSHub before opening a browser.",
            "5. Playwright browser fallback only when previous layers fail or anti-bot friction blocks retrieval.",
            "Do not use browser-style acquisition as the default path.",
            f"Current acquisition posture: {summary.status}; primary mode: {summary.primary_mode}.",
        ]
        lines.extend(self._market_mode_guidance_lines(market_mode))
        if skill_guidance:
            lines.append(skill_guidance)
        return " ".join(lines)

    def _official_api_layer(self) -> AcquisitionLayerStatus:
        if self.settings.default_broker_adapter == "alpaca" or any(
            [
                self.settings.alpaca_api_key,
                self.settings.alpaca_paper_api_key,
                self.settings.alpaca_live_api_key,
            ]
        ):
            return AcquisitionLayerStatus(
                key="official_apis",
                label="Official APIs",
                status="ok",
                message="Broker and provider API paths are available for structured source-of-truth retrieval.",
            )
        return AcquisitionLayerStatus(
            key="official_apis",
            label="Official APIs",
            status="warn",
            message="No explicit official provider API is configured yet, so research will lean more heavily on search-based acquisition.",
        )

    def _hosted_search_layer(self) -> AcquisitionLayerStatus:
        if self.settings.openai_api_key:
            return AcquisitionLayerStatus(
                key="hosted_web_search",
                label="Hosted Web Search",
                status="ok",
                message="Codex-compatible hosted web search is available for continuous research intake.",
            )
        return AcquisitionLayerStatus(
            key="hosted_web_search",
            label="Hosted Web Search",
            status="warn",
            message="No Codex-compatible API key is configured, so the primary hosted web-search layer is unavailable.",
        )

    def _search_scrape_layer(self, *, probe_endpoints: bool) -> AcquisitionLayerStatus:
        base_url = self._search_scrape_base_url()
        if base_url:
            probe = self._probe_endpoint(base_url, probe_endpoints=probe_endpoints)
            return AcquisitionLayerStatus(
                key="search_scrape",
                label="Search And Scrape",
                status=probe.status,
                message=(
                    "A self-hosted search/scrape fallback is configured for anti-bot, metasearch, or deep-fetch recovery."
                    if probe.status == "ok"
                    else f"Search/scrape fallback is configured, but readiness probe is degraded: {probe.message}"
                ),
                details=probe.details,
            )
        return AcquisitionLayerStatus(
            key="search_scrape",
            label="Search And Scrape",
            status="warn",
            message="No self-hosted search/scrape endpoint is configured; SearXNG-style metasearch remains unavailable on this runtime.",
            details={"configured": False},
        )

    def _feed_router_layer(self, *, probe_endpoints: bool) -> AcquisitionLayerStatus:
        if self.settings.rsshub_base_url:
            probe = self._probe_endpoint(self.settings.rsshub_base_url, probe_endpoints=probe_endpoints)
            return AcquisitionLayerStatus(
                key="feed_router",
                label="Feed Router",
                status=probe.status,
                message=(
                    "RSSHub-style feed routing is configured for low-cost social, blog, and announcement monitoring."
                    if probe.status == "ok"
                    else f"RSSHub-style feed routing is configured, but readiness probe is degraded: {probe.message}"
                ),
                details=probe.details,
            )
        return AcquisitionLayerStatus(
            key="feed_router",
            label="Feed Router",
            status="warn",
            message="No RSSHub endpoint is configured, so the system must rely on direct feeds and search alone.",
            details={"configured": False},
        )

    def _skill_pack_layer(self) -> AcquisitionLayerStatus:
        required = self.skill_catalog.required_acquisition_skill_ids(
            include_playwright=self._playwright_enabled()
        )
        missing = [skill_id for skill_id in required if self.skill_catalog.find(skill_id) is None]
        if not missing:
            return AcquisitionLayerStatus(
                key="skill_pack",
                label="Acquisition Skill Pack",
                status="ok",
                message="The repo-local acquisition skill pack is present for search/feed and browser-assisted research.",
                details={"missing_skill_ids": []},
            )
        return AcquisitionLayerStatus(
            key="skill_pack",
            label="Acquisition Skill Pack",
            status="warn",
            message="The repo-local acquisition skill pack is incomplete, so research will lean more heavily on ad-hoc prompting.",
            details={"missing_skill_ids": missing},
        )

    def _browser_fallback_layer(self, *, probe_endpoints: bool) -> AcquisitionLayerStatus:
        if not self._playwright_enabled():
            return AcquisitionLayerStatus(
                key="browser_fallback",
                label="Playwright Browser Fallback",
                status="ok",
                message="Playwright browser fallback is intentionally disabled by default; browser acquisition remains an exception path.",
                details={"enabled": False},
            )
        if self._playwright_endpoint():
            probe = self._probe_endpoint(self._playwright_endpoint(), probe_endpoints=probe_endpoints)
            return AcquisitionLayerStatus(
                key="browser_fallback",
                label="Playwright Browser Fallback",
                status=probe.status,
                message=(
                    "A Playwright browser endpoint is configured for last-resort acquisition against dynamic or anti-bot pages."
                    if probe.status == "ok"
                    else f"Playwright browser fallback is enabled, but readiness probe is degraded: {probe.message}"
                ),
                details=probe.details,
            )
        return AcquisitionLayerStatus(
            key="browser_fallback",
            label="Playwright Browser Fallback",
            status="warn",
            message="Playwright browser fallback is enabled but no endpoint is configured yet.",
            details={"enabled": True, "configured": False},
        )

    def _search_scrape_base_url(self) -> str | None:
        return self.settings.searxng_base_url or self.settings.web_fetch_base_url

    def _playwright_enabled(self) -> bool:
        if self.settings.playwright_browser_enabled is not None:
            return bool(self.settings.playwright_browser_enabled)
        return bool(self.settings.browser_fallback_enabled)

    def _playwright_endpoint(self) -> str | None:
        return self.settings.playwright_browser_endpoint or self.settings.browser_fallback_endpoint

    def _active_sleeves_for_market_mode(self, market_mode: str) -> list[str]:
        if market_mode == "cn":
            return ["cn_equities"]
        if market_mode == "us":
            return ["us_equities", "us_options"]
        return []

    def _market_mode_guidance_lines(self, market_mode: str) -> list[str]:
        if market_mode == "cn":
            return [
                "In cn mode, prioritize SSE, SZSE, CSRC, company filings, and AKShare-style structured collectors before generic web search.",
                "Treat Tushare or other local structured feeds as optional secondary sources, not the only truth source.",
                "Respect A-share microstructure such as the midday break, daily price-limit regimes, and T+1 cash-equity exit constraints when turning research into execution ideas.",
                "Do not propose US options, Alpaca-only workflows, or other US broker-dependent paths for a cn deployment.",
            ]
        if market_mode == "us":
            return [
                "In us mode, prioritize broker truth, SEC filings, exchange notices, earnings releases, and option-chain-aware sources when the question touches options, shorting, or leverage.",
                "Treat social or narrative chatter as weak evidence unless it is confirmed by primary filings, broker state, or exchange data.",
            ]
        return [
            "If the deployment market mode is unclear, keep recommendations conservative and avoid market-specific live execution assumptions.",
        ]

    def _probe_endpoint(self, endpoint: str, *, probe_endpoints: bool) -> AcquisitionLayerStatus:
        if not probe_endpoints:
            return AcquisitionLayerStatus(
                key="probe",
                label="Probe",
                status="ok",
                message="Probe skipped for summary-only mode.",
                details={"configured": True, "probed": False, "endpoint": endpoint},
            )

        parsed = urlparse(endpoint)
        start = time.perf_counter()
        try:
            if parsed.scheme in {"http", "https"}:
                request = Request(endpoint, headers={"User-Agent": "quant-evo-acquisition-doctor/1.0"})
                with urlopen(request, timeout=self.endpoint_probe_timeout_seconds) as response:
                    status_code = getattr(response, "status", None) or response.getcode()
                elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
                return AcquisitionLayerStatus(
                    key="probe",
                    label="Probe",
                    status="ok" if int(status_code) < 500 else "warn",
                    message=f"HTTP probe returned {status_code} in {elapsed_ms} ms.",
                    details={
                        "configured": True,
                        "probed": True,
                        "endpoint": endpoint,
                        "status_code": int(status_code),
                        "latency_ms": elapsed_ms,
                    },
                )
            if parsed.scheme in {"ws", "wss"}:
                host = parsed.hostname or ""
                port = parsed.port or (443 if parsed.scheme == "wss" else 80)
                with socket.create_connection((host, port), timeout=self.endpoint_probe_timeout_seconds):
                    pass
                elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
                return AcquisitionLayerStatus(
                    key="probe",
                    label="Probe",
                    status="ok",
                    message=f"Socket probe reached {host}:{port} in {elapsed_ms} ms.",
                    details={
                        "configured": True,
                        "probed": True,
                        "endpoint": endpoint,
                        "host": host,
                        "port": port,
                        "latency_ms": elapsed_ms,
                    },
                )
        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
            return AcquisitionLayerStatus(
                key="probe",
                label="Probe",
                status="warn",
                message=f"Probe failed after {elapsed_ms} ms: {exc}",
                details={
                    "configured": True,
                    "probed": True,
                    "endpoint": endpoint,
                    "latency_ms": elapsed_ms,
                    "error": str(exc),
                },
            )

        return AcquisitionLayerStatus(
            key="probe",
            label="Probe",
            status="warn",
            message=f"Unsupported acquisition endpoint scheme: {parsed.scheme or 'unknown'}",
            details={
                "configured": True,
                "probed": True,
                "endpoint": endpoint,
                "scheme": parsed.scheme or None,
            },
        )
