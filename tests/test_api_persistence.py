import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import text

from quant_evo_nextgen.api.main import create_app
from quant_evo_nextgen.config import Settings
from quant_evo_nextgen.db.models import DocumentModel, EvidenceItemModel, InsightModel
from quant_evo_nextgen.services.broker import (
    BrokerAccountState,
    BrokerCancelRequest,
    BrokerCancelResult,
    BrokerExecutionRequest,
    BrokerExecutionResult,
    BrokerOrderState,
    BrokerReplaceRequest,
    BrokerReplaceResult,
    BrokerSyncRequest,
    BrokerSyncResult,
    PositionState,
)


class ScriptedAsyncBrokerAdapter:
    adapter_key = "scripted_async"

    def __init__(self) -> None:
        self.base_equity = 10000.0
        self.base_cash = 10000.0
        self.orders: dict[str, BrokerOrderState] = {}
        self.positions: dict[str, PositionState] = {}

    def execute_order(
        self,
        request: BrokerExecutionRequest,
        current_position: PositionState | None,
    ) -> BrokerExecutionResult:
        broker_order_id = f"scripted-{uuid4()}"
        current_time = datetime.now(tz=UTC)
        self.orders[broker_order_id] = BrokerOrderState(
            broker_order_id=broker_order_id,
            client_order_id=request.client_order_id,
            symbol=request.symbol,
            instrument_id=request.instrument_id,
            instrument_key=request.instrument_key,
            underlying_symbol=request.underlying_symbol,
            asset_type=request.asset_type,
            position_effect=request.position_effect,
            side=request.side,
            order_type=request.order_type,
            time_in_force=request.time_in_force,
            quantity=request.quantity,
            filled_quantity=0.0,
            requested_notional=request.requested_notional,
            avg_fill_price=None,
            limit_price=request.limit_price,
            stop_price=request.stop_price,
            status="submitted",
            broker_updated_at=current_time,
            raw_payload={"adapter": self.adapter_key, "mode": "async_submit"},
        )
        return BrokerExecutionResult(
            broker_order_id=broker_order_id,
            client_order_id=request.client_order_id,
            order_status="submitted",
            filled_quantity=0.0,
            avg_fill_price=None,
            broker_updated_at=current_time,
            raw_payload={"adapter": self.adapter_key, "mode": "async_submit"},
            resulting_position=None,
        )

    def sync_state(self, request: BrokerSyncRequest) -> BrokerSyncResult:
        active_positions = [position for position in self.positions.values() if position.quantity > 0]
        gross_exposure = sum((position.market_price or position.avg_entry_price) * position.quantity for position in active_positions)
        return BrokerSyncResult(
            account_state=BrokerAccountState(
                provider_key=request.provider_key,
                account_ref=request.account_ref,
                environment=request.environment,
                equity=self.base_equity,
                cash=max(0.0, self.base_cash - gross_exposure),
                buying_power=max(0.0, self.base_equity - gross_exposure),
                gross_exposure=gross_exposure,
                net_exposure=gross_exposure,
                positions_count=len(active_positions),
                open_orders_count=sum(1 for order in self.orders.values() if order.status in {"accepted", "submitted", "partially_filled"}),
                source_captured_at=datetime.now(tz=UTC),
                source_age_seconds=0,
                raw_payload={"adapter": self.adapter_key},
            ),
            orders=list(self.orders.values()),
            positions=active_positions,
            notes=[],
            raw_payload={"adapter": self.adapter_key, "full_sync": request.full_sync},
        )

    def cancel_order(
        self,
        request: BrokerCancelRequest,
        current_order: BrokerOrderState,
    ) -> BrokerCancelResult:
        current_time = datetime.now(tz=UTC)
        state = self.orders[current_order.broker_order_id]
        state.status = "canceled"
        state.broker_updated_at = current_time
        state.raw_payload = {"adapter": self.adapter_key, "action": "cancel"}
        return BrokerCancelResult(
            broker_order_id=state.broker_order_id,
            client_order_id=state.client_order_id,
            order_status=state.status,
            broker_updated_at=state.broker_updated_at,
            raw_payload=state.raw_payload,
        )

    def replace_order(
        self,
        request: BrokerReplaceRequest,
        current_order: BrokerOrderState,
    ) -> BrokerReplaceResult:
        current_time = datetime.now(tz=UTC)
        state = self.orders[current_order.broker_order_id]
        state.status = "replaced"
        state.broker_updated_at = current_time
        state.raw_payload = {"adapter": self.adapter_key, "action": "replace"}
        replacement_order = BrokerOrderState(
            broker_order_id=f"scripted-{uuid4()}",
            client_order_id=request.client_order_id,
            symbol=request.symbol,
            instrument_id=request.instrument_id,
            instrument_key=request.instrument_key,
            underlying_symbol=request.underlying_symbol,
            asset_type=request.asset_type,
            position_effect=request.position_effect,
            side=request.side,
            order_type=request.order_type,
            time_in_force=request.time_in_force,
            quantity=request.quantity,
            filled_quantity=0.0,
            requested_notional=request.requested_notional,
            avg_fill_price=None,
            limit_price=request.limit_price,
            stop_price=request.stop_price,
            status="submitted",
            broker_updated_at=current_time,
            raw_payload={"adapter": self.adapter_key, "action": "replace_submit"},
        )
        self.orders[replacement_order.broker_order_id] = replacement_order
        return BrokerReplaceResult(
            previous_order_status=state.status,
            previous_broker_updated_at=state.broker_updated_at,
            previous_raw_payload=state.raw_payload,
            replacement_order=replacement_order,
        )

    def fill_order(self, broker_order_id: str, fill_price: float) -> None:
        state = self.orders[broker_order_id]
        state.status = "filled"
        state.filled_quantity = state.quantity
        state.avg_fill_price = fill_price
        state.broker_updated_at = datetime.now(tz=UTC)
        self.positions[state.symbol] = PositionState(
            strategy_spec_id="external-sync",
            symbol=state.symbol,
            asset_type=state.asset_type,
            direction="long",
            quantity=state.quantity,
            avg_entry_price=fill_price,
            realized_pnl=0.0,
            instrument_id=state.instrument_id,
            instrument_key=state.instrument_key,
            underlying_symbol=state.underlying_symbol,
            market_price=fill_price,
            raw_payload={"adapter": self.adapter_key},
        )


