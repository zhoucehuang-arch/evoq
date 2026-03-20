from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from quant_evo_nextgen.services.codex_fabric import CodexFabricService
from quant_evo_nextgen.services.evolution import EvolutionService
from quant_evo_nextgen.services.execution import ExecutionService
from quant_evo_nextgen.services.learning import LearningService
from quant_evo_nextgen.services.state_store import StateStore
from quant_evo_nextgen.services.strategy_lab import StrategyLabService


@dataclass(slots=True)
class CapabilityGap:
    gap_key: str
    label: str
    severity: str
    summary: str
    recommended_action: str


@dataclass(slots=True)
class CapabilityScorecard:
    capability_key: str
    label: str
    score_pct: int
    status: str
    evidence_count: int
    summary: str
    gaps: list[str]


@dataclass(slots=True)
class CapabilityReviewSummary:
    overall_score_pct: int
    status: str
    scorecards: list[CapabilityScorecard]
    capability_gaps: list[CapabilityGap]
    stall_state: str
    stall_summary: str | None
    should_queue_replan: bool


class EvolutionCapabilityService:
    def __init__(
        self,
        *,
        state_store: StateStore,
        learning_service: LearningService | None = None,
        strategy_service: StrategyLabService | None = None,
        execution_service: ExecutionService | None = None,
        evolution_service: EvolutionService | None = None,
        codex_fabric_service: CodexFabricService | None = None,
    ) -> None:
        self.state_store = state_store
        self.learning_service = learning_service
        self.strategy_service = strategy_service
        self.execution_service = execution_service
        self.evolution_service = evolution_service
        self.codex_fabric_service = codex_fabric_service

    def build_review(self, *, now: datetime | None = None) -> CapabilityReviewSummary:
        current_time = now or datetime.now(tz=UTC)
        sources = self.state_store.list_source_health()
        loops = self.state_store.list_supervisor_loops()
        incidents = self.state_store.list_incidents(open_only=True, limit=50)
        runtime = self.state_store.get_runtime_snapshot()
        learning_metrics = self.learning_service.get_learning_metrics() if self.learning_service is not None else None
        strategy_metrics = self.strategy_service.get_metrics() if self.strategy_service is not None else None
        evolution_metrics = self.evolution_service.get_metrics() if self.evolution_service is not None else None
        execution_readiness = (
            self.execution_service.get_execution_readiness() if self.execution_service is not None else None
        )
        proposals = self.evolution_service.list_improvement_proposals(limit=20) if self.evolution_service else []
        decisions = self.evolution_service.list_promotion_decisions(limit=20) if self.evolution_service else []
        codex_runs = self.codex_fabric_service.list_runs(limit=25) if self.codex_fabric_service else []

        loop_map = {loop.loop_key: loop for loop in loops}
        scorecards = [
            self._research_continuity_scorecard(
                sources=sources,
                learning_metrics=learning_metrics,
                loop_map=loop_map,
                codex_runs=codex_runs,
                now=current_time,
            ),
            self._learning_quality_scorecard(
                sources=sources,
                learning_metrics=learning_metrics,
                loop_map=loop_map,
            ),
            self._strategy_discipline_scorecard(
                strategy_metrics=strategy_metrics,
                execution_readiness=execution_readiness,
                loop_map=loop_map,
            ),
            self._governed_evolution_scorecard(
                evolution_metrics=evolution_metrics,
                loop_map=loop_map,
                proposals=proposals,
                decisions=decisions,
                codex_runs=codex_runs,
                now=current_time,
            ),
            self._capital_guardrail_scorecard(
                execution_readiness=execution_readiness,
                incidents=incidents,
            ),
        ]

        capability_gaps: list[CapabilityGap] = []
        for scorecard in scorecards:
            for index, gap in enumerate(scorecard.gaps, start=1):
                capability_gaps.append(
                    CapabilityGap(
                        gap_key=f"{scorecard.capability_key}-{index}",
                        label=scorecard.label,
                        severity="critical" if scorecard.status == "fail" else "warn",
                        summary=gap,
                        recommended_action=self._recommended_action_for_scorecard(scorecard.capability_key),
                    )
                )

        stall_state, stall_summary = self._stall_assessment(
            proposals=proposals,
            decisions=decisions,
            codex_runs=codex_runs,
            loop_map=loop_map,
            now=current_time,
        )
        if stall_summary:
            capability_gaps.insert(
                0,
                CapabilityGap(
                    gap_key="evolution-stall",
                    label="Evolution anti-stall",
                    severity="critical" if stall_state == "critical" else "warn",
                    summary=stall_summary,
                    recommended_action=(
                        "Queue a bounded Ralph-style replanning run, open a recovery goal, and review the top blocked capability gaps."
                    ),
                ),
            )

        overall_score = round(sum(card.score_pct for card in scorecards) / max(1, len(scorecards)))
        overall_status = "ok"
        if any(card.status == "fail" for card in scorecards):
            overall_status = "fail"
        elif any(card.status == "warn" for card in scorecards):
            overall_status = "warn"

        return CapabilityReviewSummary(
            overall_score_pct=int(overall_score),
            status=overall_status,
            scorecards=scorecards,
            capability_gaps=capability_gaps[:10],
            stall_state=stall_state,
            stall_summary=stall_summary,
            should_queue_replan=stall_state in {"warning", "critical"},
        )

    def _research_continuity_scorecard(
        self,
        *,
        sources,
        learning_metrics,
        loop_map,
        codex_runs,
        now: datetime,
    ) -> CapabilityScorecard:
        gaps: list[str] = []
        score = 0
        total_sources = len(sources)
        healthy_sources = sum(1 for source in sources if source.health_status in {"healthy", "unknown"})
        healthy_ratio = (healthy_sources / total_sources) if total_sources else 0.0
        if total_sources:
            score += round(healthy_ratio * 35)
            if healthy_sources < total_sources:
                gaps.append("Some research sources are degraded or stale, so online learning coverage is uneven.")
        else:
            gaps.append("No source-health records exist yet, so continuous learning sources are still unverified.")

        if learning_metrics is not None and learning_metrics.document_count > 0:
            score += 20
        else:
            gaps.append("No research documents have been ingested into durable learning state yet.")

        research_loop = loop_map.get("research-intake")
        distillation_loop = loop_map.get("research-distillation")
        if research_loop and research_loop.is_enabled and research_loop.execution_mode == "active":
            score += 20
        else:
            gaps.append("The research-intake supervisor loop is not active.")

        if distillation_loop and distillation_loop.is_enabled and distillation_loop.execution_mode == "active":
            score += 10
        else:
            gaps.append("The research-distillation loop is not active, so intake may not become durable evidence quickly.")

        recent_completed = sum(
            1
            for run in codex_runs
            if run.supervisor_loop_key == "research-intake"
            and run.status == "completed"
            and run.completed_at is not None
            and self._coerce_utc(run.completed_at) >= now - timedelta(hours=24)
        )
        if recent_completed > 0:
            score += 15
        else:
            gaps.append("No completed research-intake Codex run was recorded in the last 24 hours.")

        return self._scorecard(
            capability_key="research_continuity",
            label="Research continuity",
            score=score,
            evidence_count=(learning_metrics.document_count if learning_metrics is not None else 0) + healthy_sources,
            gaps=gaps,
            success_summary="Continuous online research intake, source health, and durable evidence flow look active.",
            fallback_summary="Continuous research is present, but one or more intake or source-health gaps remain.",
        )

    def _learning_quality_scorecard(
        self,
        *,
        sources,
        learning_metrics,
        loop_map,
    ) -> CapabilityScorecard:
        gaps: list[str] = []
        score = 0
        degraded_sources = sum(1 for source in sources if source.health_status in {"degraded", "stale", "broken"})
        synthesis_loop = loop_map.get("learning-synthesis")
        if synthesis_loop and synthesis_loop.is_enabled and synthesis_loop.execution_mode == "active":
            score += 20
        else:
            gaps.append("The learning-synthesis loop is not active.")

        if learning_metrics is None:
            gaps.append("Learning metrics are unavailable on this node.")
            return self._scorecard(
                capability_key="learning_quality",
                label="Learning quality",
                score=score,
                evidence_count=0,
                gaps=gaps,
                success_summary="Learning quarantine and synthesis quality are healthy.",
                fallback_summary="Learning quality signals are incomplete or degraded.",
            )

        if learning_metrics.insight_count > 0:
            score += 20
        else:
            gaps.append("No durable insights have been synthesized yet.")

        ready_ratio = (
            learning_metrics.ready_insight_count / learning_metrics.insight_count
            if learning_metrics.insight_count
            else 0.0
        )
        score += round(min(25.0, ready_ratio * 25.0))
        if learning_metrics.quarantined_insight_count > max(2, learning_metrics.ready_insight_count):
            gaps.append("Quarantined insights are outpacing ready insights, which suggests the learning pipeline is noisy.")
        else:
            score += 15

        if degraded_sources == 0:
            score += 20
        else:
            gaps.append("One or more degraded sources are still feeding the learning boundary.")

        return self._scorecard(
            capability_key="learning_quality",
            label="Learning quality",
            score=score,
            evidence_count=learning_metrics.insight_count,
            gaps=gaps,
            success_summary="Learning synthesis is producing reviewable insights without excessive quarantine pressure.",
            fallback_summary="Learning synthesis is working, but the quarantine ratio or source quality still needs attention.",
        )

    def _strategy_discipline_scorecard(
        self,
        *,
        strategy_metrics,
        execution_readiness,
        loop_map,
    ) -> CapabilityScorecard:
        gaps: list[str] = []
        score = 0
        strategy_loop = loop_map.get("strategy-evaluation")
        if strategy_loop and strategy_loop.is_enabled and strategy_loop.execution_mode == "active":
            score += 20
        else:
            gaps.append("The strategy-evaluation loop is not active.")

        if strategy_metrics is None:
            gaps.append("Strategy metrics are unavailable on this node.")
            return self._scorecard(
                capability_key="strategy_discipline",
                label="Strategy discipline",
                score=score,
                evidence_count=0,
                gaps=gaps,
                success_summary="Strategy research, paper validation, and governed promotion look healthy.",
                fallback_summary="Strategy discipline is present, but the paper-to-production path is still thin.",
            )

        if strategy_metrics.spec_count > 0:
            score += 20
        else:
            gaps.append("No durable strategy specs exist yet.")

        if strategy_metrics.paper_candidate_count + strategy_metrics.paper_running_count > 0:
            score += 20
        else:
            gaps.append("No strategy is currently in a paper-validation lane.")

        if strategy_metrics.production_count > 0:
            score += 20
        else:
            gaps.append("No governed production strategy is active yet.")

        if execution_readiness is not None and execution_readiness.status in {"ready", "degraded"}:
            score += 20 if execution_readiness.status == "ready" else 10
            if execution_readiness.status == "degraded":
                gaps.append("Execution readiness is degraded, so strategy promotion quality cannot be treated as fully healthy.")
        elif execution_readiness is not None:
            gaps.append("Execution readiness is blocked, so strategy validation cannot advance safely.")

        return self._scorecard(
            capability_key="strategy_discipline",
            label="Strategy discipline",
            score=score,
            evidence_count=(
                strategy_metrics.spec_count
                + strategy_metrics.paper_candidate_count
                + strategy_metrics.paper_running_count
                + strategy_metrics.production_count
            ),
            gaps=gaps,
            success_summary="The strategy pipeline has durable specs, validation lanes, and governed readiness signals.",
            fallback_summary="The strategy pipeline exists, but paper/live readiness is still uneven.",
        )

    def _governed_evolution_scorecard(
        self,
        *,
        evolution_metrics,
        loop_map,
        proposals,
        decisions,
        codex_runs,
        now: datetime,
    ) -> CapabilityScorecard:
        gaps: list[str] = []
        score = 0
        sync_loop = loop_map.get("evolution-governance-sync")
        council_loop = loop_map.get("council-reflection")
        capability_loop = loop_map.get("capability-review")
        if sync_loop and sync_loop.is_enabled and sync_loop.execution_mode == "active":
            score += 25
        else:
            gaps.append("The evolution-governance-sync loop is not active.")

        if council_loop and council_loop.is_enabled:
            score += 10
        else:
            gaps.append("Council reflection is still disabled, so multi-perspective replanning is thinner than intended.")

        if capability_loop and capability_loop.is_enabled and capability_loop.execution_mode == "active":
            score += 10
        else:
            gaps.append("Capability review is not active, so anti-stall replanning is not continuously watched.")

        recent_completed = sum(
            1
            for run in codex_runs
            if run.supervisor_loop_key in {"strategy-evaluation", "council-reflection", "capability-review"}
            and run.status == "completed"
            and run.completed_at is not None
            and self._coerce_utc(run.completed_at) >= now - timedelta(hours=72)
        )
        if recent_completed:
            score += 10
        else:
            gaps.append("No completed reflection or strategy-evaluation Codex run was recorded in the last 72 hours.")

        if evolution_metrics is None:
            gaps.append("Evolution governance metrics are unavailable on this node.")
            return self._scorecard(
                capability_key="governed_evolution",
                label="Governed evolution",
                score=score,
                evidence_count=0,
                gaps=gaps,
                success_summary="Evolution proposals, canaries, and promotion decisions are flowing with governance.",
                fallback_summary="Evolution governance exists, but proposal flow or automated review remains thin.",
            )

        if evolution_metrics.proposal_count > 0:
            score += 15
        else:
            gaps.append("No evolution proposal has been recorded yet.")

        if evolution_metrics.promoted_count + evolution_metrics.active_canary_count > 0:
            score += 15
        else:
            gaps.append("No active canary lane or promoted improvement has been observed yet.")

        blocked_recent = sum(
            1 for proposal in proposals if proposal.proposal_state in {"blocked", "rolled_back"}
        )
        if blocked_recent >= 2 and not decisions:
            gaps.append("Recent evolution proposals are stalling in blocked or rolled-back states without enough recovery activity.")

        return self._scorecard(
            capability_key="governed_evolution",
            label="Governed evolution",
            score=score,
            evidence_count=evolution_metrics.proposal_count + len(decisions),
            gaps=gaps,
            success_summary="Evolution proposals are moving through governed canary and promotion stages.",
            fallback_summary="Governed evolution exists, but proposal flow or anti-stall coverage is still incomplete.",
        )

    def _capital_guardrail_scorecard(
        self,
        *,
        execution_readiness,
        incidents,
    ) -> CapabilityScorecard:
        gaps: list[str] = []
        score = 0
        if execution_readiness is None:
            gaps.append("Execution readiness is unavailable on this node.")
            return self._scorecard(
                capability_key="capital_guardrails",
                label="Capital guardrails",
                score=score,
                evidence_count=0,
                gaps=gaps,
                success_summary="Capital-facing guardrails, broker health, and execution readiness look healthy.",
                fallback_summary="Capital-facing guardrails exist, but readiness or incident posture is still degraded.",
            )

        if execution_readiness.status == "ready":
            score += 55
        elif execution_readiness.status == "degraded":
            score += 35
            gaps.extend(execution_readiness.warnings[:2])
        else:
            gaps.extend(execution_readiness.blocked_reasons[:3] or ["Execution readiness is blocked."])

        if not incidents:
            score += 25
        else:
            gaps.append("Open incidents are active, so unattended capital-facing confidence must stay constrained.")

        if execution_readiness.latest_provider_health in {None, "healthy", "unknown"}:
            score += 20
        else:
            gaps.append("Provider or broker health is degraded.")

        return self._scorecard(
            capability_key="capital_guardrails",
            label="Capital guardrails",
            score=score,
            evidence_count=execution_readiness.active_production_strategies,
            gaps=gaps,
            success_summary="Capital-facing automation has usable broker and execution guardrails.",
            fallback_summary="Capital-facing automation is bounded, but readiness or incident pressure is still limiting it.",
        )

    def _stall_assessment(
        self,
        *,
        proposals,
        decisions,
        codex_runs,
        loop_map,
        now: datetime,
    ) -> tuple[str, str | None]:
        recent_reflection_runs = [
            run
            for run in codex_runs
            if run.supervisor_loop_key in {"strategy-evaluation", "council-reflection", "capability-review"}
            and run.status == "completed"
            and run.completed_at is not None
            and self._coerce_utc(run.completed_at) >= now - timedelta(hours=72)
        ]
        recent_proposals = [
            proposal
            for proposal in proposals
            if self._coerce_utc(proposal.created_at) >= now - timedelta(hours=72)
        ]
        stale_ready = [
            proposal
            for proposal in proposals
            if proposal.proposal_state in {"candidate", "ready_for_review", "shadow_passed", "canary_passed"}
            and self._coerce_utc(proposal.created_at) <= now - timedelta(hours=48)
        ]
        recent_recovery_decisions = [
            decision
            for decision in decisions
            if self._coerce_utc(decision.decided_at) >= now - timedelta(hours=72)
            and decision.decision in {"shadow_approved", "canary_approved", "promoted"}
        ]
        recent_blocked = [
            proposal
            for proposal in proposals
            if proposal.proposal_state in {"blocked", "rolled_back"}
            and self._coerce_utc(proposal.created_at) >= now - timedelta(hours=72)
        ]
        council_loop = loop_map.get("council-reflection")

        if len(recent_blocked) >= 2 and not recent_recovery_decisions:
            return (
                "critical",
                "Recent evolution proposals are repeatedly blocking or rolling back without any successful recovery decision.",
            )
        if stale_ready:
            return (
                "warning",
                "At least one evolution proposal has been waiting more than 48 hours without being advanced or formally rejected.",
            )
        if len(recent_reflection_runs) >= 3 and not recent_proposals:
            return (
                "warning",
                "Multiple bounded reflection runs completed in the last 72 hours, but none produced a durable evolution proposal.",
            )
        if len(recent_reflection_runs) >= 2 and (council_loop is None or not council_loop.is_enabled):
            return (
                "warning",
                "Reflection work is happening, but council reflection is disabled, so the system is under-using multi-expert replanning.",
            )
        return ("healthy", None)

    def _scorecard(
        self,
        *,
        capability_key: str,
        label: str,
        score: int,
        evidence_count: int,
        gaps: list[str],
        success_summary: str,
        fallback_summary: str,
    ) -> CapabilityScorecard:
        bounded_score = max(0, min(100, int(score)))
        status = "ok" if bounded_score >= 75 else "warn" if bounded_score >= 50 else "fail"
        summary = success_summary if not gaps and status == "ok" else fallback_summary
        return CapabilityScorecard(
            capability_key=capability_key,
            label=label,
            score_pct=bounded_score,
            status=status,
            evidence_count=max(0, int(evidence_count)),
            summary=summary,
            gaps=gaps,
        )

    def _recommended_action_for_scorecard(self, capability_key: str) -> str:
        return {
            "research_continuity": "Restore source health, keep research-intake active, and verify new external evidence is being ingested.",
            "learning_quality": "Reduce noisy inputs, review quarantined insights, and strengthen synthesis before promoting memory.",
            "strategy_discipline": "Push at least one governed strategy through paper validation before treating the pipeline as healthy.",
            "governed_evolution": "Advance or reject stale proposals, keep governance sync active, and use bounded council reflection for replanning.",
            "capital_guardrails": "Resolve blocked execution reasons, broker incidents, or readiness warnings before increasing autonomy.",
        }.get(capability_key, "Review the affected subsystem and open a bounded recovery plan.")

    def _coerce_utc(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
