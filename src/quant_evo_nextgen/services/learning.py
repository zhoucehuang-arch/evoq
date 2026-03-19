from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable, Sequence
from urllib.parse import urlparse

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from quant_evo_nextgen.contracts.state import LearningDocumentSummary, LearningInsightSummary
from quant_evo_nextgen.db.models import (
    CodexAttemptModel,
    CodexRunModel,
    DocumentModel,
    EvidenceItemModel,
    InsightModel,
    SourceHealthModel,
)


_QUARANTINE_KEYWORDS = (
    "prompt injection",
    "system prompt",
    "ignore previous",
    "jailbreak",
    "credential",
    "secret leak",
    "exfiltrate",
    "malware",
    "affiliate spam",
    "poisoned",
)


@dataclass(slots=True)
class LearningIngestResult:
    codex_run_id: str
    status: str
    document_id: str | None = None
    evidence_count: int = 0
    reason: str | None = None


@dataclass(slots=True)
class LearningSynthesisResult:
    document_id: str
    status: str
    insight_id: str | None = None
    promotion_state: str | None = None
    quarantine_reason: str | None = None


@dataclass(slots=True)
class LearningMeshMetrics:
    document_count: int
    insight_count: int
    ready_insight_count: int
    quarantined_insight_count: int


class LearningService:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self.session_factory = session_factory

    def ingest_completed_research_runs(self, *, limit: int = 5) -> list[LearningIngestResult]:
        with self.session_factory() as session:
            query = (
                select(CodexRunModel)
                .outerjoin(DocumentModel, DocumentModel.codex_run_id == CodexRunModel.id)
                .where(
                    CodexRunModel.supervisor_loop_key == "research-intake",
                    CodexRunModel.status == "completed",
                    DocumentModel.id.is_(None),
                )
                .order_by(CodexRunModel.completed_at.asc(), CodexRunModel.queued_at.asc())
                .limit(limit)
            )
            runs = session.scalars(query).all()
            results: list[LearningIngestResult] = []
            for run in runs:
                structured = self._merged_structured_output(session, run)
                if structured is None:
                    results.append(
                        LearningIngestResult(
                            codex_run_id=run.id,
                            status="skipped",
                            reason="Completed research run has no structured output.",
                        )
                    )
                    continue

                citations = [str(item) for item in structured.get("citations") or []]
                citation_source_keys = self._ensure_citation_sources(session, citations)
                followup_tasks = [str(item) for item in structured.get("followup_tasks") or []]
                risks_found = [str(item) for item in structured.get("risks_found") or []]
                confidence = self._coerce_confidence(structured.get("confidence"))
                summary = str(structured.get("summary") or run.objective)
                preferred_storage_path = structured.get("preferred_stdout_path") or (run.result_payload or {}).get(
                    "stdout_path"
                )
                document = DocumentModel(
                    codex_run_id=run.id,
                    workflow_run_id=run.workflow_run_id,
                    supervisor_loop_key=run.supervisor_loop_key,
                    source_key=citation_source_keys[0] if citation_source_keys else "research-intake",
                    source_type=self._source_type_for_key(citation_source_keys[0]) if citation_source_keys else "codex-research",
                    title=self._title_for_run(run.objective),
                    summary=summary,
                    storage_path=str(preferred_storage_path) if preferred_storage_path else None,
                    citations_json=citations,
                    followup_tasks=followup_tasks,
                    risks_found=risks_found,
                    ingested_at=datetime.now(tz=UTC),
                    created_by="learning-service",
                    origin_type="codex-run",
                    origin_id=run.id,
                    status="ingested",
                    confidence=confidence,
                    tags=self._coalesce_unique_strings(
                        ([f"supervisor-loop:{run.supervisor_loop_key}"] if run.supervisor_loop_key else [])
                        + [f"source:{source_key}" for source_key in citation_source_keys]
                    ),
                )
                session.add(document)
                session.flush()

                evidence_count = 0
                for citation in citations:
                    session.add(
                        EvidenceItemModel(
                            document_id=document.id,
                            codex_run_id=run.id,
                            evidence_type="external_citation",
                            claim_text=summary,
                            citation_ref=citation,
                            topic="research-intake",
                            recorded_at=datetime.now(tz=UTC),
                            created_by="learning-service",
                            origin_type="codex-run",
                            origin_id=run.id,
                            status="candidate",
                            confidence=confidence,
                        )
                    )
                    evidence_count += 1

                run.result_payload = {
                    **run.result_payload,
                    "learning_document_id": document.id,
                    "learning_evidence_count": evidence_count,
                    "learning_ingested_at": datetime.now(tz=UTC).isoformat(),
                }
                results.append(
                    LearningIngestResult(
                        codex_run_id=run.id,
                        status="ingested",
                        document_id=document.id,
                        evidence_count=evidence_count,
                    )
                )

            session.commit()
            return results

    def synthesize_pending_insights(self, *, limit: int = 5) -> list[LearningSynthesisResult]:
        with self.session_factory() as session:
            query = (
                select(DocumentModel)
                .outerjoin(InsightModel, InsightModel.document_id == DocumentModel.id)
                .where(
                    DocumentModel.status.in_(("ingested", "resynthesis_pending")),
                    or_(InsightModel.id.is_(None), DocumentModel.status == "resynthesis_pending"),
                )
                .order_by(DocumentModel.ingested_at.asc(), DocumentModel.created_at.asc())
                .limit(limit)
            )
            documents = session.scalars(query).all()
            results: list[LearningSynthesisResult] = []

            for document in documents:
                evidence_items = session.scalars(
                    select(EvidenceItemModel)
                    .where(EvidenceItemModel.document_id == document.id)
                    .order_by(EvidenceItemModel.recorded_at.asc(), EvidenceItemModel.created_at.asc())
                ).all()
                citations = self._coalesce_unique_strings(
                    [item.citation_ref for item in evidence_items if item.citation_ref] + list(document.citations_json)
                )
                source_health = self._load_source_health_for_citations(session, citations)
                topic_key = self._topic_for_document(document, evidence_items)
                challenge_notes = self._coalesce_unique_strings(
                    list(document.risks_found) + list(document.followup_tasks)
                )
                quarantine_reason = self._detect_quarantine_reason(
                    document,
                    citations,
                    challenge_notes,
                    source_health,
                )
                promotion_state = self._promotion_state(
                    confidence=document.confidence,
                    evidence_count=len(evidence_items),
                    citations=citations,
                    source_health=source_health,
                    quarantine_reason=quarantine_reason,
                )
                insight_status = "quarantined" if quarantine_reason else "candidate"
                recorded_at = datetime.now(tz=UTC)
                insight = session.scalar(select(InsightModel).where(InsightModel.document_id == document.id))
                if insight is None:
                    insight = InsightModel(
                        document_id=document.id,
                        codex_run_id=document.codex_run_id,
                        workflow_run_id=document.workflow_run_id,
                        supervisor_loop_key=document.supervisor_loop_key,
                        topic_key=topic_key,
                        title=self._title_for_run(document.title),
                        summary=document.summary,
                        supporting_evidence_refs=[item.id for item in evidence_items],
                        citation_refs=citations,
                        challenge_notes=challenge_notes,
                        followup_tasks=list(document.followup_tasks),
                        promotion_state=promotion_state,
                        quarantine_reason=quarantine_reason,
                        recorded_at=recorded_at,
                        last_validated_at=None if quarantine_reason else recorded_at,
                        created_by="learning-service",
                        origin_type="document",
                        origin_id=document.id,
                        status=insight_status,
                        confidence=document.confidence,
                        tags=self._coalesce_unique_strings(
                            list(document.tags)
                            + [f"topic:{topic_key}", f"promotion:{promotion_state}"]
                            + [f"source:{source.source_key}" for source in source_health]
                        ),
                    )
                    session.add(insight)
                    session.flush()
                else:
                    insight.codex_run_id = document.codex_run_id
                    insight.workflow_run_id = document.workflow_run_id
                    insight.supervisor_loop_key = document.supervisor_loop_key
                    insight.topic_key = topic_key
                    insight.title = self._title_for_run(document.title)
                    insight.summary = document.summary
                    insight.supporting_evidence_refs = [item.id for item in evidence_items]
                    insight.citation_refs = citations
                    insight.challenge_notes = challenge_notes
                    insight.followup_tasks = list(document.followup_tasks)
                    insight.promotion_state = promotion_state
                    insight.quarantine_reason = quarantine_reason
                    insight.recorded_at = recorded_at
                    insight.last_validated_at = None if quarantine_reason else recorded_at
                    insight.status = insight_status
                    insight.confidence = document.confidence
                    insight.tags = self._coalesce_unique_strings(
                        list(insight.tags)
                        + list(document.tags)
                        + [f"topic:{topic_key}", f"promotion:{promotion_state}"]
                        + [f"source:{source.source_key}" for source in source_health]
                    )

                document.status = "quarantined" if quarantine_reason else "distilled"
                document.tags = self._coalesce_unique_strings(
                    list(document.tags) + [f"topic:{topic_key}", f"insight:{insight.id}"]
                )
                for evidence in evidence_items:
                    evidence.status = "quarantined" if quarantine_reason else "linked"
                    evidence.tags = self._coalesce_unique_strings(
                        list(evidence.tags) + [f"insight:{insight.id}", f"topic:{topic_key}"]
                    )

                if document.codex_run_id:
                    codex_run = session.get(CodexRunModel, document.codex_run_id)
                    if codex_run is not None:
                        codex_run.result_payload = {
                            **codex_run.result_payload,
                            "learning_insight_id": insight.id,
                            "learning_insight_status": insight.status,
                            "learning_promotion_state": promotion_state,
                            "learning_quarantine_reason": quarantine_reason,
                            "learning_synthesized_at": recorded_at.isoformat(),
                        }

                results.append(
                    LearningSynthesisResult(
                        document_id=document.id,
                        status="quarantined" if quarantine_reason else "synthesized",
                        insight_id=insight.id,
                        promotion_state=promotion_state,
                        quarantine_reason=quarantine_reason,
                    )
                )

            session.commit()
            return results

    def list_documents(
        self,
        *,
        limit: int = 10,
        source_types: Sequence[str] | None = None,
    ) -> list[LearningDocumentSummary]:
        with self.session_factory() as session:
            evidence_counts = (
                select(
                    EvidenceItemModel.document_id.label("document_id"),
                    func.count(EvidenceItemModel.id).label("evidence_count"),
                )
                .group_by(EvidenceItemModel.document_id)
                .subquery()
            )
            query = (
                select(DocumentModel, evidence_counts.c.evidence_count)
                .outerjoin(evidence_counts, evidence_counts.c.document_id == DocumentModel.id)
                .order_by(DocumentModel.ingested_at.desc())
                .limit(limit)
            )
            if source_types:
                query = query.where(DocumentModel.source_type.in_(list(source_types)))
            rows = session.execute(query).all()
            return [
                self._document_summary(document, int(evidence_count or 0))
                for document, evidence_count in rows
            ]

    def list_insights(
        self,
        *,
        limit: int = 10,
        statuses: Sequence[str] | None = None,
        promotion_states: Sequence[str] | None = None,
    ) -> list[LearningInsightSummary]:
        with self.session_factory() as session:
            query = select(InsightModel).order_by(InsightModel.recorded_at.desc()).limit(limit)
            if statuses:
                query = query.where(InsightModel.status.in_(list(statuses)))
            if promotion_states:
                query = query.where(InsightModel.promotion_state.in_(list(promotion_states)))
            insights = session.scalars(query).all()
            return [self._insight_summary(insight) for insight in insights]

    def get_learning_metrics(self) -> LearningMeshMetrics:
        with self.session_factory() as session:
            return LearningMeshMetrics(
                document_count=self._count(session, select(func.count()).select_from(DocumentModel)),
                insight_count=self._count(session, select(func.count()).select_from(InsightModel)),
                ready_insight_count=self._count(
                    session,
                    select(func.count()).select_from(InsightModel).where(
                        InsightModel.promotion_state == "ready_for_review"
                    ),
                ),
                quarantined_insight_count=self._count(
                    session,
                    select(func.count()).select_from(InsightModel).where(InsightModel.status == "quarantined"),
                ),
            )

    def _document_summary(self, document: DocumentModel, evidence_count: int) -> LearningDocumentSummary:
        return LearningDocumentSummary(
            id=document.id,
            codex_run_id=document.codex_run_id,
            workflow_run_id=document.workflow_run_id,
            supervisor_loop_key=document.supervisor_loop_key,
            source_key=document.source_key,
            source_type=document.source_type,
            title=document.title,
            summary=document.summary,
            status=document.status,
            citation_count=len(document.citations_json),
            evidence_count=evidence_count,
            confidence=document.confidence,
            created_at=document.created_at,
        )

    def _insight_summary(self, insight: InsightModel) -> LearningInsightSummary:
        return LearningInsightSummary(
            id=insight.id,
            document_id=insight.document_id,
            codex_run_id=insight.codex_run_id,
            workflow_run_id=insight.workflow_run_id,
            supervisor_loop_key=insight.supervisor_loop_key,
            topic_key=insight.topic_key,
            title=insight.title,
            summary=insight.summary,
            status=insight.status,
            promotion_state=insight.promotion_state,
            evidence_count=len(insight.supporting_evidence_refs),
            citation_count=len(insight.citation_refs),
            confidence=insight.confidence,
            quarantine_reason=insight.quarantine_reason,
            created_at=insight.created_at,
        )

    def _structured_output(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        structured = payload.get("structured_output") if payload else None
        return structured if isinstance(structured, dict) else None

    def _merged_structured_output(self, session: Session, run: CodexRunModel) -> dict[str, Any] | None:
        attempt_records = [
            {
                "phase": attempt.phase,
                "structured": structured,
                "result_payload": attempt.result_payload,
            }
            for attempt in session.scalars(
                select(CodexAttemptModel)
                .where(CodexAttemptModel.codex_run_id == run.id)
                .order_by(CodexAttemptModel.attempt_no.asc())
            ).all()
            for structured in [self._structured_output(attempt.result_payload)]
            if structured is not None
        ]
        if not attempt_records:
            return self._structured_output(run.result_payload)

        latest = attempt_records[-1]["structured"]
        preferred_summary = next(
            (
                str(record["structured"].get("summary"))
                for record in reversed(attempt_records)
                if record["phase"] == "implement" and record["structured"].get("summary")
            ),
            str(latest.get("summary") or run.objective),
        )
        preferred_confidence = next(
            (
                record["structured"].get("confidence")
                for record in reversed(attempt_records)
                if record["structured"].get("confidence") is not None
            ),
            latest.get("confidence"),
        )
        preferred_stdout_path = next(
            (
                record["result_payload"].get("stdout_path")
                for record in reversed(attempt_records)
                if record["phase"] == "implement" and record["result_payload"].get("stdout_path")
            ),
            (run.result_payload or {}).get("stdout_path"),
        )
        return {
            **latest,
            "summary": preferred_summary,
            "confidence": preferred_confidence,
            "preferred_stdout_path": preferred_stdout_path,
            "citations": self._coalesce_unique_strings(
                [item for record in attempt_records for item in record["structured"].get("citations") or []]
            ),
            "followup_tasks": self._coalesce_unique_strings(
                [item for record in attempt_records for item in record["structured"].get("followup_tasks") or []]
            ),
            "risks_found": self._coalesce_unique_strings(
                [item for record in attempt_records for item in record["structured"].get("risks_found") or []]
            ),
        }

    def _title_for_run(self, objective: str) -> str:
        title = objective.strip()
        if len(title) <= 180:
            return title
        return title[:177].rstrip() + "..."

    def _coerce_confidence(self, value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _topic_for_document(self, document: DocumentModel, evidence_items: Sequence[EvidenceItemModel]) -> str:
        evidence_topics = [item.topic for item in evidence_items if item.topic]
        if evidence_topics:
            return Counter(evidence_topics).most_common(1)[0][0]
        if document.supervisor_loop_key:
            return document.supervisor_loop_key
        if document.source_key:
            return document.source_key
        return "general-learning"

    def _promotion_state(
        self,
        *,
        confidence: float | None,
        evidence_count: int,
        citations: Sequence[str],
        source_health: Sequence[SourceHealthModel],
        quarantine_reason: str | None,
    ) -> str:
        if quarantine_reason:
            return "blocked"

        effective_confidence = confidence if confidence is not None else 0.5
        source_count = self._supporting_source_count(citations)
        average_trust = (
            sum(source.trust_score for source in source_health) / len(source_health)
            if source_health
            else 0.5
        )
        if effective_confidence >= 0.75 and evidence_count >= 2 and source_count >= 2 and average_trust >= 0.5:
            return "ready_for_review"
        if effective_confidence >= 0.6 and evidence_count >= 1 and average_trust >= 0.35:
            return "candidate"
        return "low_confidence"

    def _detect_quarantine_reason(
        self,
        document: DocumentModel,
        citations: Sequence[str],
        challenge_notes: Sequence[str],
        source_health: Sequence[SourceHealthModel],
    ) -> str | None:
        if not citations:
            return "No citations were preserved for this document."

        degraded_source = next(
            (
                source
                for source in source_health
                if source.health_status in {"compromised", "blocked"}
                or source.trust_score < 0.25
            ),
            None,
        )
        if degraded_source is not None:
            return f"Source health below quarantine floor: {degraded_source.source_key}."

        combined_text = " ".join(
            [document.summary, *document.risks_found, *document.followup_tasks, *challenge_notes]
        ).lower()
        for keyword in _QUARANTINE_KEYWORDS:
            if keyword in combined_text:
                return f"Detected learning-poisoning keyword: {keyword}."

        for citation in citations:
            parsed = urlparse(citation)
            if parsed.scheme and parsed.scheme not in {"http", "https"}:
                return f"Unsupported citation scheme detected: {parsed.scheme}."

        return None

    def _supporting_source_count(self, citations: Sequence[str]) -> int:
        sources = {
            (urlparse(citation).netloc or citation).strip().lower()
            for citation in citations
            if citation and str(citation).strip()
        }
        return len(sources)

    def _ensure_citation_sources(self, session: Session, citations: Sequence[str]) -> list[str]:
        source_keys: list[str] = []
        seen: set[str] = set()
        for citation in citations:
            source_key = self._source_key_for_citation(citation)
            if source_key in seen:
                continue
            seen.add(source_key)
            source_keys.append(source_key)
            existing = session.scalar(
                select(SourceHealthModel).where(SourceHealthModel.source_key == source_key)
            )
            if existing is None:
                session.add(
                    SourceHealthModel(
                        source_key=source_key,
                        source_type=self._source_type_for_key(source_key),
                        health_status="unknown",
                        trust_score=0.5,
                        freshness_score=0.5,
                        notes="Auto-discovered from durable learning citations.",
                        created_by="learning-service",
                        origin_type="citation",
                        origin_id=citation,
                        status="active",
                    )
                )
        return source_keys

    def _load_source_health_for_citations(
        self,
        session: Session,
        citations: Sequence[str],
    ) -> list[SourceHealthModel]:
        source_keys = [self._source_key_for_citation(citation) for citation in citations if citation]
        if not source_keys:
            return []
        return session.scalars(
            select(SourceHealthModel).where(SourceHealthModel.source_key.in_(source_keys))
        ).all()

    def _source_key_for_citation(self, citation: str) -> str:
        parsed = urlparse(citation)
        return (parsed.netloc or citation).strip().lower()

    def _source_type_for_key(self, source_key: str) -> str:
        if source_key.endswith(".gov") or source_key.endswith(".edu"):
            return "official"
        if any(token in source_key for token in ("reuters", "bloomberg", "wsj", "news")):
            return "news"
        return "web"

    def _coalesce_unique_strings(self, items: Sequence[str | None]) -> list[str]:
        seen: set[str] = set()
        values: list[str] = []
        for item in items:
            if item is None:
                continue
            value = str(item).strip()
            if not value or value in seen:
                continue
            seen.add(value)
            values.append(value)
        return values

    def _count(self, session: Session, query: Any) -> int:
        value = session.scalar(query)
        return int(value or 0)
