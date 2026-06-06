"""Differentiated retention routing (Capability 2 & 3, Section VII.2-VII.3).

Maps a validated `Classification` onto a concrete response track. The offer
catalogue is a direct encoding of Table VII-1; the outreach SLA / channel come
from the priority-band triage in Section VII.2. Low-Potential and Release
subscribers continue through the standard cancellation workflow unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import LifeContext, PriorityBand, RecoverabilityClass
from .schemas import Classification


@dataclass(frozen=True)
class Track:
    name: str
    primary_offer: str
    secondary_action: str


# Table VII-1. Life Moments response tracks by life-context category.
RESPONSE_TRACKS: dict[LifeContext, Track] = {
    LifeContext.BUDGET_PRESSURE: Track(
        "Budget Pressure",
        "Temporary 10-20% discount or smaller box for 4 weeks",
        "Scheduled re-engagement at 6 weeks with full plan offer",
    ),
    LifeContext.SCHEDULE_CHANGE: Track(
        "Schedule Change",
        "Extended pause option (4-8 weeks) at no penalty",
        "Pre-scheduled reactivation reminder at return date",
    ),
    LifeContext.HEALTH_EVENT: Track(
        "Health Event",
        "Free plan switch to relevant dietary tier + empathetic message",
        "Nutritionist resource link or condition-specific guidance",
    ),
    LifeContext.WORK_TRAVEL: Track(
        "Work Travel",
        "Flexible pause or delivery-skip for stated travel period",
        "Welcome-back offer pre-loaded at projected return date",
    ),
    LifeContext.NEW_ARRIVAL: Track(
        "New Arrival",
        "Simplified meal tier; frequency adjustment",
        "Family-size plan recommendation upon return",
    ),
    LifeContext.RELOCATION: Track(
        "Relocation",
        "Coverage confirmation for new address; welcome offer",
        "Re-engagement outreach if outside coverage area",
    ),
    LifeContext.OTHER: Track(
        "Other Life Context",
        "Empathetic message + flexible pause option",
        "Scheduled re-engagement at 6 weeks",
    ),
}

STANDARD_TRACK = Track(
    "Standard Cancellation Workflow",
    "No retention offer (standard workflow)",
    "Warm farewell message",
)

# Priority-band -> outreach SLA + channel (Section VII.2).
_SLA = {
    PriorityBand.URGENT: ("Within 24 hours", "CRM-flagged for customer success personalization"),
    PriorityBand.HIGH: ("Within 48-72 hours", "Automated personalized outreach"),
    PriorityBand.MODERATE: ("Scheduled sequence", "Automated re-engagement sequence"),
    PriorityBand.LOW: ("Scheduled sequence", "Automated re-engagement sequence"),
}


@dataclass(frozen=True)
class RoutingDecision:
    track_name: str
    primary_offer: str
    secondary_action: str
    outreach_sla: str
    channel: str


def route(classification: Classification) -> RoutingDecision:
    """Return the routing decision for a classification."""
    # Only High-Potential subscribers receive a differentiated retention track.
    if classification.recoverability is not RecoverabilityClass.HIGH_POTENTIAL:
        return RoutingDecision(
            track_name=STANDARD_TRACK.name,
            primary_offer=STANDARD_TRACK.primary_offer,
            secondary_action=STANDARD_TRACK.secondary_action,
            outreach_sla="None",
            channel="Standard cancellation workflow",
        )

    track = RESPONSE_TRACKS.get(classification.life_context, RESPONSE_TRACKS[LifeContext.OTHER])
    sla, channel = _SLA[classification.band]
    return RoutingDecision(
        track_name=track.name,
        primary_offer=track.primary_offer,
        secondary_action=track.secondary_action,
        outreach_sla=sla,
        channel=channel,
    )
