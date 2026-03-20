from quant_evo_nextgen.config import Settings
from quant_evo_nextgen.services.acquisition import AcquisitionStackService


def test_acquisition_stack_reports_ok_with_hosted_search_and_browser_disabled() -> None:
    settings = Settings(
        openai_api_key="relay-key",
        openai_base_url="https://relay.example.com/v1",
        browser_fallback_enabled=False,
    )
    summary = AcquisitionStackService(settings).build_summary()

    assert summary.status == "warn"
    assert summary.primary_mode == "hosted_web_search"
    assert any(layer.key == "hosted_web_search" and layer.status == "ok" for layer in summary.layers)
    assert any(layer.key == "browser_fallback" and layer.status == "ok" for layer in summary.layers)


def test_acquisition_stack_warns_without_hosted_search() -> None:
    settings = Settings()
    summary = AcquisitionStackService(settings).build_summary()

    assert summary.status == "warn"
    assert any(layer.key == "hosted_web_search" and layer.status == "warn" for layer in summary.layers)


def test_acquisition_stack_reports_ok_with_local_fallbacks_and_skill_pack(tmp_path) -> None:
    skill_root = tmp_path / "skills"
    (skill_root / "search-rss-intake").mkdir(parents=True)
    (skill_root / "search-rss-intake" / "SKILL.md").write_text("# Search And RSS Intake\n", encoding="utf-8")
    (skill_root / "playwright-browser-intake").mkdir(parents=True)
    (skill_root / "playwright-browser-intake" / "SKILL.md").write_text(
        "# Playwright Browser Intake\n",
        encoding="utf-8",
    )

    settings = Settings(
        repo_root=tmp_path,
        openai_api_key="relay-key",
        alpaca_paper_api_key="paper-key",
        searxng_base_url="http://searxng:8080",
        rsshub_base_url="http://rsshub:1200",
        playwright_browser_enabled=True,
        playwright_browser_endpoint="ws://playwright:3001/browser",
    )
    summary = AcquisitionStackService(settings).build_summary()
    guidance = AcquisitionStackService(settings).prompt_guidance()

    assert summary.status == "ok"
    assert summary.primary_mode == "official_apis_plus_hosted_web_search_plus_local_fallbacks"
    assert any(layer.key == "skill_pack" and layer.status == "ok" for layer in summary.layers)
    assert any(layer.key == "feed_router" and layer.status == "ok" for layer in summary.layers)
    assert "playwright-browser-intake" in guidance


def test_acquisition_stack_surfaces_probe_failure_for_configured_http_fallback(monkeypatch) -> None:
    settings = Settings(
        openai_api_key="relay-key",
        searxng_base_url="http://searxng:8080",
    )

    def _raise_probe(*args, **kwargs):
        raise OSError("probe down")

    monkeypatch.setattr("quant_evo_nextgen.services.acquisition.urlopen", _raise_probe)
    summary = AcquisitionStackService(settings).build_summary(probe_endpoints=True)
    layer = next(layer for layer in summary.layers if layer.key == "search_scrape")

    assert summary.status == "warn"
    assert layer.status == "warn"
    assert "probe is degraded" in layer.message
    assert layer.details is not None
    assert layer.details["probed"] is True


def test_acquisition_stack_surfaces_probe_success_for_playwright_socket(monkeypatch) -> None:
    settings = Settings(
        openai_api_key="relay-key",
        playwright_browser_enabled=True,
        playwright_browser_endpoint="ws://playwright:3001/browser",
    )

    class _DummySocket:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(
        "quant_evo_nextgen.services.acquisition.socket.create_connection",
        lambda *args, **kwargs: _DummySocket(),
    )
    summary = AcquisitionStackService(settings).build_summary(probe_endpoints=True)
    layer = next(layer for layer in summary.layers if layer.key == "browser_fallback")

    assert layer.status == "ok"
    assert layer.details is not None
    assert layer.details["probed"] is True
