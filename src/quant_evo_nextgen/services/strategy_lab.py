from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable, Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from quant_evo_nextgen.contracts.state import (
    BacktestRunCreate,
    BacktestRunSummary,
    PaperRunCreate,
    PaperRunSummary,
    PromotionDecisionCreate,
    PromotionDecisionSummary,
    StrategyHypothesisCreate,
    StrategyHypothesisSummary,
    StrategySpecCreate,
    StrategySpecSummary,
    WithdrawalDecisionCreate,
    WithdrawalDecisionSummary,
)
from quant_evo_nextgen.db.models import (
    BacktestRunModel,
    HypothesisModel,
    InsightModel,
    PaperRunModel,
    PromotionDecisionModel,
    StrategySpecModel,
    WithdrawalDecisionModel,
)


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

    def _evaluate_backtest(
        self,
        *,
        metrics: dict[str, Any],
        sample_size: int,
    ) -> tuple[str, list[str]]:
        sharpe_ratio = self._metric_float(metrics, "sharpe_ratio")
        total_return_pct = self._metric_float(metrics, "total_return_pct")
        max_drawdown_pct = self._metric_float(metrics, "max_drawdown_pct", default=100.0)

        notes: list[str] = []
        if sample_size < 100:
            notes.append("Sample size below the paper-promotion floor (100).")
        if sharpe_ratio < 1.0:
            notes.append("Sharpe ratio below 1.0.")
        if max_drawdown_pct > 15.0:
            notes.append("Max drawdown above 15%.")
        if total_return_pct <= 0:
            notes.append("Total return is not positive.")

        if sample_size >= 100 and sharpe_ratio >= 1.0 and max_drawdown_pct <= 15.0 and total_return_pct > 0:
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

    def _count(self, session: Session, query: Any) -> int:
        value = session.scalar(query)
        return int(value or 0)