def test_api_persists_goals_incidents_and_dashboard_counts(tmp_path: Path) -> None:
    _seed_repo_state(tmp_path)
    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'api.db'}",
        db_bootstrap_on_start=True,
    )
    app = create_app(settings)

    with TestClient(app) as client:
        goal_response = client.post(
            "/api/v1/goals",
            json={
                "title": "Stabilize provider abstraction",
                "description": "Track relay drift explicitly.",
                "mission_domain": "governance",
                "status": "active",
                "created_by": "tester",
            },
        )
        assert goal_response.status_code == 200

        incident_response = client.post(
            "/api/v1/incidents",
            json={
                "title": "Discord token rotation drill",
                "summary": "Validate break-glass path.",
                "severity": "SEV-3",
                "status": "open",
            },
        )
        assert incident_response.status_code == 200

        approval_response = client.post(
            "/api/v1/approvals",
            json={
                "approval_type": "pause_evolution",
                "subject_type": "domain",
                "subject_id": "evolution",
                "requested_by": "tester",
                "risk_level": "R2",
            },
        )
        assert approval_response.status_code == 200

        client.app.state.state_store.record_heartbeat(
            node_role="core",
            deployment_topology="single_node_bootstrap",
            mode="paper_only",
            risk_state="observe",
            summary_payload={"production_strategies": 1},
        )

        overview_response = client.get("/api/v1/dashboard/overview")
        trading_response = client.get("/api/v1/dashboard/trading")
        system_dashboard_response = client.get("/api/v1/dashboard/system")
        status_response = client.get("/api/v1/system/status")

        assert overview_response.status_code == 200
        assert trading_response.status_code == 200
        assert system_dashboard_response.status_code == 200
        assert status_response.status_code == 200

        overview_payload = overview_response.json()
        trading_payload = trading_response.json()
        system_dashboard_payload = system_dashboard_response.json()
        status_payload = status_response.json()

        assert overview_payload["system"]["active_goals"] == 1
        assert overview_payload["system"]["open_incidents"] == 1
        assert overview_payload["freshness"]["state"] in {"fresh", "lagging"}
        assert "pending approvals 1" in overview_payload["highlights"][3]
        assert trading_payload["domain_states"][1]["domain"] == "evolution"
        assert system_dashboard_payload["providers"][0]["provider_key"] == "primary-relay"
        assert status_payload["active_goals"] == 1
        assert status_payload["open_incidents"] == 1
        assert status_payload["pending_approvals"] == 1


def test_api_exposes_queued_codex_runs_in_system_views(tmp_path: Path) -> None:
    _seed_repo_state(tmp_path)
    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'api-codex.db'}",
        db_bootstrap_on_start=True,
        openai_api_key="relay-key",
        openai_base_url="https://relay.example.com/v1",
    )
    app = create_app(settings)

    with TestClient(app) as client:
        queue_response = client.post(
            "/api/v1/codex/runs",
            json={
                "codex_run_id": "api-codex-1",
                "worker_class": "implementation_worker",
                "objective": "Implement a supervised improvement task.",
                "context_summary": "Queue the task for the codex fabric runner.",
                "repo_path": str(tmp_path),
                "workspace_path": str(tmp_path),
                "write_scope": ["src/"],
                "allowed_tools": ["shell"],
                "search_enabled": False,
                "risk_tier": "R2",
                "max_duration_sec": 120,
                "max_token_budget": 10000,
                "max_iterations": 3,
                "acceptance_criteria": ["Persist the queued request."],
                "review_required": True,
                "eval_required": True,
            },
        )
        assert queue_response.status_code == 200

        system_dashboard_response = client.get("/api/v1/dashboard/system")
        evolution_dashboard_response = client.get("/api/v1/dashboard/evolution")
        status_response = client.get("/api/v1/system/status")

        assert system_dashboard_response.status_code == 200
        assert evolution_dashboard_response.status_code == 200
        assert status_response.status_code == 200

        system_dashboard_payload = system_dashboard_response.json()
        evolution_dashboard_payload = evolution_dashboard_response.json()
        status_payload = status_response.json()

        assert system_dashboard_payload["recent_codex_runs"][0]["id"] == "api-codex-1"
        assert evolution_dashboard_payload["recent_codex_runs"][0]["status"] == "queued"
        assert status_payload["codex_queue_depth"] == 1


def test_api_exposes_runtime_config_registry_and_system_dashboard_cards(tmp_path: Path) -> None:
    _seed_repo_state(tmp_path)
    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'api-runtime-config.db'}",
        db_bootstrap_on_start=True,
    )
    app = create_app(settings)

    with TestClient(app) as client:
        proposal_response = client.post(
            "/api/v1/runtime-config/proposals",
            json={
                "target_type": "system_policy",
                "target_key": "heartbeat_runtime",
                "requested_by": "tester",
                "proposed_value_json": {"interval_seconds": 240},
                "change_summary": "Increase heartbeat interval.",
            },
        )
        assert proposal_response.status_code == 200
        proposal_payload = proposal_response.json()

        apply_response = client.post(f"/api/v1/runtime-config/proposals/{proposal_payload['id']}/apply")
        assert apply_response.status_code == 200

        config_response = client.get("/api/v1/runtime-config")
        revisions_response = client.get("/api/v1/runtime-config/revisions")
        system_dashboard_response = client.get("/api/v1/dashboard/system")

        assert config_response.status_code == 200
        assert revisions_response.status_code == 200
        assert system_dashboard_response.status_code == 200

        config_payload = config_response.json()
        revisions_payload = revisions_response.json()
        system_dashboard_payload = system_dashboard_response.json()

        heartbeat_entry = next(entry for entry in config_payload if entry["target_key"] == "heartbeat_runtime")
        dashboard_heartbeat_entry = next(
            entry for entry in system_dashboard_payload["runtime_config"] if entry["target_key"] == "heartbeat_runtime"
        )
        discord_access_entry = next(
            entry
            for entry in system_dashboard_payload["owner_preferences"]
            if entry["preference_key"] == "discord_access"
        )
        assert heartbeat_entry["value_json"]["interval_seconds"] == 240
        assert revisions_payload[0]["target_key"] == "heartbeat_runtime"
        assert system_dashboard_payload["runtime_config"]
        assert system_dashboard_payload["recent_config_revisions"][0]["target_key"] == "heartbeat_runtime"
        assert all(entry["target_type"] != "owner_preference" for entry in system_dashboard_payload["runtime_config"])
        assert "value_json" not in dashboard_heartbeat_entry
        assert dashboard_heartbeat_entry["contains_sensitive_fields"] is False
        assert "Interval seconds: 240" in dashboard_heartbeat_entry["preview_lines"]
        assert "value_json" not in discord_access_entry
        assert discord_access_entry["contains_sensitive_fields"] is True
        assert any("not configured" in line or "configured" in line for line in discord_access_entry["preview_lines"])


