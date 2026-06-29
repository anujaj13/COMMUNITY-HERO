"""
Insights Service — AI-powered predictive analytics for Community Hero
Powered by Google Gemini with Structured Outputs

Provides:
  - generate_insights(db)            : dashboard-level predictions (cached 10 min)
  - forecast_resolution(issue_id, db): per-issue resolution time estimate
"""
import time
import json
from datetime import datetime, timedelta
from typing import Optional
from collections import defaultdict
from math import sqrt

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from google.genai import types

from app.services.ai_service import _get_client, _call_gemini_with_retry, _parse_json_block
from app.utils.logging_config import logger


# ── Pydantic Schemas ───────────────────────────────────────────────────────────

class AtRiskIssue(BaseModel):
    id: int = Field(description="The issue ID")
    title: str = Field(description="Short issue title")
    reason: str = Field(description="One sentence explaining why this issue is at risk of escalation")
    risk_level: str = Field(description="One of: medium, high, critical")


class CategoryTrend(BaseModel):
    category: str = Field(description="The issue category name")
    direction: str = Field(description="One of: rising, falling, stable")
    change_pct: int = Field(description="Percentage change vs prior week, e.g. 45 or -12")
    insight: str = Field(description="One sentence explaining what is driving this trend")


class HotspotCluster(BaseModel):
    label: str = Field(description="Human readable area label, e.g. 'Downtown area' or 'North district'")
    issue_count: int = Field(description="Number of open issues in this cluster")
    dominant_category: str = Field(description="The most common category in this cluster")
    severity: str = Field(description="One of: moderate, severe")
    lat: float = Field(description="Approximate centroid latitude of the cluster")
    lng: float = Field(description="Approximate centroid longitude of the cluster")


class InsightsResult(BaseModel):
    at_risk_issues: list[AtRiskIssue] = Field(
        description="Up to 3 open issues most at risk of escalating. Empty list if none."
    )
    category_trends: list[CategoryTrend] = Field(
        description="Trend analysis for each category that has issues. Up to 5 entries."
    )
    hotspot_clusters: list[HotspotCluster] = Field(
        description="Geographic clusters of open issues. Up to 3 entries. Empty list if location data is unavailable."
    )
    summary_narrative: str = Field(
        description="2-3 sentence executive summary of community issue health for a civic dashboard"
    )


class ResolutionForecast(BaseModel):
    issue_id: int = Field(description="The issue ID being forecast")
    estimated_days: int = Field(description="Estimated days until resolution, from today")
    confidence: str = Field(description="One of: low, medium, high")
    rationale: str = Field(description="One sentence explaining the forecast")


# ── In-Memory TTL Cache ────────────────────────────────────────────────────────

_insights_cache: dict = {
    "data": None,
    "expires_at": 0.0,
}
CACHE_TTL_SECONDS = 600  # 10 minutes


# ── Snapshot Builder ───────────────────────────────────────────────────────────

