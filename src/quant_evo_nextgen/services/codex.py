from __future__ import annotations

from pathlib import Path

from quant_evo_nextgen.config import Settings
from quant_evo_nextgen.contracts.codex import CodexRunRequest


def build_exec_command(
    request: CodexRunRequest,
    settings: Settings,
    *,
    output_last_message_path: Path | None = None,
    prompt_override: str | None = None,
) -> list[str]:
    prompt = prompt_override or _render_prompt(request)
    command = [
        settings.codex_command,
        "exec",
        "--json",
        "-C",
        str(request.workspace_path),
        "--skip-git-repo-check",
    ]

    model = request.model or settings.codex_default_model
    if model:
        command.extend(["-m", model])

    if request.output_schema_path:
        command.extend(["--output-schema", str(request.output_schema_path)])

    if output_last_message_path is not None:
        command.extend(["--output-last-message", str(output_last_message_path)])

    if request.search_enabled:
        command.append("--search")

    if settings.openai_base_url:
        command.extend(["-c", f"openai_base_url={settings.openai_base_url}"])

    command.append(prompt)
    return command


def _render_prompt(request: CodexRunRequest) -> str:
    sections = [
        f"Objective: {request.objective}",
        f"Context: {request.context_summary}",
        f"Risk tier: {request.risk_tier}",
        f"Write scope: {', '.join(request.write_scope) if request.write_scope else 'read-only'}",
        f"Execution mode: {request.execution_mode}",
        f"Max iterations: {request.max_iterations}",
    ]

    if request.allowed_tools:
        sections.append(f"Allowed tools: {', '.join(request.allowed_tools)}")

    if request.related_artifacts:
        sections.append(f"Related artifacts: {', '.join(request.related_artifacts)}")

    if request.memory_refs:
        sections.append(f"Memory refs: {', '.join(request.memory_refs)}")

    if request.citation_requirements:
        sections.append("Citation requirements:")
        sections.extend(f"- {item}" for item in request.citation_requirements)

    if request.acceptance_criteria:
        sections.append("Acceptance criteria:")
        sections.extend(f"- {criterion}" for criterion in request.acceptance_criteria)

    if request.prompt_appendix:
        sections.append(request.prompt_appendix)

    return "\n".join(sections)


def ensure_paths_exist(request: CodexRunRequest) -> None:
    for path in (request.repo_path, request.workspace_path):
        if not Path(path).exists():
            raise FileNotFoundError(f"Codex path does not exist: {path}")


def build_exec_environment(settings: Settings) -> dict[str, str]:
    env: dict[str, str] = {}
    if settings.openai_api_key:
        env["CODEX_API_KEY"] = settings.openai_api_key
        env["OPENAI_API_KEY"] = settings.openai_api_key
    if settings.openai_base_url:
        env["OPENAI_BASE_URL"] = settings.openai_base_url
    return env