def test_api_exposes_system_doctor_report(tmp_path: Path) -> None:
    _seed_repo_state(tmp_path)
    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'api-doctor.db'}",
        db_bootstrap_on_start=True,
        discord_token="token",
        discord_allowed_user_ids="123456789",
        openai_api_key="relay-key",
        openai_base_url="https://relay.example.com/v1",
    )
    app = create_app(settings)

    with TestClient(app) as client:
        with client.app.state.database.session_scope() as session:
            session.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
            session.execute(text("INSERT INTO alembic_version (version_num) VALUES ('20260320_0014')"))

        doctor_response = client.get("/api/v1/system/doctor")
        assert doctor_response.status_code == 200

        payload = doctor_response.json()
        assert payload["status"] == "warn"
        assert any(check["key"] == "runtime_registry" and check["status"] == "ok" for check in payload["checks"])
        assert any(profile["key"] == "node_vps_deploy" for profile in payload["profiles"])
        assert any(profile["key"] == "capital_activation" for profile in payload["profiles"])
        assert any(profile["key"] == "owner_target_full_system" for profile in payload["profiles"])


def test_api_persists_evolution_governance_records_and_dashboard_metrics(tmp_path: Path) -> None:
    _seed_repo_state(tmp_path)
    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'api-evolution.db'}",
        db_bootstrap_on_start=True,
    )
    app = create_app(settings)

    with TestClient(app) as client:
        proposal_response = client.post(
            "/api/v1/evolution/proposals",
            json={
                "title": "Tighten research quarantine scoring",
                "summary": "Promote only evidence-backed insights with lower drift risk.",
                "target_surface": "learning",
                "proposal_kind": "policy_tuning",
                "change_scope": ["src/quant_evo_nextgen/services/learning.py"],
                "expected_benefit": {"quarantine_precision_pct": 12.5},
                "evaluation_summary": {"baseline_false_positive_pct": 4.1},
                "risk_summary": "Could suppress useful but novel insights if tuned too aggressively.",
                "canary_plan": {"lane_type": "canary", "traffic_pct": 10},
                "rollback_plan": {"action": "restore_previous_thresholds"},
                "objective_drift_checks": ["owner_alignment", "strategy_quality"],
                "proposal_state": "ready_for_review",
                "created_by": "tester",
            },
        )
        assert proposal_response.status_code == 200
        proposal_id = proposal_response.json()["id"]

        canary_response = client.post(
            "/api/v1/evolution/canary-runs",
            json={
                "proposal_id": proposal_id,
                "lane_type": "canary",
                "environment": "paper",
                "traffic_pct": 10,
                "success_metrics": {"quarantine_precision_pct": 14.2},
                "objective_drift_score": 0.08,
                "objective_drift_summary": "No meaningful drift detected in the paper lane.",
                "rollback_ready": True,
                "status": "passed",
                "created_by": "tester",
            },
        )
        assert canary_response.status_code == 200

        promotion_response = client.post(
            "/api/v1/evolution/promotion-decisions",
            json={
                "proposal_id": proposal_id,
                "decision": "promoted",
                "rationale": "Canary lane improved precision without visible objective drift.",
                "decided_by": "tester",
                "decision_payload": {"environment": "paper", "next_step": "promote_to_default"},
            },
        )
        assert promotion_response.status_code == 200

        proposals_response = client.get("/api/v1/evolution/proposals")
        canary_runs_response = client.get("/api/v1/evolution/canary-runs")
        promotion_decisions_response = client.get("/api/v1/evolution/promotion-decisions")
        dashboard_response = client.get("/api/v1/dashboard/evolution")

        assert proposals_response.status_code == 200
        assert canary_runs_response.status_code == 200
        assert promotion_decisions_response.status_code == 200
        assert dashboard_response.status_code == 200

        proposals_payload = proposals_response.json()
        canary_runs_payload = canary_runs_response.json()
        promotion_decisions_payload = promotion_decisions_response.json()
        dashboard_payload = dashboard_response.json()

        assert proposals_payload[0]["id"] == proposal_id
        assert proposals_payload[0]["proposal_state"] == "promoted"
        assert canary_runs_payload[0]["proposal_id"] == proposal_id
        assert canary_runs_payload[0]["status"] == "passed"
        assert promotion_decisions_payload[0]["proposal_id"] == proposal_id
        assert promotion_decisions_payload[0]["decision"] == "promoted"
        assert dashboard_payload["metrics"]["proposal_count"] == 1
        assert dashboard_payload["metrics"]["ready_for_review_count"] == 0
        assert dashboard_payload["metrics"]["active_canary_count"] == 0
        assert dashboard_payload["metrics"]["promoted_count"] == 1
        assert dashboard_payload["metrics"]["rolled_back_count"] == 0
        assert len(dashboard_payload["capability_scorecards"]) == 5
        assert dashboard_payload["stall_state"] == "healthy"
        assert isinstance(dashboard_payload["capability_gaps"], list)
        assert dashboard_payload["recent_proposals"][0]["proposal_state"] == "promoted"
        assert dashboard_payload["recent_canary_runs"][0]["lane_type"] == "canary"
        assert dashboard_payload["recent_promotion_decisions"][0]["decision"] == "promoted"