def _build_snapshot(db: Session) -> dict:
    """
    Queries the database and returns a compact JSON-serializable snapshot
    suitable for inclusion in a Gemini prompt.
    """
    from app.models.issue import Issue
    from app.models.verification import Verification

    now = datetime.utcnow()
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)
    fourteen_days_ago = now - timedelta(days=14)

    # All open issues (not resolved/closed)
    open_issues = db.query(Issue).filter(
        Issue.status.notin_(["resolved", "closed"])
    ).all()

    # All issues created in last 30 days
    recent_issues = db.query(Issue).filter(
        Issue.created_at >= thirty_days_ago
    ).all()

    # Category counts for this week vs last week
    this_week_issues = db.query(Issue).filter(
        Issue.created_at >= seven_days_ago
    ).all()
    last_week_issues = db.query(Issue).filter(
        Issue.created_at >= fourteen_days_ago,
        Issue.created_at < seven_days_ago
    ).all()

    # Category aggregation
    this_week_by_cat = defaultdict(int)
    for i in this_week_issues:
        this_week_by_cat[i.category] += 1

    last_week_by_cat = defaultdict(int)
    for i in last_week_issues:
        last_week_by_cat[i.category] += 1

    category_trend_data = {}
    all_cats = set(list(this_week_by_cat.keys()) + list(last_week_by_cat.keys()))
    for cat in all_cats:
        this = this_week_by_cat.get(cat, 0)
        last = last_week_by_cat.get(cat, 0)
        category_trend_data[cat] = {"this_week": this, "last_week": last}

    # Priority distribution
    priority_counts = defaultdict(int)
    for i in open_issues:
        priority_counts[i.priority] += 1

    # Status distribution
    status_counts = defaultdict(int)
    for i in recent_issues:
        status_counts[i.status] += 1

    # Stale reported issues (>7 days, still 'reported')
    stale_reported = [
        i for i in open_issues
        if i.status == "reported" and (now - i.created_at).days >= 7
    ]

    # Top 5 open issues by verification count
    top_verified = sorted(
        open_issues, key=lambda x: x.verification_count or 0, reverse=True
    )[:5]

    # Resolved this week vs last week
    resolved_this_week = db.query(Issue).filter(
        Issue.status == "resolved",
        Issue.resolved_at >= seven_days_ago
    ).count()
    resolved_last_week = db.query(Issue).filter(
        Issue.status == "resolved",
        Issue.resolved_at >= fourteen_days_ago,
        Issue.resolved_at < seven_days_ago
    ).count()

    # Geographic clusters (simple centroid grouping)
    geo_issues = [
        i for i in open_issues
        if i.latitude is not None and i.longitude is not None
    ]
    clusters = _compute_clusters(geo_issues)

    # At-risk candidates: high verifications but still old status
    at_risk_candidates = [
        {
            "id": i.id,
            "title": i.title,
            "status": i.status,
            "priority": i.priority,
            "verification_count": i.verification_count or 0,
            "days_open": (now - i.created_at).days,
            "category": i.category,
        }
        for i in open_issues
        if (i.verification_count or 0) >= 2 or (now - i.created_at).days >= 5
    ][:10]  # Cap at 10 to stay within token budget

    return {
        "total_open_issues": len(open_issues),
        "total_recent_issues_30d": len(recent_issues),
        "priority_distribution": dict(priority_counts),
        "status_distribution": dict(status_counts),
        "category_weekly_trend": category_trend_data,
        "stale_reported_count": len(stale_reported),
        "resolved_this_week": resolved_this_week,
        "resolved_last_week": resolved_last_week,
        "top_verified_open_issues": [
            {"id": i.id, "title": i.title, "verifications": i.verification_count or 0,
             "priority": i.priority, "days_open": (now - i.created_at).days}
            for i in top_verified
        ],
        "at_risk_candidates": at_risk_candidates,
        "geographic_clusters": clusters,
    }


def _compute_clusters(issues: list, radius_deg: float = 0.05) -> list:
    """
    Simple greedy geographic clustering by proximity.
    Returns up to 3 clusters with centroid lat/lng and count.
    """
    if not issues:
        return []

    clusters = []
    assigned = set()

    for i, issue in enumerate(issues):
        if i in assigned:
            continue
        cluster = [issue]
        assigned.add(i)
        for j, other in enumerate(issues):
            if j in assigned:
                continue
            dist = sqrt(
                (issue.latitude - other.latitude) ** 2 +
                (issue.longitude - other.longitude) ** 2
            )
            if dist <= radius_deg:
                cluster.append(other)
                assigned.add(j)

        cat_counts = defaultdict(int)
        for c in cluster:
            cat_counts[c.category] += 1
        dominant = max(cat_counts, key=cat_counts.get)
        centroid_lat = sum(c.latitude for c in cluster) / len(cluster)
        centroid_lng = sum(c.longitude for c in cluster) / len(cluster)

        clusters.append({
            "count": len(cluster),
            "dominant_category": dominant,
            "centroid_lat": round(centroid_lat, 5),
            "centroid_lng": round(centroid_lng, 5),
        })

    # Return top 3 by size
    clusters.sort(key=lambda x: x["count"], reverse=True)
    return clusters[:3]


# ── Main Insights Generator ────────────────────────────────────────────────────

