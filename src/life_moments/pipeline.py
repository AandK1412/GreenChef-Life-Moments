"""End-to-end pipeline orchestration.

For each cancellation comment:
    pre-screen  ->  classify (LLM or heuristic)  ->  validate  ->  route

`classify_record` handles one record; `run` processes an iterable of records and
returns enriched `RoutedRecord`s.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from .classifier import Classifier, get_classifier
from .prescreen import pre_screen
from .routing import route
from .schemas import Classification, RoutedRecord
from .validation import validate


class Pipeline:
    def __init__(self, classifier: Classifier | None = None):
        self.classifier: Classifier = classifier or get_classifier()

    def classify_record(self, order_id: str, week: int, comment: str) -> RoutedRecord:
        screen = pre_screen(comment)
        used_llm = False
        sent_to_classifier = screen.send_to_llm

        if screen.send_to_llm:
            classification: Classification = self.classifier.classify(comment)
            used_llm = self.classifier.name != "heuristic"
        else:
            assert screen.shortcut is not None
            classification = screen.shortcut

        verdict = validate(classification, comment)
        decision = route(classification)

        return RoutedRecord(
            order_id=order_id,
            week=week,
            comment=comment,
            classification=classification,
            track_name=decision.track_name,
            primary_offer=decision.primary_offer,
            secondary_action=decision.secondary_action,
            outreach_sla=decision.outreach_sla,
            channel=decision.channel,
            needs_human_review=verdict.needs_human_review,
            review_reason=verdict.reason,
            sent_to_classifier=sent_to_classifier,
            used_llm=used_llm,
        )

    def run(self, records: Iterable[dict]) -> Iterator[RoutedRecord]:
        """Process records. Each record is a dict with order_id, week, comment."""
        for rec in records:
            yield self.classify_record(
                order_id=str(rec.get("order_id", "")),
                week=int(rec.get("week", 0)),
                comment=str(rec.get("comment", "")),
            )