def test_dashboard_api_routes_require_shared_token_when_configured(tmp_path: Path) -> None:
    _seed_repo_state(tmp_path)
    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'api-dashboard-token.db'}",
        db_bootstrap_on_start=True,
        dashboard_api_token="shared-token",
    )
    app = create_app(settings)

    with TestClient(app) as client:
        overview_response = client.get("/api/v1/dashboard/overview")
        doctor_response = client.get("/api/v1/system/doctor")
        health_response = client.get("/healthz")
        authorized_overview = client.get(
            "/api/v1/dashboard/overview",
            headers={"X-Quant-Evo-Dashboard-Token": "shared-token"},
        )

        assert overview_response.status_code == 401
        assert doctor_response.status_code == 401
        assert health_response.status_code == 200
        assert authorized_overview.status_code == 200


def test_api_exposes_learning_documents_and_insights_in_dashboard(tmp_path: Path) -> None:
    _seed_repo_state(tmp_path)
    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'api-learning.db'}",
        db_bootstrap_on_start=True,
    )
    app = create_app(settings)

    with TestClient(app) as client:
        with client.app.state.database.session_scope() as session:
            document = DocumentModel(
                source_key="research-intake",
                source_type="codex-research",
                title="Durable research note",
                summary="Collected cited material about relay reliability and memory safety.",
                citations_json=[
                    "https://provider.example.com/reliability",
                    "https://safety.example.org/learning",
                ],
                followup_tasks=["Promote only after review."],
                risks_found=["Needs human review before principle promotion."],
                ingested_at=datetime.now(tz=UTC),
                created_by="test",
                origin_type="test",
                origin_id="api-learning",
                status="distilled",
                confidence=0.84,
            )
            session.add(document)
            session.flush()
            session.add(
                EvidenceItemModel(
                    document_id=document.id,
                    evidence_type="external_citation",
                    claim_text=document.summary,
                    citation_ref="https://provider.example.com/reliability",
                    topic="research-intake",
                    recorded_at=datetime.now(tz=UTC),
                    created_by="test",
                    origin_type="test",
                    origin_id=document.id,
                    status="linked",
                    confidence=0.84,
                )
            )
            session.add(
                EvidenceItemModel(
                    document_id=document.id,
                    evidence_type="external_citation",
                    claim_text=document.summary,
                    citation_ref="https://safety.example.org/learning",
                    topic="research-intake",
                    recorded_at=datetime.now(tz=UTC),
                    created_by="test",
                    origin_type="test",
                    origin_id=document.id,
                    status="linked",
                    confidence=0.84,
                )
            )
            session.add(
                InsightModel(
                    document_id=document.id,
                    topic_key="research-intake",
                    title="Relay reliability needs continuous revalidation",
                    summary="Provider stability and learning safety both need continuous checks.",
                    supporting_evidence_refs=["evidence-1", "evidence-2"],
                    citation_refs=[
                        "https://provider.example.com/reliability",
                        "https://safety.example.org/learning",
                    ],
                    challenge_notes=["Needs review before promotion."],
                    followup_tasks=["Validate with another source."],
                    promotion_state="ready_for_review",
                    recorded_at=datetime.now(tz=UTC),
                    last_validated_at=datetime.now(tz=UTC),
                    created_by="test",
                    origin_type="test",
                    origin_id=document.id,
                    status="candidate",
                    confidence=0.84,
                )
            )

        dashboard_learning_response = client.get("/api/v1/dashboard/learning")
        learning_documents_response = client.get("/api/v1/learning/documents")
        learning_insights_response = client.get("/api/v1/learning/insights")

        assert dashboard_learning_response.status_code == 200
        assert learning_documents_response.status_code == 200
        assert learning_insights_response.status_code == 200

        dashboard_learning_payload = dashboard_learning_response.json()
        learning_documents_payload = learning_documents_response.json()
        learning_insights_payload = learning_insights_response.json()

        assert dashboard_learning_payload["metrics"]["document_count"] == 1
        assert dashboard_learning_payload["metrics"]["insight_count"] == 1
        assert dashboard_learning_payload["metrics"]["ready_insight_count"] == 1
        assert dashboard_learning_payload["metrics"]["quarantined_insight_count"] == 0
        assert dashboard_learning_payload["recent_documents"][0]["title"] == "Durable research note"
        assert dashboard_learning_payload["recent_documents"][0]["status"] == "distilled"
        assert dashboard_learning_payload["recent_documents"][0]["source_key"] == "research-intake"
        assert dashboard_learning_payload["recent_insights"][0]["promotion_state"] == "ready_for_review"
        assert dashboard_learning_payload["recent_insights"][0]["topic_key"] == "research-intake"
        assert dashboard_learning_payload["recent_insights"][0]["document_id"] == document.id
        assert learning_documents_payload[0]["status"] == "distilled"
        assert learning_insights_payload[0]["status"] == "candidate"