def generate_insights(db: Session) -> dict:
    """
    Returns AI-generated predictive insights for the community dashboard.
    Results are cached for CACHE_TTL_SECONDS to avoid repeated Gemini calls.
    """
    global _insights_cache

    # Serve from cache if still valid
    if _insights_cache["data"] and time.time() < _insights_cache["expires_at"]:
        logger.info("InsightsService: Serving insights from cache")
        return _insights_cache["data"]

    logger.info("InsightsService: Building DB snapshot for insights generation...")
    snapshot = _build_snapshot(db)

    # Graceful fallback for sparse data
    if snapshot["total_recent_issues_30d"] < 3:
        logger.info("InsightsService: Too few issues for meaningful insights, returning sparse data response")
        result = _sparse_data_fallback()
        _insights_cache["data"] = result
        _insights_cache["expires_at"] = time.time() + CACHE_TTL_SECONDS
        return result

    prompt = f"""You are a civic AI analyst for a community issue-reporting platform called Community Hero.
Analyze the following data snapshot and generate predictive insights for the dashboard.

DATA SNAPSHOT (last 30 days):
{json.dumps(snapshot, indent=2)}

Instructions:
- at_risk_issues: Identify up to 3 open issues from 'at_risk_candidates' that are most likely to escalate.
  Focus on issues with high verification_count relative to their status, or issues that have been open many days.
- category_trends: For each category in 'category_weekly_trend', assess direction (rising/falling/stable).
  Use the this_week vs last_week counts. If last_week is 0 and this_week > 0, direction is 'rising'.
  Provide up to 5 entries sorted by significance.
- hotspot_clusters: Convert 'geographic_clusters' into labeled hotspot alerts. Estimate a human-friendly
  area label (e.g. 'Central district', 'Northern zone'). severity is 'severe' if count >= 5, else 'moderate'.
  Use the centroid_lat/centroid_lng values directly.
- summary_narrative: Write 2-3 sentences as a civic official briefing on overall community issue health.

Respond using the provided JSON schema. Be concise and actionable."""

    try:
        client = _get_client()

        def make_request():
            return client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    response_mime_type="application/json",
                    response_schema=InsightsResult,
                )
            )

        response = _call_gemini_with_retry(make_request, max_retries=3, initial_delay=2)
        result = _parse_json_block(response.text)
        result["generated_at"] = datetime.utcnow().isoformat()
        result["sparse_data"] = False

        logger.info("InsightsService: Insights generated successfully")
        _insights_cache["data"] = result
        _insights_cache["expires_at"] = time.time() + CACHE_TTL_SECONDS
        return result

    except Exception as e:
        logger.error(f"InsightsService: Failed to generate insights: {e}", exc_info=True)
        return _error_fallback(str(e))


# ── Resolution Forecast ────────────────────────────────────────────────────────

def forecast_resolution(issue_id: int, db: Session) -> dict:
    """
    Estimates resolution time for a specific issue based on its attributes
    and historical resolution patterns from the database.
    """
    from app.models.issue import Issue

    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        return {"error": "Issue not found"}

    # Historical resolution times for same category
    resolved_same_cat = db.query(Issue).filter(
        Issue.category == issue.category,
        Issue.status == "resolved",
        Issue.resolved_at.isnot(None),
    ).all()

    avg_days = None
    if resolved_same_cat:
        times = [
            (i.resolved_at - i.created_at).days
            for i in resolved_same_cat
            if i.resolved_at and i.created_at
        ]
        avg_days = round(sum(times) / len(times)) if times else None

    days_open = (datetime.utcnow() - issue.created_at).days if issue.created_at else 0

    prompt = f"""You are a civic AI analyst. Estimate the resolution time for this community issue.

ISSUE DETAILS:
- ID: {issue.id}
- Title: {issue.title}
- Category: {issue.category}
- Priority: {issue.priority}
- Current Status: {issue.status}
- Days Open: {days_open}
- Verification Count: {issue.verification_count or 0}
- Impact Score: {issue.impact_score or 0}

HISTORICAL CONTEXT:
- Average resolution time for '{issue.category}' issues: {f"{avg_days} days" if avg_days else "No historical data"}
- Sample size: {len(resolved_same_cat)} resolved issues in this category

Instructions:
- Estimate how many more days until this issue will be resolved, from today.
- Consider priority (critical = faster), verifications (more = more attention), and historical average.
- confidence is 'high' if historical data is available, 'medium' if partial, 'low' if no data.
- Return issue_id as {issue.id}.

Respond using the provided JSON schema."""

    try:
        client = _get_client()

        def make_request():
            return client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json",
                    response_schema=ResolutionForecast,
                )
            )

        response = _call_gemini_with_retry(make_request, max_retries=2, initial_delay=1)
        result = _parse_json_block(response.text)
        logger.info(f"InsightsService: Resolution forecast for issue {issue_id}: {result}")
        return result

    except Exception as e:
        logger.error(f"InsightsService: Forecast failed for issue {issue_id}: {e}")
        return {
            "issue_id": issue_id,
            "estimated_days": avg_days or 7,
            "confidence": "low",
            "rationale": "Forecast unavailable; using category average estimate."
        }


# ── Fallback Responses ─────────────────────────────────────────────────────────

def _sparse_data_fallback() -> dict:
    return {
        "at_risk_issues": [],
        "category_trends": [],
        "hotspot_clusters": [],
        "summary_narrative": "Not enough community data yet to generate meaningful predictions. Keep reporting issues to unlock AI-powered insights!",
        "generated_at": datetime.utcnow().isoformat(),
        "sparse_data": True,
    }


def _error_fallback(error_msg: str) -> dict:
    return {
        "at_risk_issues": [],
        "category_trends": [],
        "hotspot_clusters": [],
        "summary_narrative": "Predictive insights are temporarily unavailable. Please try again shortly.",
        "generated_at": datetime.utcnow().isoformat(),
        "sparse_data": False,
        "error": error_msg,
    }
