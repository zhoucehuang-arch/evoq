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