def test_api_exposes_strategy_lab_lifecycle_and_trading_dashboard(tmp_path: Path) -> None:
    _seed_repo_state(tmp_path)
    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'api-strategy.db'}",
        db_bootstrap_on_start=True,
    )
    app = create_app(settings)

    with TestClient(app) as client:
        hypothesis_response = client.post(
            "/api/v1/strategy/hypotheses",
            json={
                "title": "Mean reversion after volatility spike",
                "thesis": "Short-term dislocation reverts when volatility cools.",
                "target_market": "crypto-perps",
                "mechanism": "Fade exhaustion after volatility spike with bounded risk.",
                "evaluation_plan": ["Backtest on high-vol regime slices.", "Run paper monitoring for 14 days."],
                "invalidation_conditions": ["Drawdown breach", "Sharpe below floor"],
                "created_by": "tester",
            },
        )
        assert hypothesis_response.status_code == 200
        hypothesis_id = hypothesis_response.json()["id"]

        spec_response = client.post(
            "/api/v1/strategy/specs",
            json={
                "hypothesis_id": hypothesis_id,
                "spec_code": "mr-vol-001",
                "version_label": "v1",
                "title": "Volatility spike mean reversion",
                "target_market": "crypto-perps",
                "signal_logic": "Enter against the spike after momentum exhaustion confirms.",
                "risk_rules": {"max_position_pct": 0.02, "stop_loss_pct": 0.01},
                "data_requirements": ["ohlcv", "funding", "open interest"],
                "invalidation_conditions": ["Regime shift"],
                "execution_constraints": {"market_hours": "24x7"},
                "created_by": "tester",
            },
        )
        assert spec_response.status_code == 200
        spec_id = spec_response.json()["id"]

        backtest_response = client.post(
            "/api/v1/strategy/backtests",
            json={
                "strategy_spec_id": spec_id,
                "dataset_range": "2024-01-01..2025-12-31",
                "sample_size": 240,
                "metrics_json": {
                    "sharpe_ratio": 1.42,
                    "total_return_pct": 18.6,
                    "max_drawdown_pct": 9.4,
                },
                "artifact_path": "artifacts/backtests/mr-vol-001.html",
                "created_by": "tester",
            },
        )
        assert backtest_response.status_code == 200
        assert backtest_response.json()["gate_result"] == "passed"

        paper_run_response = client.post(
            "/api/v1/strategy/paper-runs",
            json={
                "strategy_spec_id": spec_id,
                "deployment_label": "paper-alpha",
                "monitoring_days": 14,
                "metrics_json": {
                    "net_pnl_pct": 4.2,
                    "profit_factor": 1.19,
                    "max_drawdown_pct": 4.7,
                },
                "capital_allocated": 5000,
                "created_by": "tester",
            },
        )
        assert paper_run_response.status_code == 200
        paper_run_id = paper_run_response.json()["id"]
        assert paper_run_response.json()["gate_result"] == "ready_for_live_review"

        promotion_response = client.post(
            "/api/v1/strategy/promotion-decisions",
            json={
                "strategy_spec_id": spec_id,
                "paper_run_id": paper_run_id,
                "target_stage": "production",
                "decision": "approved",
                "rationale": "Backtest and paper gates both passed with acceptable drawdown.",
                "decided_by": "tester",
            },
        )
        assert promotion_response.status_code == 200

        trading_response = client.get("/api/v1/dashboard/trading")
        specs_response = client.get("/api/v1/strategy/specs")
        backtests_response = client.get("/api/v1/strategy/backtests")
        paper_runs_response = client.get("/api/v1/strategy/paper-runs")
        promotions_response = client.get("/api/v1/strategy/promotion-decisions")

        assert trading_response.status_code == 200
        assert specs_response.status_code == 200
        assert backtests_response.status_code == 200
        assert paper_runs_response.status_code == 200
        assert promotions_response.status_code == 200

        trading_payload = trading_response.json()
        specs_payload = specs_response.json()
        backtests_payload = backtests_response.json()
        paper_runs_payload = paper_runs_response.json()
        promotions_payload = promotions_response.json()

        assert trading_payload["strategy_lab"]["hypothesis_count"] == 1
        assert trading_payload["strategy_lab"]["spec_count"] == 1
        assert trading_payload["strategy_lab"]["production_count"] == 1
        assert trading_payload["recent_specs"][0]["spec_code"] == "mr-vol-001"
        assert trading_payload["recent_specs"][0]["current_stage"] == "production"
        assert trading_payload["recent_backtests"][0]["gate_result"] == "passed"
        assert trading_payload["recent_paper_runs"][0]["gate_result"] == "ready_for_live_review"
        assert specs_payload[0]["current_stage"] == "production"
        assert backtests_payload[0]["sample_size"] == 240
        assert paper_runs_payload[0]["deployment_label"] == "paper-alpha"
        assert promotions_payload[0]["decision"] == "approved"


def test_api_exposes_execution_readiness_and_trading_dashboard(tmp_path: Path) -> None:
    _seed_repo_state(tmp_path)
    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'api-execution.db'}",
        db_bootstrap_on_start=True,
        market_calendar="XNYS",
        market_timezone="America/New_York",
    )
    app = create_app(settings)

    with TestClient(app) as client:
        hypothesis_response = client.post(
            "/api/v1/strategy/hypotheses",
            json={
                "title": "Execution readiness baseline",
                "thesis": "Trading readiness should require a production strategy.",
                "target_market": "us-equities",
                "mechanism": "Promote a bounded strategy so readiness can be evaluated honestly.",
                "created_by": "tester",
            },
        )
        hypothesis_id = hypothesis_response.json()["id"]

        spec_response = client.post(
            "/api/v1/strategy/specs",
            json={
                "hypothesis_id": hypothesis_id,
                "spec_code": "exec-ready-001",
                "title": "Execution readiness baseline",
                "target_market": "us-equities",
                "signal_logic": "Bounded signal path for readiness testing.",
                "created_by": "tester",
            },
        )
        spec_id = spec_response.json()["id"]

        promotion_response = client.post(
            "/api/v1/strategy/promotion-decisions",
            json={
                "strategy_spec_id": spec_id,
                "target_stage": "production",
                "decision": "approved",
                "rationale": "Promoted for execution-readiness validation.",
                "decided_by": "tester",
            },
        )
        assert promotion_response.status_code == 200

        session_response = client.post(
            "/api/v1/execution/market-sessions",
            json={
                "market_calendar": "XNYS",
                "market_timezone": "America/New_York",
                "session_label": "regular",
                "is_market_open": True,
                "trading_allowed": True,
                "created_by": "tester",
            },
        )
        assert session_response.status_code == 200

        snapshot_response = client.post(
            "/api/v1/execution/account-snapshots",
            json={
                "provider_key": "alpaca-paper",
                "account_ref": "paper-main",
                "environment": "paper",
                "equity": 10100,
                "cash": 6500,
                "buying_power": 18000,
                "gross_exposure": 3200,
                "net_exposure": 2500,
                "positions_count": 2,
                "open_orders_count": 1,
                "created_by": "tester",
            },
        )
        assert snapshot_response.status_code == 200
        snapshot_id = snapshot_response.json()["id"]

        reconciliation_response = client.post(
            "/api/v1/execution/reconciliation-runs",
            json={
                "provider_key": "alpaca-paper",
                "account_ref": "paper-main",
                "account_snapshot_id": snapshot_id,
                "environment": "paper",
                "internal_equity": 10099,
                "internal_positions_count": 2,
                "internal_open_orders_count": 1,
                "created_by": "tester",
            },
        )
        assert reconciliation_response.status_code == 200

        readiness_response = client.get("/api/v1/execution/readiness")
        trading_response = client.get("/api/v1/dashboard/trading")

        assert readiness_response.status_code == 200
        assert trading_response.status_code == 200

        readiness_payload = readiness_response.json()
        trading_payload = trading_response.json()

        assert readiness_payload["status"] == "ready"
        assert readiness_payload["trading_allowed"] is True
        assert trading_payload["execution_readiness"]["status"] == "ready"
        assert trading_payload["latest_account_snapshot"]["provider_key"] == "alpaca-paper"
        assert trading_payload["latest_reconciliation"]["status"] == "matched"
        assert trading_payload["recent_market_sessions"][0]["session_label"] == "regular"


