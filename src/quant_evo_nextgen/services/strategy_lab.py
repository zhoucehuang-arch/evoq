from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable, Sequence

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from quant_evo_nextgen.contracts.state import (
    BacktestRunCreate,
    BacktestRunSummary,
    FactorReplayBacktestCreate,
    PaperRunCreate,
    PaperRunSummary,
    PromotionDecisionCreate,
    PromotionDecisionSummary,
    StrategyHypothesisCreate,
    StrategyHypothesisSummary,
    StrategyResearchBriefCreate,
    StrategyResearchBriefPromotionCreate,
    StrategyResearchBriefSummary,
    StrategySpecCreate,
    StrategySpecSummary,
    WithdrawalDecisionCreate,
    WithdrawalDecisionSummary,
)
from quant_evo_nextgen.db.models import (
    BacktestRunModel,
    FactorSnapshotModel,
    HistoricalBarModel,
    HypothesisModel,
    InsightModel,
    PaperRunModel,
    PromotionDecisionModel,
    StrategyResearchBriefModel,
    StrategySpecModel,
    WithdrawalDecisionModel,
)
from quant_evo_nextgen.services.adversarial import run_adversarial_checks
from quant_evo_nextgen.services.cost_models import (
    CostModelConfig,
    aggregate_cost_pct,
    cost_model_payload,
    estimate_symbol_trade_cost,
)
from quant_evo_nextgen.services.statistical_validation import validate_backtest_statistics


@dataclass(slots=True)
class StrategyLabMetrics:
    hypothesis_count: int
    spec_count: int
    paper_candidate_count: int
    paper_running_count: int
    live_candidate_count: int
    production_count: int


