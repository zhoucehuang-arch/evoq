from __future__ import annotations

from dataclasses import dataclass

from quant_evo_nextgen.config import Settings


@dataclass(slots=True)
class AcquisitionLayerStatus:
    key: str
    label: str
    status: str
    message: str


@dataclass(slots=True)
class AcquisitionStackSummary:
    status: str
    primary_mode: str
    layers: list[AcquisitionLayerStatus]


class AcquisitionStackService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build_summary(self) -> AcquisitionStackSummary:
        layers = [
            self._official_api_layer(),
            self._hosted_search_layer(),
            self._search_scrape_layer(),
            self._browser_fallback_layer(),
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
        if layers[0].status == "ok":
            primary_mode = "official_apis_plus_hosted_search"
        return AcquisitionStackSummary(status=overall, primary_mode=primary_mode, layers=layers)

    def prompt_guidance(self) -> str:
        summary = self.build_summary()
        lines = [
            "Use the governed layered acquisition stack in this order:",
            "1. Official APIs and broker/provider truth when they answer the question.",
            "2. Hosted web search through the configured Codex-compatible search path.",
            "3. Optional search/scrape service only when the first two layers are insufficient.",
            "4. Browser fallback only when previous layers fail or anti-bot friction blocks retrieval.",
            "Do not use browser-style acquisition as the default path.",
            f"Current acquisition posture: {summary.status}; primary mode: {summary.primary_mode}.",
        ]
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

    def _search_scrape_layer(self) -> AcquisitionLayerStatus:
        if self.settings.web_fetch_base_url:
            return AcquisitionLayerStatus(
                key="search_scrape",
                label="Search And Scrape",
                status="ok",
                message="An auxiliary search/scrape service is configured for anti-bot or deep-fetch fallback.",
            )
        return AcquisitionLayerStatus(
            key="search_scrape",
            label="Search And Scrape",
            status="warn",
            message="No auxiliary search/scrape service is configured; the stack will rely on hosted search until one is needed.",
        )

    def _browser_fallback_layer(self) -> AcquisitionLayerStatus:
        if not self.settings.browser_fallback_enabled:
            return AcquisitionLayerStatus(
                key="browser_fallback",
                label="Browser Fallback",
                status="ok",
                message="Browser fallback is intentionally disabled by default; GUI/browser acquisition remains an emergency-only path.",
            )
        if self.settings.browser_fallback_endpoint:
            return AcquisitionLayerStatus(
                key="browser_fallback",
                label="Browser Fallback",
                status="ok",
                message="A browser fallback endpoint is configured for last-resort acquisition.",
            )
        return AcquisitionLayerStatus(
            key="browser_fallback",
            label="Browser Fallback",
            status="warn",
            message="Browser fallback is enabled but no endpoint is configured yet.",
        )