def test_api_submits_order_intent_and_exposes_order_path_in_trading_dashboard(tmp_path: Path) -> None:
    _seed_repo_state(tmp_path)
    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'api-order-path.db'}",
        db_bootstrap_on_start=True,
        market_calendar="CRYPTO_24X7",
        market_timezone="UTC",
        default_broker_provider_key="paper-sim",
        default_broker_account_ref="paper-main",
    )
    app = create_app(settings)

    with TestClient(app) as client:
        hypothesis_id = client.post(
            "/api/v1/strategy/hypotheses",
            json={
                "title": "Paper execution path",
                "thesis": "A production strategy is needed before paper orders can be simulated safely.",
                "target_market": "us-equities",
                "mechanism": "Use paper adapter to validate durable order lineage.",
                "created_by": "tester",
            },
        ).json()["id"]

        spec_id = client.post(
            "/api/v1/strategy/specs",
            json={
                "hypothesis_id": hypothesis_id,
                "spec_code": "paper-order-001",
                "title": "Paper execution path",
                "target_market": "us-equities",
                "signal_logic": "Bounded paper execution path.",
                "created_by": "tester",
            },
        ).json()["id"]

        client.post(
            "/api/v1/strategy/promotion-decisions",
            json={
                "strategy_spec_id": spec_id,
                "target_stage": "production",
                "decision": "approved",
                "rationale": "Promoted for order-path validation.",
                "decided_by": "tester",
            },
        )

        client.post(
            "/api/v1/execution/market-sessions",
            json={
                "market_calendar": "CRYPTO_24X7",
                "market_timezone": "UTC",
                "session_label": "continuous",
                "is_market_open": True,
                "trading_allowed": True,
                "created_by": "tester",
            },
        )

        snapshot_id = client.post(
            "/api/v1/execution/account-snapshots",
            json={
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "equity": 10000,
                "cash": 10000,
                "buying_power": 10000,
                "gross_exposure": 0,
                "net_exposure": 0,
                "positions_count": 0,
                "open_orders_count": 0,
                "created_by": "tester",
            },
        ).json()["id"]

        client.post(
            "/api/v1/execution/reconciliation-runs",
            json={
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "account_snapshot_id": snapshot_id,
                "environment": "paper",
                "internal_equity": 10000,
                "internal_positions_count": 0,
                "internal_open_orders_count": 0,
                "created_by": "tester",
            },
        )

        order_intent_response = client.post(
            "/api/v1/execution/order-intents",
            json={
                "strategy_spec_id": spec_id,
                "symbol": "AAPL",
                "side": "buy",
                "quantity": 4,
                "reference_price": 120,
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "created_by": "tester",
            },
        )
        order_records_response = client.get("/api/v1/execution/order-records")
        positions_response = client.get("/api/v1/execution/positions")
        trading_response = client.get("/api/v1/dashboard/trading")

        assert order_intent_response.status_code == 200
        assert order_records_response.status_code == 200
        assert positions_response.status_code == 200
        assert trading_response.status_code == 200

        order_intent_payload = order_intent_response.json()
        order_records_payload = order_records_response.json()
        positions_payload = positions_response.json()
        trading_payload = trading_response.json()

        assert order_intent_payload["status"] == "filled"
        assert order_records_payload[0]["symbol"] == "AAPL"
        assert positions_payload[0]["symbol"] == "AAPL"
        assert trading_payload["allocation_policy"]["policy_key"] == "paper-default"
        assert trading_payload["recent_order_intents"][0]["symbol"] == "AAPL"
        assert trading_payload["recent_order_records"][0]["broker_order_id"].startswith("paper-")
        assert trading_payload["active_positions"][0]["quantity"] == 4


