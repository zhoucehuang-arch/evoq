from pathlib import Path

from quant_evo_nextgen.config import Settings
from quant_evo_nextgen.contracts.codex import CodexRunRequest
from quant_evo_nextgen.services.codex import build_exec_command, build_exec_environment


def test_build_exec_command_includes_schema_and_search() -> None:
    request = CodexRunRequest(
        codex_run_id="run-1",
        goal_id="goal-1",
        task_id="task-1",
        worker_class="implementation_worker",
        objective="Implement the API endpoint.",
        context_summary="Use the repo contracts.",
        repo_path=Path("."),
        workspace_path=Path("."),
        write_scope=["src/"],
        allowed_tools=["shell", "web"],
        search_enabled=True,
        output_schema_path=Path("schema.json"),
        acceptance_criteria=["Endpoint returns 200"],
    )
    settings = Settings(repo_root=Path("."))

    command = build_exec_command(request, settings)

    assert command[:2] == ["codex", "exec"]
    assert "--json" in command
    assert "--search" in command
    assert "--output-schema" in command
    assert "Implement the API endpoint." in command[-1]


def test_build_exec_environment_uses_openai_compatible_relay_settings() -> None:
    settings = Settings(
        repo_root=Path("."),
        openai_api_key="relay-key",
        openai_base_url="https://relay.example.com/v1",
    )

    env = build_exec_environment(settings)

    assert env["CODEX_API_KEY"] == "relay-key"
    assert env["OPENAI_API_KEY"] == "relay-key"
    assert env["OPENAI_BASE_URL"] == "https://relay.example.com/v1"