class StrategyLabService:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self.session_factory = session_factory

    def create_research_brief(
        self,
        payload: StrategyResearchBriefCreate | dict[str, Any],
    ) -> StrategyResearchBriefSummary:
        request = StrategyResearchBriefCreate.model_validate(payload)
        audit_status, audit_notes, readiness_score = self._audit_research_brief(request)

        with self.session_factory() as session:
            if request.source_insight_id is not None and session.get(InsightModel, request.source_insight_id) is None:
                raise ValueError(f"Insight not found: {request.source_insight_id}")

            brief = StrategyResearchBriefModel(
                source_insight_id=request.source_insight_id,
                title=request.title,
                thesis=request.thesis,
                opportunity_kind=request.opportunity_kind,
                target_market=request.target_market,
                signal_definition=request.signal_definition,
                expected_mechanism=request.expected_mechanism,
                llm_provider=request.llm_provider,
                llm_model=request.llm_model,
                llm_model_cutoff=request.llm_model_cutoff,
                prompt_hash=request.prompt_hash,
                tool_refs=request.tool_refs,
                evidence_refs=request.evidence_refs,
                data_requirements=request.data_requirements,
                point_in_time_controls=request.point_in_time_controls,
                evaluation_plan=request.evaluation_plan,
                cost_model_requirements=request.cost_model_requirements,
                baseline_refs=request.baseline_refs,
                invalidation_conditions=request.invalidation_conditions,
                risk_controls_required=request.risk_controls_required,
                attack_tests_required=request.attack_tests_required,
                audit_status=audit_status,
                audit_notes=audit_notes,
                readiness_score=readiness_score,
                created_by=request.created_by,
                origin_type=request.origin_type,
                origin_id=request.origin_id,
                status=request.status,
            )
            session.add(brief)
            session.commit()
            session.refresh(brief)
            return self._research_brief_summary(brief)

    def list_research_briefs(
        self,
        *,
        limit: int = 20,
        audit_statuses: Sequence[str] | None = None,
    ) -> list[StrategyResearchBriefSummary]:
        with self.session_factory() as session:
            query = select(StrategyResearchBriefModel).order_by(StrategyResearchBriefModel.created_at.desc()).limit(
                limit
            )
            if audit_statuses:
                query = query.where(StrategyResearchBriefModel.audit_status.in_(list(audit_statuses)))
            briefs = session.scalars(query).all()
            return [self._research_brief_summary(brief) for brief in briefs]

    def promote_research_brief_to_hypothesis(
        self,
        brief_id: str,
        payload: StrategyResearchBriefPromotionCreate | dict[str, Any] | None = None,
    ) -> StrategyHypothesisSummary:
        request = StrategyResearchBriefPromotionCreate.model_validate(payload or {})
        with self.session_factory() as session:
            brief = session.get(StrategyResearchBriefModel, brief_id)
            if brief is None:
                raise ValueError(f"Research brief not found: {brief_id}")
            if brief.audit_status != "ready_for_spec":
                raise ValueError(f"Research brief is not ready for hypothesis promotion: {brief.audit_status}")
            if brief.promoted_hypothesis_id is not None:
                existing = session.get(HypothesisModel, brief.promoted_hypothesis_id)
                if existing is not None:
                    return self._hypothesis_summary(existing)

            hypothesis = HypothesisModel(
                source_insight_id=brief.source_insight_id,
                title=brief.title,
                thesis=brief.thesis,
                target_market=brief.target_market,
                mechanism=brief.expected_mechanism,
                risk_hypothesis="; ".join(brief.risk_controls_required),
                evaluation_plan=list(brief.evaluation_plan),
                invalidation_conditions=list(brief.invalidation_conditions),
                current_stage="hypothesis",
                created_by=request.created_by,
                origin_type="llm_research_brief",
                origin_id=brief.id,
                status=request.status,
            )
            session.add(hypothesis)
            session.flush()
            brief.promoted_hypothesis_id = hypothesis.id
            brief.status = "promoted"
            session.commit()
            session.refresh(hypothesis)
            return self._hypothesis_summary(hypothesis)

    def create_hypothesis(
        self,
        payload: StrategyHypothesisCreate | dict[str, Any],
    ) -> StrategyHypothesisSummary:
        request = StrategyHypothesisCreate.model_validate(payload)
        with self.session_factory() as session:
            if request.source_insight_id is not None and session.get(InsightModel, request.source_insight_id) is None:
                raise ValueError(f"Insight not found: {request.source_insight_id}")

            hypothesis = HypothesisModel(
                source_insight_id=request.source_insight_id,
                title=request.title,
                thesis=request.thesis,
                target_market=request.target_market,
                mechanism=request.mechanism,
                risk_hypothesis=request.risk_hypothesis,
                evaluation_plan=request.evaluation_plan,
                invalidation_conditions=request.invalidation_conditions,
                current_stage="hypothesis",
                created_by=request.created_by,
                origin_type=request.origin_type,
                origin_id=request.origin_id,
                status=request.status,
            )
            session.add(hypothesis)
            session.commit()
            session.refresh(hypothesis)
            return self._hypothesis_summary(hypothesis)

    def list_hypotheses(
        self,
        *,
        limit: int = 20,
        current_stages: Sequence[str] | None = None,
    ) -> list[StrategyHypothesisSummary]:
        with self.session_factory() as session:
            query = select(HypothesisModel).order_by(HypothesisModel.created_at.desc()).limit(limit)
            if current_stages:
                query = query.where(HypothesisModel.current_stage.in_(list(current_stages)))
            hypotheses = session.scalars(query).all()
            return [self._hypothesis_summary(hypothesis) for hypothesis in hypotheses]

    def create_strategy_spec(
        self,
        payload: StrategySpecCreate | dict[str, Any],
    ) -> StrategySpecSummary:
        request = StrategySpecCreate.model_validate(payload)
        with self.session_factory() as session:
            hypothesis = session.get(HypothesisModel, request.hypothesis_id)
            if hypothesis is None:
                raise ValueError(f"Hypothesis not found: {request.hypothesis_id}")

            existing = session.scalar(
                select(StrategySpecModel).where(StrategySpecModel.spec_code == request.spec_code)
            )
            if existing is not None:
                raise ValueError(f"Strategy spec code already exists: {request.spec_code}")

            spec = StrategySpecModel(
                hypothesis_id=request.hypothesis_id,
                spec_code=request.spec_code,
                version_label=request.version_label,
                title=request.title,
                target_market=request.target_market,
                signal_logic=request.signal_logic,
                risk_rules=request.risk_rules,
                data_requirements=request.data_requirements,
                invalidation_conditions=request.invalidation_conditions,
                execution_constraints=request.execution_constraints,
                current_stage="specified",
                created_by=request.created_by,
                origin_type=request.origin_type,
                origin_id=request.origin_id,
                status=request.status,
            )
            session.add(spec)
            hypothesis.current_stage = "specified"
            session.commit()
            session.refresh(spec)
            return self._spec_summary(spec)

    def list_strategy_specs(
        self,
        *,
        limit: int = 20,
        current_stages: Sequence[str] | None = None,
    ) -> list[StrategySpecSummary]:
        with self.session_factory() as session:
            query = select(StrategySpecModel).order_by(StrategySpecModel.created_at.desc()).limit(limit)
            if current_stages:
                query = query.where(StrategySpecModel.current_stage.in_(list(current_stages)))
            specs = session.scalars(query).all()
            return [self._spec_summary(spec) for spec in specs]

    def record_backtest(
        self,
        payload: BacktestRunCreate | dict[str, Any],
    ) -> BacktestRunSummary:
        request = BacktestRunCreate.model_validate(payload)
        with self.session_factory() as session:
            spec = session.get(StrategySpecModel, request.strategy_spec_id)
            if spec is None:
                raise ValueError(f"Strategy spec not found: {request.strategy_spec_id}")

            gate_result, gate_notes = self._evaluate_backtest(
                metrics=request.metrics_json,
                sample_size=request.sample_size,
            )
            backtest = BacktestRunModel(
                strategy_spec_id=request.strategy_spec_id,
                dataset_range=request.dataset_range,
                sample_size=request.sample_size,
                metrics_json=request.metrics_json,
                artifact_path=request.artifact_path,
                gate_result=gate_result,
                gate_notes=gate_notes,
                started_at=datetime.now(tz=UTC),
                completed_at=datetime.now(tz=UTC),
                created_by=request.created_by,
                origin_type=request.origin_type,
                origin_id=request.origin_id,
                status=request.status,
            )
            session.add(backtest)
            spec.latest_backtest_gate = gate_result
            spec.current_stage = self._spec_stage_after_backtest(gate_result)
            session.commit()
            session.refresh(backtest)
            return self._backtest_summary(backtest)

    def run_factor_replay_backtest(
        self,
        payload: FactorReplayBacktestCreate | dict[str, Any],
    ) -> BacktestRunSummary:
        request = FactorReplayBacktestCreate.model_validate(payload)
        with self.session_factory() as session:
            spec = session.get(StrategySpecModel, request.strategy_spec_id)
            if spec is None:
                raise ValueError(f"Strategy spec not found: {request.strategy_spec_id}")

            snapshots = self._latest_factor_snapshots(session, request)
            selected = [
                snapshot
                for snapshot in sorted(snapshots, key=lambda item: (item.rank or 999_999, -item.value))
                if snapshot.percentile is None or snapshot.percentile >= request.min_percentile
            ][: request.top_n]
            all_values = [snapshot.value for snapshot in snapshots]
            selected_values = [snapshot.value for snapshot in selected]
            input_bar_ids = sorted({bar_id for snapshot in selected for bar_id in (snapshot.input_bar_ids or [])})
            bar_count = 0
            if input_bar_ids:
                bar_count = int(
                    session.scalar(select(func.count(HistoricalBarModel.id)).where(HistoricalBarModel.id.in_(input_bar_ids)))
                    or 0
                )
            equity_curve, curve_max_drawdown_pct, curve_hit_ratio = self._build_equity_curve(
                session,
                input_bar_ids=input_bar_ids,
                selected_symbols=[snapshot.symbol for snapshot in selected],
            )

            gross_return_pct = round((sum(selected_values) / len(selected_values)) * 100, 6) if selected_values else 0.0
            baseline_return_pct = round((sum(all_values) / len(all_values)) * 100, 6) if all_values else 0.0
            cost_config = CostModelConfig.from_backtest_payload(
                cost_bps=request.cost_bps,
                slippage_bps=request.slippage_bps,
                payload=request.cost_model,
            )
            bars_by_symbol = self._historical_bars_by_symbol(
                session,
                input_bar_ids=input_bar_ids,
                selected_symbols=[snapshot.symbol for snapshot in selected],
            )
            cost_breakdowns = [
                estimate_symbol_trade_cost(
                    symbol=snapshot.symbol,
                    bars=bars_by_symbol.get(snapshot.symbol, []),
                    config=cost_config,
                )
                for snapshot in selected
            ]
            total_cost_pct = aggregate_cost_pct(cost_breakdowns)
            total_return_pct = round(gross_return_pct - total_cost_pct, 6)
            excess_return_pct = round(total_return_pct - baseline_return_pct, 6)
            factor_max_drawdown_pct = round(max([0.0, *[-value * 100 for value in selected_values if value < 0]]), 6)
            max_drawdown_pct = max(factor_max_drawdown_pct, curve_max_drawdown_pct)
            factor_hit_ratio = round(
                sum(1 for value in selected_values if value > 0) / len(selected_values),
                6,
            ) if selected_values else 0.0
            hit_ratio = curve_hit_ratio or factor_hit_ratio
            sharpe_ratio = round(total_return_pct / max(1.0, max_drawdown_pct or 1.0), 6)
            factor_snapshot_ids = [snapshot.id for snapshot in selected]
            dataset_range = self._dataset_range_from_snapshots(selected)
            metrics = {
                "sharpe_ratio": sharpe_ratio,
                "total_return_pct": total_return_pct,
                "gross_return_pct": gross_return_pct,
                "baseline_return_pct": baseline_return_pct,
                "excess_return_pct": excess_return_pct,
                "max_drawdown_pct": max_drawdown_pct,
                "hit_ratio": hit_ratio,
                "turnover": 1.0 if selected else 0.0,
                "trade_count": len(selected),
                "equity_curve": equity_curve,
                "factor_code": request.factor_code,
                "selected_symbols": [snapshot.symbol for snapshot in selected],
                "factor_snapshot_ids": factor_snapshot_ids,
                "input_bar_ids": input_bar_ids,
                "lineage": {
                    "strategy_spec_id": request.strategy_spec_id,
                    "factor_snapshot_ids": factor_snapshot_ids,
                    "input_bar_ids": input_bar_ids,
                    "bar_count": bar_count,
                    "as_of": request.as_of.isoformat() if request.as_of else None,
                },
                "cost_model": {
                    **cost_model_payload(cost_config, cost_breakdowns),
                    "cost_bps": request.cost_bps,
                    "slippage_bps": request.slippage_bps,
                },
                "baseline_refs": request.baseline_refs,
                "point_in_time_controls": request.point_in_time_controls,
            }
            gate_result, gate_notes = self._evaluate_backtest(metrics=metrics, sample_size=bar_count)
            backtest = BacktestRunModel(
                strategy_spec_id=request.strategy_spec_id,
                dataset_range=dataset_range,
                sample_size=bar_count,
                metrics_json=metrics,
                artifact_path=f"factor-replay://{request.factor_code}/{request.strategy_spec_id}",
                gate_result=gate_result,
                gate_notes=gate_notes,
                started_at=datetime.now(tz=UTC),
                completed_at=datetime.now(tz=UTC),
                created_by=request.created_by,
                origin_type=request.origin_type,
                origin_id=request.origin_id,
                status=request.status,
            )
            session.add(backtest)
            spec.latest_backtest_gate = gate_result
            spec.current_stage = self._spec_stage_after_backtest(gate_result)
            spec.execution_constraints = {
                **(spec.execution_constraints or {}),
                "latest_factor_replay": {
                    "factor_code": request.factor_code,
                    "factor_snapshot_ids": factor_snapshot_ids,
                    "input_bar_ids": input_bar_ids,
                    "gate_result": gate_result,
                },
            }
            session.commit()
            session.refresh(backtest)
            return self._backtest_summary(backtest)

    def list_backtests(
        self,
        *,
        limit: int = 20,
        strategy_spec_id: str | None = None,
        gate_results: Sequence[str] | None = None,
    ) -> list[BacktestRunSummary]:
        with self.session_factory() as session:
            query = select(BacktestRunModel).order_by(BacktestRunModel.created_at.desc()).limit(limit)
            if strategy_spec_id:
                query = query.where(BacktestRunModel.strategy_spec_id == strategy_spec_id)
            if gate_results:
                query = query.where(BacktestRunModel.gate_result.in_(list(gate_results)))
            backtests = session.scalars(query).all()
            return [self._backtest_summary(backtest) for backtest in backtests]

    def record_paper_run(
        self,
        payload: PaperRunCreate | dict[str, Any],
    ) -> PaperRunSummary:
        request = PaperRunCreate.model_validate(payload)
        with self.session_factory() as session:
            spec = session.get(StrategySpecModel, request.strategy_spec_id)
            if spec is None:
                raise ValueError(f"Strategy spec not found: {request.strategy_spec_id}")

            gate_result, gate_notes = self._evaluate_paper_run(
                metrics=request.metrics_json,
                monitoring_days=request.monitoring_days,
            )
            paper_run = PaperRunModel(
                strategy_spec_id=request.strategy_spec_id,
                deployment_label=request.deployment_label,
                monitoring_days=request.monitoring_days,
                metrics_json=request.metrics_json,
                capital_allocated=request.capital_allocated,
                gate_result=gate_result,
                gate_notes=gate_notes,
                started_at=datetime.now(tz=UTC),
                completed_at=datetime.now(tz=UTC),
                created_by=request.created_by,
                origin_type=request.origin_type,
                origin_id=request.origin_id,
                status=request.status,
            )
            session.add(paper_run)
            spec.latest_paper_gate = gate_result
            spec.current_stage = self._spec_stage_after_paper_run(gate_result)
            session.commit()
            session.refresh(paper_run)
            return self._paper_run_summary(paper_run)

    def list_paper_runs(
        self,
        *,
        limit: int = 20,
        strategy_spec_id: str | None = None,
        gate_results: Sequence[str] | None = None,
    ) -> list[PaperRunSummary]:
        with self.session_factory() as session:
            query = select(PaperRunModel).order_by(PaperRunModel.created_at.desc()).limit(limit)
            if strategy_spec_id:
                query = query.where(PaperRunModel.strategy_spec_id == strategy_spec_id)
            if gate_results:
                query = query.where(PaperRunModel.gate_result.in_(list(gate_results)))
            paper_runs = session.scalars(query).all()
            return [self._paper_run_summary(paper_run) for paper_run in paper_runs]

    def record_promotion_decision(
        self,
        payload: PromotionDecisionCreate | dict[str, Any],
    ) -> PromotionDecisionSummary:
        request = PromotionDecisionCreate.model_validate(payload)
        with self.session_factory() as session:
            spec = session.get(StrategySpecModel, request.strategy_spec_id)
            if spec is None:
                raise ValueError(f"Strategy spec not found: {request.strategy_spec_id}")
            if request.paper_run_id is not None and session.get(PaperRunModel, request.paper_run_id) is None:
                raise ValueError(f"Paper run not found: {request.paper_run_id}")

            decision = PromotionDecisionModel(
                strategy_spec_id=request.strategy_spec_id,
                paper_run_id=request.paper_run_id,
                target_stage=request.target_stage,
                decision=request.decision,
                rationale=request.rationale,
                evidence_refs=request.evidence_refs,
                decided_by=request.decided_by,
                created_by=request.created_by or request.decided_by,
                origin_type=request.origin_type,
                origin_id=request.origin_id,
                status=request.status or request.decision,
            )
            session.add(decision)
            if request.decision == "approved":
                spec.current_stage = request.target_stage
            elif request.decision == "rejected":
                spec.current_stage = f"{request.target_stage}_rejected"
            else:
                spec.current_stage = f"{request.target_stage}_deferred"
            session.commit()
            session.refresh(decision)
            return self._promotion_summary(decision)

    def list_promotion_decisions(
        self,
        *,
        limit: int = 20,
        strategy_spec_id: str | None = None,
    ) -> list[PromotionDecisionSummary]:
        with self.session_factory() as session:
            query = select(PromotionDecisionModel).order_by(PromotionDecisionModel.created_at.desc()).limit(limit)
            if strategy_spec_id:
                query = query.where(PromotionDecisionModel.strategy_spec_id == strategy_spec_id)
            decisions = session.scalars(query).all()
            return [self._promotion_summary(decision) for decision in decisions]

    def record_withdrawal_decision(
        self,
        payload: WithdrawalDecisionCreate | dict[str, Any],
    ) -> WithdrawalDecisionSummary:
        request = WithdrawalDecisionCreate.model_validate(payload)
        with self.session_factory() as session:
            spec = session.get(StrategySpecModel, request.strategy_spec_id)
            if spec is None:
                raise ValueError(f"Strategy spec not found: {request.strategy_spec_id}")
            if request.replacement_strategy_spec_id is not None and session.get(
                StrategySpecModel,
                request.replacement_strategy_spec_id,
            ) is None:
                raise ValueError(f"Replacement strategy spec not found: {request.replacement_strategy_spec_id}")

            decision = WithdrawalDecisionModel(
                strategy_spec_id=request.strategy_spec_id,
                replacement_strategy_spec_id=request.replacement_strategy_spec_id,
                reason=request.reason,
                evidence_refs=request.evidence_refs,
                decided_by=request.decided_by,
                created_by=request.created_by or request.decided_by,
                origin_type=request.origin_type,
                origin_id=request.origin_id,
                status=request.status or "withdrawn",
            )
            session.add(decision)
            spec.current_stage = "withdrawn"
            spec.status = "withdrawn"
            session.commit()
            session.refresh(decision)
            return self._withdrawal_summary(decision)

    def list_withdrawal_decisions(
        self,
        *,
        limit: int = 20,
        strategy_spec_id: str | None = None,
    ) -> list[WithdrawalDecisionSummary]:
        with self.session_factory() as session:
            query = select(WithdrawalDecisionModel).order_by(WithdrawalDecisionModel.created_at.desc()).limit(limit)
            if strategy_spec_id:
                query = query.where(WithdrawalDecisionModel.strategy_spec_id == strategy_spec_id)
            decisions = session.scalars(query).all()
            return [self._withdrawal_summary(decision) for decision in decisions]

    def get_metrics(self) -> StrategyLabMetrics:
        with self.session_factory() as session:
            return StrategyLabMetrics(
                hypothesis_count=self._count(session, select(func.count()).select_from(HypothesisModel)),
                spec_count=self._count(session, select(func.count()).select_from(StrategySpecModel)),
                paper_candidate_count=self._count(
                    session,
                    select(func.count()).select_from(StrategySpecModel).where(
                        StrategySpecModel.current_stage == "paper_candidate"
                    ),
                ),
                paper_running_count=self._count(
                    session,
                    select(func.count()).select_from(StrategySpecModel).where(
                        StrategySpecModel.current_stage == "paper_running"
                    ),
                ),
                live_candidate_count=self._count(
                    session,
                    select(func.count()).select_from(StrategySpecModel).where(
                        StrategySpecModel.current_stage == "live_candidate"
                    ),
                ),
                production_count=self._count(
                    session,
                    select(func.count()).select_from(StrategySpecModel).where(
                        StrategySpecModel.current_stage == "production"
                    ),
                ),
            )

    def _audit_research_brief(
        self,
        request: StrategyResearchBriefCreate,
    ) -> tuple[str, list[str], float]:
        required_groups = {
            "LLM model version": bool(request.llm_model),
            "LLM model cutoff": bool(request.llm_model_cutoff),
            "Prompt hash or durable prompt reference": bool(request.prompt_hash),
            "Tool or source trace": bool(request.tool_refs),
            "External evidence references": bool(request.evidence_refs),
            "Data requirements": bool(request.data_requirements),
            "Point-in-time controls": bool(request.point_in_time_controls),
            "Evaluation plan": bool(request.evaluation_plan),
            "Cost and slippage requirements": bool(request.cost_model_requirements),
            "Baseline comparisons": bool(request.baseline_refs),
            "Invalidation conditions": bool(request.invalidation_conditions),
            "Risk controls": bool(request.risk_controls_required),
            "Attack or leakage tests": bool(request.attack_tests_required),
        }
        notes = [f"Missing {label}." for label, present in required_groups.items() if not present]
        blockers = self._research_brief_blockers(request)
        adversarial = run_adversarial_checks(request.model_dump())
        blockers.extend(adversarial.notes)
        readiness_score = round(sum(1 for present in required_groups.values() if present) / len(required_groups), 3)

        if blockers:
            return ("blocked", blockers + notes, readiness_score)
        if notes:
            return ("needs_evidence", notes, readiness_score)
        return ("ready_for_spec", ["Research brief satisfies the LLM quant opportunity gate."], readiness_score)

    def _research_brief_blockers(self, request: StrategyResearchBriefCreate) -> list[str]:
        text_parts: list[str] = [
            request.title,
            request.thesis,
            request.signal_definition,
            request.expected_mechanism,
            " ".join(request.evaluation_plan),
            " ".join(request.invalidation_conditions),
            " ".join(request.risk_controls_required),
        ]
        text = " ".join(part.lower() for part in text_parts if part)
        blocked_patterns = {
            "direct live": "Brief requests direct live deployment before gated validation.",
            "immediate live": "Brief requests immediate live deployment before gated validation.",
            "place live order": "Brief crosses from research into live order execution.",
            "send live order": "Brief crosses from research into live order execution.",
            "skip backtest": "Brief attempts to skip backtest validation.",
            "skip paper": "Brief attempts to skip paper validation.",
            "ignore risk": "Brief explicitly weakens risk controls.",
            "all in": "Brief implies unbounded capital allocation.",
        }
        return [message for phrase, message in blocked_patterns.items() if phrase in text]

    def _research_brief_summary(self, brief: StrategyResearchBriefModel) -> StrategyResearchBriefSummary:
        return StrategyResearchBriefSummary(
            id=brief.id,
            source_insight_id=brief.source_insight_id,
            title=brief.title,
            opportunity_kind=brief.opportunity_kind,
            target_market=brief.target_market,
            audit_status=brief.audit_status,
            audit_notes=list(brief.audit_notes),
            readiness_score=brief.readiness_score,
            promoted_hypothesis_id=brief.promoted_hypothesis_id,
            status=brief.status,
            created_at=brief.created_at,
        )

    def _evaluate_backtest(
        self,
        *,
        metrics: dict[str, Any],
        sample_size: int,
    ) -> tuple[str, list[str]]:
        sharpe_ratio = self._metric_float(metrics, "sharpe_ratio")
        total_return_pct = self._metric_float(metrics, "total_return_pct")
        max_drawdown_pct = self._metric_float(metrics, "max_drawdown_pct", default=100.0)
        excess_return_pct = self._metric_float(metrics, "excess_return_pct")

        notes: list[str] = []
        if not metrics.get("cost_model"):
            notes.append("Missing explicit cost and slippage model.")
        if not metrics.get("baseline_refs") or "baseline_return_pct" not in metrics:
            notes.append("Missing baseline comparison.")
        if not metrics.get("point_in_time_controls"):
            notes.append("Missing point-in-time replay controls.")
        statistical = validate_backtest_statistics(metrics, sample_size=sample_size)
        metrics["statistical_validation"] = statistical.metrics
        notes.extend(statistical.notes)
        adversarial = run_adversarial_checks(metrics)
        metrics["adversarial_validation"] = {
            "passed": adversarial.passed,
            "risk_counts": adversarial.risk_counts,
        }
        notes.extend(adversarial.notes)
        lineage = metrics.get("lineage") if isinstance(metrics.get("lineage"), dict) else {}
        if not lineage.get("input_bar_ids") and not metrics.get("input_bar_ids"):
            notes.append("Missing data lineage from bars to signals.")
        if "baseline_return_pct" in metrics and excess_return_pct <= 0:
            notes.append("No positive uplift versus baseline after costs.")
        if sample_size < 100:
            notes.append("Sample size below the paper-promotion floor (100).")
        if sharpe_ratio < 1.0:
            notes.append("Sharpe ratio below 1.0.")
        if max_drawdown_pct > 15.0:
            notes.append("Max drawdown above 15%.")
        if total_return_pct <= 0:
            notes.append("Total return is not positive.")

        governance_clear = not any(
            note.startswith("Missing") or "baseline" in note.lower()
            for note in notes
        )
        if (
            governance_clear
            and statistical.passed
            and adversarial.passed
            and sample_size >= 100
            and sharpe_ratio >= 1.0
            and max_drawdown_pct <= 15.0
            and total_return_pct > 0
        ):
            return ("passed", ["Backtest satisfies the paper-candidate gate."])
        if max_drawdown_pct > 25.0 or total_return_pct < -5.0:
            return ("failed", notes or ["Backtest failed the hard safety gate."])
        return ("needs_review", notes or ["Backtest needs additional review."])

    def _evaluate_paper_run(
        self,
        *,
        metrics: dict[str, Any],
        monitoring_days: int,
    ) -> tuple[str, list[str]]:
        net_pnl_pct = self._metric_float(metrics, "net_pnl_pct")
        profit_factor = self._metric_float(metrics, "profit_factor")
        max_drawdown_pct = self._metric_float(metrics, "max_drawdown_pct", default=100.0)

        notes: list[str] = []
        if monitoring_days < 10:
            notes.append("Paper monitoring window is below 10 days.")
        if profit_factor < 1.05:
            notes.append("Profit factor is below 1.05.")
        if max_drawdown_pct > 8.0:
            notes.append("Max drawdown above 8% during paper trading.")
        if net_pnl_pct <= 0:
            notes.append("Paper PnL is not positive.")

        if monitoring_days >= 10 and profit_factor >= 1.05 and max_drawdown_pct <= 8.0 and net_pnl_pct > 0:
            return ("ready_for_live_review", ["Paper run satisfies the live-candidate review gate."])
        if max_drawdown_pct > 12.0 or net_pnl_pct < -3.0:
            return ("failed", notes or ["Paper run failed the hard safety gate."])
        if monitoring_days < 5:
            return ("monitoring", notes or ["Paper run is still gathering monitoring evidence."])
        return ("needs_review", notes or ["Paper run needs additional review."])

    def _spec_stage_after_backtest(self, gate_result: str) -> str:
        mapping = {
            "passed": "paper_candidate",
            "failed": "backtest_failed",
            "needs_review": "backtest_review",
        }
        return mapping.get(gate_result, "backtest_review")

    def _spec_stage_after_paper_run(self, gate_result: str) -> str:
        mapping = {
            "ready_for_live_review": "live_candidate",
            "failed": "paper_failed",
            "monitoring": "paper_running",
            "needs_review": "paper_review",
        }
        return mapping.get(gate_result, "paper_review")

    def _hypothesis_summary(self, hypothesis: HypothesisModel) -> StrategyHypothesisSummary:
        return StrategyHypothesisSummary(
            id=hypothesis.id,
            source_insight_id=hypothesis.source_insight_id,
            title=hypothesis.title,
            thesis=hypothesis.thesis,
            target_market=hypothesis.target_market,
            current_stage=hypothesis.current_stage,
            status=hypothesis.status,
            created_at=hypothesis.created_at,
        )

    def _spec_summary(self, spec: StrategySpecModel) -> StrategySpecSummary:
        return StrategySpecSummary(
            id=spec.id,
            hypothesis_id=spec.hypothesis_id,
            spec_code=spec.spec_code,
            version_label=spec.version_label,
            title=spec.title,
            target_market=spec.target_market,
            current_stage=spec.current_stage,
            latest_backtest_gate=spec.latest_backtest_gate,
            latest_paper_gate=spec.latest_paper_gate,
            status=spec.status,
            created_at=spec.created_at,
        )

    def _backtest_summary(self, backtest: BacktestRunModel) -> BacktestRunSummary:
        return BacktestRunSummary(
            id=backtest.id,
            strategy_spec_id=backtest.strategy_spec_id,
            dataset_range=backtest.dataset_range,
            sample_size=backtest.sample_size,
            gate_result=backtest.gate_result,
            gate_notes=list(backtest.gate_notes),
            metrics_json=dict(backtest.metrics_json),
            artifact_path=backtest.artifact_path,
            created_at=backtest.created_at,
        )

    def _paper_run_summary(self, paper_run: PaperRunModel) -> PaperRunSummary:
        return PaperRunSummary(
            id=paper_run.id,
            strategy_spec_id=paper_run.strategy_spec_id,
            deployment_label=paper_run.deployment_label,
            monitoring_days=paper_run.monitoring_days,
            gate_result=paper_run.gate_result,
            gate_notes=list(paper_run.gate_notes),
            metrics_json=dict(paper_run.metrics_json),
            capital_allocated=paper_run.capital_allocated,
            status=paper_run.status,
            created_at=paper_run.created_at,
        )

    def _promotion_summary(self, decision: PromotionDecisionModel) -> PromotionDecisionSummary:
        return PromotionDecisionSummary(
            id=decision.id,
            strategy_spec_id=decision.strategy_spec_id,
            paper_run_id=decision.paper_run_id,
            target_stage=decision.target_stage,
            decision=decision.decision,
            rationale=decision.rationale,
            decided_by=decision.decided_by,
            decided_at=decision.decided_at,
            created_at=decision.created_at,
        )

    def _withdrawal_summary(self, decision: WithdrawalDecisionModel) -> WithdrawalDecisionSummary:
        return WithdrawalDecisionSummary(
            id=decision.id,
            strategy_spec_id=decision.strategy_spec_id,
            replacement_strategy_spec_id=decision.replacement_strategy_spec_id,
            reason=decision.reason,
            decided_by=decision.decided_by,
            decided_at=decision.decided_at,
            created_at=decision.created_at,
        )

    def _metric_float(self, metrics: dict[str, Any], key: str, *, default: float = 0.0) -> float:
        value = metrics.get(key, default)
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _latest_factor_snapshots(
        self,
        session: Session,
        request: FactorReplayBacktestCreate,
    ) -> list[FactorSnapshotModel]:
        query = select(FactorSnapshotModel).where(
            FactorSnapshotModel.factor_code == request.factor_code,
            FactorSnapshotModel.market == request.market,
        )
        if request.as_of is not None:
            query = query.where(FactorSnapshotModel.as_of <= request.as_of)
        rows = session.scalars(
            query.order_by(desc(FactorSnapshotModel.as_of), FactorSnapshotModel.symbol.asc())
        ).all()

        latest_by_symbol: dict[str, FactorSnapshotModel] = {}
        for row in rows:
            if request.provider_key and (row.lineage_payload or {}).get("provider_key") != request.provider_key:
                continue
            if row.symbol not in latest_by_symbol:
                latest_by_symbol[row.symbol] = row
        return list(latest_by_symbol.values())

    def _dataset_range_from_snapshots(self, snapshots: list[FactorSnapshotModel]) -> str | None:
        dates = [snapshot.as_of for snapshot in snapshots if snapshot.as_of is not None]
        if not dates:
            return None
        return f"{min(dates).date().isoformat()}..{max(dates).date().isoformat()}"

    def _build_equity_curve(
        self,
        session: Session,
        *,
        input_bar_ids: list[str],
        selected_symbols: list[str],
    ) -> tuple[list[dict[str, Any]], float, float]:
        if not input_bar_ids or not selected_symbols:
            return [], 0.0, 0.0
        rows = session.scalars(
            select(HistoricalBarModel)
            .where(HistoricalBarModel.id.in_(input_bar_ids), HistoricalBarModel.symbol.in_(selected_symbols))
            .order_by(HistoricalBarModel.bar_start.asc(), HistoricalBarModel.symbol.asc())
        ).all()
        bars_by_symbol: dict[str, list[HistoricalBarModel]] = {}
        for row in rows:
            bars_by_symbol.setdefault(row.symbol, []).append(row)

        returns_by_date: dict[str, list[float]] = {}
        for bars in bars_by_symbol.values():
            for previous, current in zip(bars, bars[1:], strict=False):
                previous_close = previous.adjusted_close if previous.is_adjusted and previous.adjusted_close else previous.close
                current_close = current.adjusted_close if current.is_adjusted and current.adjusted_close else current.close
                if previous_close == 0:
                    continue
                date_key = current.bar_start.date().isoformat()
                returns_by_date.setdefault(date_key, []).append((current_close / previous_close) - 1.0)

        equity = 1.0
        peak = 1.0
        max_drawdown = 0.0
        positive_days = 0
        curve: list[dict[str, Any]] = []
        for date_key in sorted(returns_by_date):
            daily_returns = returns_by_date[date_key]
            if not daily_returns:
                continue
            daily_return = sum(daily_returns) / len(daily_returns)
            equity *= 1.0 + daily_return
            peak = max(peak, equity)
            drawdown = 0.0 if peak == 0 else (peak - equity) / peak
            max_drawdown = max(max_drawdown, drawdown)
            if daily_return > 0:
                positive_days += 1
            curve.append(
                {
                    "date": date_key,
                    "return_pct": round(daily_return * 100, 6),
                    "equity": round(equity, 8),
                    "drawdown_pct": round(drawdown * 100, 6),
                }
            )

        hit_ratio = round(positive_days / len(curve), 6) if curve else 0.0
        return curve, round(max_drawdown * 100, 6), hit_ratio

    def _historical_bars_by_symbol(
        self,
        session: Session,
        *,
        input_bar_ids: list[str],
        selected_symbols: list[str],
    ) -> dict[str, list[HistoricalBarModel]]:
        if not input_bar_ids or not selected_symbols:
            return {}
        rows = session.scalars(
            select(HistoricalBarModel)
            .where(HistoricalBarModel.id.in_(input_bar_ids), HistoricalBarModel.symbol.in_(selected_symbols))
            .order_by(HistoricalBarModel.symbol.asc(), HistoricalBarModel.bar_start.asc())
        ).all()
        bars_by_symbol: dict[str, list[HistoricalBarModel]] = {}
        for row in rows:
            bars_by_symbol.setdefault(row.symbol, []).append(row)
        return bars_by_symbol

    def _count(self, session: Session, query: Any) -> int:
        value = session.scalar(query)
        return int(value or 0)