def test_api_exposes_broker_sync_cancel_and_replace_paths(tmp_path: Path) -> None:
    _seed_repo_state(tmp_path)
    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'api-external-execution.db'}",
        db_bootstrap_on_start=True,
        market_calendar="CRYPTO_24X7",
        market_timezone="UTC",
        default_broker_provider_key="scripted-broker",
        default_broker_account_ref="paper-main",
    )
    app = create_app(settings)

    with TestClient(app) as client:
        adapter = ScriptedAsyncBrokerAdapter()
        client.app.state.execution_service.adapters["scripted_async"] = adapter

        hypothesis_id = client.post(
            "/api/v1/strategy/hypotheses",
            json={
                "title": "Async execution path",
                "thesis": "External-style broker paths need durable sync and replace lineage.",
                "target_market": "us-equities",
                "mechanism": "Asynchronous broker acceptance followed by sync recovery.",
                "created_by": "tester",
            },
        ).json()["id"]

        spec_id = client.post(
            "/api/v1/strategy/specs",
            json={
                "hypothesis_id": hypothesis_id,
                "spec_code": "async-order-001",
                "title": "Async execution path",
                "target_market": "us-equities",
                "signal_logic": "Validate sync, cancel, and replace flows.",
                "created_by": "tester",
            },
        ).json()["id"]

        client.post(
            "/api/v1/strategy/promotion-decisions",
            json={
                "strategy_spec_id": spec_id,
                "target_stage": "production",
                "decision": "approved",
                "rationale": "Promoted for external-path validation.",
                "decided_by": "tester",
            },
        )

        client.post(
            "/api/v1/execution/market-sessions",
            json={
                "market_calendar": "CRYPTO_24X7",
                "market_timezone": "UTC",
                "session_label": "continuous",
                "is_market_open": True,
                "trading_allowed": True,
                "created_by": "tester",
            },
        )

        snapshot_id = client.post(
            "/api/v1/execution/account-snapshots",
            json={
                "provider_key": "scripted-broker",
                "account_ref": "paper-main",
                "environment": "paper",
                "equity": 10000,
                "cash": 10000,
                "buying_power": 10000,
                "gross_exposure": 0,
                "net_exposure": 0,
                "positions_count": 0,
                "open_orders_count": 0,
                "created_by": "tester",
            },
        ).json()["id"]

        client.post(
            "/api/v1/execution/reconciliation-runs",
            json={
                "provider_key": "scripted-broker",
                "account_ref": "paper-main",
                "account_snapshot_id": snapshot_id,
                "environment": "paper",
                "internal_equity": 10000,
                "internal_positions_count": 0,
                "internal_open_orders_count": 0,
                "created_by": "tester",
            },
        )

        first_intent = client.post(
            "/api/v1/execution/order-intents",
            json={
                "strategy_spec_id": spec_id,
                "symbol": "AAPL",
                "side": "buy",
                "quantity": 2,
                "reference_price": 100,
                "provider_key": "scripted-broker",
                "account_ref": "paper-main",
                "environment": "paper",
                "broker_adapter": "scripted_async",
                "created_by": "tester",
            },
        )
        first_order_id = client.get("/api/v1/execution/order-records").json()[0]["id"]
        cancel_response = client.post(
            f"/api/v1/execution/order-records/{first_order_id}/cancel",
            json={"reason": "cancel stale quote", "created_by": "tester"},
        )

        second_intent = client.post(
            "/api/v1/execution/order-intents",
            json={
                "strategy_spec_id": spec_id,
                "symbol": "MSFT",
                "side": "buy",
                "quantity": 2,
                "reference_price": 90,
                "provider_key": "scripted-broker",
                "account_ref": "paper-main",
                "environment": "paper",
                "broker_adapter": "scripted_async",
                "created_by": "tester",
            },
        )
        replace_source_id = client.get("/api/v1/execution/order-records").json()[0]["id"]
        replace_response = client.post(
            f"/api/v1/execution/order-records/{replace_source_id}/replace",
            json={
                "quantity": 3,
                "reference_price": 95,
                "limit_price": 94.5,
                "time_in_force": "gtc",
                "created_by": "tester",
            },
        )

        replacement_broker_order_id = replace_response.json()["broker_order_id"]
        adapter.fill_order(replacement_broker_order_id, 95.0)
        sync_response = client.post(
            "/api/v1/execution/broker-sync-runs",
            json={
                "provider_key": "scripted-broker",
                "account_ref": "paper-main",
                "environment": "paper",
                "broker_adapter": "scripted_async",
                "created_by": "tester",
            },
        )
        trading_response = client.get("/api/v1/dashboard/trading")

        assert first_intent.status_code == 200
        assert cancel_response.status_code == 200
        assert second_intent.status_code == 200
        assert replace_response.status_code == 200
        assert sync_response.status_code == 200
        assert trading_response.status_code == 200

        cancel_payload = cancel_response.json()
        replace_payload = replace_response.json()
        sync_payload = sync_response.json()
        trading_payload = trading_response.json()

        assert cancel_payload["status"] == "canceled"
        assert replace_payload["status"] == "submitted"
        assert replace_payload["parent_order_record_id"] == replace_source_id
        assert sync_payload["status"] == "synchronized"
        assert trading_payload["latest_broker_sync"]["broker_adapter"] == "scripted_async"
        assert trading_payload["active_positions"][0]["symbol"] == "MSFT"
        assert trading_payload["recent_order_records"][0]["status"] == "filled"


def test_api_exposes_instrument_and_broker_capability_registries(tmp_path: Path) -> None:
    database_path = tmp_path / "api-instrument-capability.db"
    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{database_path}",
        db_bootstrap_on_start=True,
    )
    _seed_repo_state(tmp_path)

    app = create_app(settings)
    with TestClient(app) as client:
        instrument_response = client.post(
            "/api/v1/execution/instruments",
            json={
                "symbol": "AAPL240619C00200000",
                "instrument_type": "option",
                "underlying_symbol": "AAPL",
                "option_right": "call",
                "option_style": "american",
                "expiration_date": "2026-06-19",
                "strike_price": 200.0,
                "contract_multiplier": 100.0,
                "created_by": "tester",
            },
        )
        capability_response = client.post(
            "/api/v1/execution/broker-capabilities",
            json={
                "capability_key": "alpaca-paper:alpaca:paper",
                "provider_key": "alpaca-paper",
                "broker_adapter": "alpaca",
                "account_ref": "paper-main",
                "environment": "paper",
                "account_mode": "margin",
                "supports_equities": True,
                "supports_etfs": True,
                "supports_fractional": True,
                "supports_short": True,
                "supports_margin": True,
                "supports_options": True,
                "supports_multi_leg_options": True,
                "supports_option_exercise": True,
                "supports_option_assignment_events": True,
                "supports_live_trading": False,
                "supports_paper_trading": True,
                "created_by": "tester",
            },
        )
        instruments_response = client.get("/api/v1/execution/instruments")
        capabilities_response = client.get("/api/v1/execution/broker-capabilities")

        assert instrument_response.status_code == 200
        assert capability_response.status_code == 200
        assert instruments_response.status_code == 200
        assert capabilities_response.status_code == 200

        instrument_payload = instrument_response.json()
        capability_payload = capability_response.json()

        assert instrument_payload["instrument_type"] == "option"
        assert instrument_payload["instrument_key"].startswith("option:AAPL:2026-06-19:call:")
        assert capability_payload["supports_options"] is True
        assert capability_payload["supports_short"] is True
        assert any(item["symbol"] == "AAPL240619C00200000" for item in instruments_response.json())
        assert any(item["capability_key"] == "alpaca-paper:alpaca:paper" for item in capabilities_response.json())


def test_api_exposes_option_event_feed_and_dashboard_option_visibility(tmp_path: Path) -> None:
    _seed_repo_state(tmp_path)
    settings = Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'api-option-events.db'}",
        db_bootstrap_on_start=True,
        market_calendar="CRYPTO_24X7",
        market_timezone="UTC",
        default_broker_provider_key="paper-sim",
        default_broker_account_ref="paper-main",
    )
    app = create_app(settings)
    expiry_date = (datetime.now(tz=UTC) + timedelta(days=7)).date().isoformat()

    with TestClient(app) as client:
        hypothesis_id = client.post(
            "/api/v1/strategy/hypotheses",
            json={
                "title": "Option event visibility",
                "thesis": "Expiring options and lifecycle events must be visible before VPS deployment.",
                "target_market": "us-options",
                "mechanism": "Drive option position state and option event state through the API surface.",
                "created_by": "tester",
            },
        ).json()["id"]
        spec_id = client.post(
            "/api/v1/strategy/specs",
            json={
                "hypothesis_id": hypothesis_id,
                "spec_code": "paper-option-visibility-001",
                "title": "Option visibility path",
                "target_market": "us-options",
                "signal_logic": "Expose expiring options and lifecycle events.",
                "created_by": "tester",
            },
        ).json()["id"]
        client.post(
            "/api/v1/strategy/promotion-decisions",
            json={
                "strategy_spec_id": spec_id,
                "target_stage": "production",
                "decision": "approved",
                "rationale": "Promoted for option dashboard validation.",
                "decided_by": "tester",
            },
        )
        client.post(
            "/api/v1/execution/market-sessions",
            json={
                "market_calendar": "CRYPTO_24X7",
                "market_timezone": "UTC",
                "session_label": "continuous",
                "is_market_open": True,
                "trading_allowed": True,
                "created_by": "tester",
            },
        )
        snapshot_id = client.post(
            "/api/v1/execution/account-snapshots",
            json={
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "equity": 10000,
                "cash": 10000,
                "buying_power": 10000,
                "gross_exposure": 0,
                "net_exposure": 0,
                "positions_count": 0,
                "open_orders_count": 0,
                "created_by": "tester",
            },
        ).json()["id"]
        client.post(
            "/api/v1/execution/reconciliation-runs",
            json={
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "account_snapshot_id": snapshot_id,
                "environment": "paper",
                "internal_equity": 10000,
                "internal_positions_count": 0,
                "internal_open_orders_count": 0,
                "created_by": "tester",
            },
        )
        client.post(
            "/api/v1/execution/allocation-policies",
            json={
                "policy_key": "paper-option-visibility",
                "environment": "paper",
                "scope": "global",
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "max_strategy_notional_pct": 2.0,
                "max_gross_exposure_pct": 2.0,
                "max_open_positions": 8,
                "max_open_orders": 8,
                "created_by": "tester",
            },
        )
        client.post(
            "/api/v1/execution/broker-capabilities",
            json={
                "capability_key": "paper-sim:paper_sim:paper",
                "provider_key": "paper-sim",
                "broker_adapter": "paper_sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "account_mode": "paper",
                "supports_options": True,
                "supports_paper_trading": True,
                "created_by": "tester",
            },
        )
        instrument_payload = client.post(
            "/api/v1/execution/instruments",
            json={
                "symbol": "AAPL260619C00200000",
                "instrument_type": "option",
                "underlying_symbol": "AAPL",
                "option_right": "call",
                "option_style": "american",
                "expiration_date": expiry_date,
                "strike_price": 200.0,
                "contract_multiplier": 100.0,
                "created_by": "tester",
            },
        ).json()
        order_intent_response = client.post(
            "/api/v1/execution/order-intents",
            json={
                "strategy_spec_id": spec_id,
                "symbol": instrument_payload["symbol"],
                "side": "buy",
                "quantity": 1,
                "reference_price": 5.0,
                "instrument_id": instrument_payload["id"],
                "asset_type": "option",
                "position_effect": "open",
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "allocation_policy_key": "paper-option-visibility",
                "created_by": "tester",
            },
        )
        trading_response = client.get("/api/v1/dashboard/trading")
        position_id = client.get("/api/v1/execution/positions").json()[0]["id"]
        option_event_response = client.post(
            "/api/v1/execution/option-events",
            json={
                "event_type": "assignment",
                "provider_key": "paper-sim",
                "account_ref": "paper-main",
                "environment": "paper",
                "symbol": instrument_payload["symbol"],
                "position_id": position_id,
                "instrument_id": instrument_payload["id"],
                "notes": "Manual review path",
                "created_by": "tester",
            },
        )
        option_events_response = client.get("/api/v1/execution/option-events")
        trading_after_event = client.get("/api/v1/dashboard/trading")

        assert order_intent_response.status_code == 200
        assert trading_response.status_code == 200
        assert option_event_response.status_code == 200
        assert option_events_response.status_code == 200
        assert trading_after_event.status_code == 200

        trading_payload = trading_response.json()
        event_payload = option_event_response.json()
        events_payload = option_events_response.json()
        trading_event_payload = trading_after_event.json()

        assert trading_payload["expiring_option_positions"][0]["symbol"] == instrument_payload["symbol"]
        assert trading_payload["active_positions"][0]["asset_type"] == "option"
        assert event_payload["review_required"] is True
        assert events_payload[0]["event_type"] == "assignment"
        assert trading_event_payload["recent_option_events"][0]["event_type"] == "assignment"
        assert trading_event_payload["recent_option_events"][0]["review_required"] is True


def _seed_repo_state(repo_root: Path) -> None:
    (repo_root / "strategies" / "candidates").mkdir(parents=True)
    (repo_root / "strategies" / "staging").mkdir(parents=True)
    (repo_root / "strategies" / "production").mkdir(parents=True)
    (repo_root / "memory" / "principles").mkdir(parents=True)
    (repo_root / "memory" / "causal").mkdir(parents=True)
    (repo_root / "evo").mkdir(parents=True)

    (repo_root / "strategies" / "candidates" / "candidate.py").write_text("print('x')", encoding="utf-8")
    (repo_root / "strategies" / "production" / "prod.py").write_text("print('x')", encoding="utf-8")
    (repo_root / "memory" / "principles" / "alpha.md").write_text("alpha", encoding="utf-8")
    (repo_root / "memory" / "causal" / "beta.md").write_text("beta", encoding="utf-8")
    (repo_root / "evo" / "feature_map.json").write_text(
        json.dumps({"stats": {"occupied_cells": 4, "coverage_pct": 0.2, "total_generations": 9}}),
        encoding="utf-8",
    )
