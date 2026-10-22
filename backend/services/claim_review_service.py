import json
import logging
from decimal import Decimal
from typing import Any

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from openai import OpenAI

from backend.config import settings

logger = logging.getLogger("insureflow.ai_claim_review")


def _get_chatgpt_adjudication(claim: dict, policy_findings: list[str], amount_findings: list[str], completeness_findings: list[str]) -> dict[str, Any]:
    """
    Invokes the ChatGPT API if configured via OPENAI_API_KEY.
    If not configured or an error occurs, falls back gracefully to a heuristic risk adjudication.
    """
    claim_amount = float(claim["claim_amount"])
    coverage_amount = float(claim["coverage_amount"])
    claim_ratio = (claim_amount / coverage_amount) if coverage_amount > 0 else 1.0

    # Check if OpenAI is configured
    if settings.openai_api_key and settings.openai_api_key.strip():
        try:
            client_kwargs = {"api_key": settings.openai_api_key.strip()}
            if settings.openai_base_url and settings.openai_base_url.strip():
                client_kwargs["base_url"] = settings.openai_base_url.strip()

            client = OpenAI(**client_kwargs)
            model = settings.openai_model or "gpt-4o-mini"

            prompt = f"""
You are an expert insurance claim adjudicator and fraud analyst AI.
Evaluate this insurance claim and output ONLY a valid JSON object.

CLAIM DETAILS:
- Claim Number: {claim.get('claim_number')}
- Policy Number: {claim.get('policy_number')}
- Policy Status: {claim.get('policy_status')}
- Incident Date: {claim.get('incident_date')}
- Policy Period: {claim.get('start_date')} to {claim.get('end_date')}
- Claim Amount: ${claim_amount:,.2f}
- Coverage Limit: ${coverage_amount:,.2f}
- Description: {claim.get('description')}

PRELIMINARY RULE CHECKS:
- Policy Checks: {policy_findings or ['Passed']}
- Amount Checks: {amount_findings or ['Passed']}
- Completeness Checks: {completeness_findings or ['Passed']}

Required JSON fields:
{{
    "risk_score": <integer from 0 to 100>,
    "recommendation": <"approve" | "investigate" | "reject">,
    "confidence_score": <float from 0.0 to 1.0>,
    "summary_reasoning": <string explaining the assessment>,
    "red_flags": [<string>, ...],
    "key_observations": [<string>, ...],
    "model_used": "{model}"
}}
"""
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a professional insurance risk adjudicator. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
                timeout=15.0
            )

            content = response.choices[0].message.content
            parsed = json.loads(content)
            parsed["provider"] = "OpenAI ChatGPT API"
            parsed["model"] = model
            return parsed

        except Exception as e:
            logger.warning(f"OpenAI API call failed, falling back to heuristic engine: {e}")

    # Fallback heuristic adjudication engine
    risk_score = 15
    red_flags = []
    observations = []

    if policy_findings:
        risk_score += 35
        red_flags.extend(policy_findings)

    if amount_findings:
        risk_score += 30
        red_flags.extend(amount_findings)

    if completeness_findings:
        risk_score += 20
        red_flags.extend(completeness_findings)

    if claim_ratio > 0.8:
        risk_score += 15
        observations.append(f"High severity claim: claimed amount is {claim_ratio * 100:.1f}% of total policy coverage limit.")

    desc = (claim.get("description") or "").lower()
    suspicious_terms = ["lost", "cash", "stolen", "unattended", "unknown person", "mysterious"]
    found_terms = [term for term in suspicious_terms if term in desc]
    if found_terms:
        risk_score += 15
        observations.append(f"Narrative contains sensitive keywords: {', '.join(found_terms)}")

    if len(desc.split()) < 10:
        risk_score += 10
        observations.append("Narrative description is brief; consider requesting supplementary proof or statements.")

    risk_score = min(99, max(5, risk_score))

    if risk_score >= 65:
        recommendation = "investigate"
        reasoning = "Elevated risk score detected due to policy status, claim-to-coverage ratio, or rule flags. Manual claims adjuster inspection required."
    elif risk_score >= 40:
        recommendation = "investigate"
        reasoning = "Moderate risk indicators observed. Routine documentation verification recommended before payout approval."
    else:
        recommendation = "approve"
        reasoning = "Standard low-risk profile. All automated policy validations and amount limits satisfied."

    return {
        "risk_score": risk_score,
        "recommendation": recommendation,
        "confidence_score": 0.88,
        "summary_reasoning": reasoning,
        "red_flags": red_flags,
        "key_observations": observations,
        "provider": "InsureFlow Heuristic Engine (Configure OPENAI_API_KEY in .env for live ChatGPT)",
        "model": settings.openai_model or "gpt-4o-mini"
    }


def review_claim(claim_id: int, db: Session):
    # 1. Retrieve claim details and related policy
    claim = db.execute(
        text("""
            SELECT
                c.claim_id,
                c.claim_number,
                c.policy_id,
                c.incident_date,
                c.claim_amount,
                c.description,
                c.status AS claim_status,
                c.decision_reason,
                p.policy_number,
                p.start_date,
                p.end_date,
                p.coverage_amount,
                p.status AS policy_status
            FROM claims c
            JOIN policies p ON c.policy_id = p.policy_id
            WHERE c.claim_id = :claim_id
        """),
        {"claim_id": claim_id},
    ).mappings().first()

    if claim is None:
        raise HTTPException(
            status_code=404,
            detail="Claim or associated policy not found",
        )

    claim = dict(claim)

    # 2. Agent 1: Policy validation
    policy_findings = []

    if claim["policy_status"] != "active":
        policy_findings.append(
            "Policy is not currently marked active; verify eligibility."
        )

    if not (
        claim["start_date"]
        <= claim["incident_date"]
        <= claim["end_date"]
    ):
        policy_findings.append(
            "Incident date falls outside the policy period."
        )

    policy_outcome = (
        "review_required" if policy_findings else "no_issue_detected"
    )

    # 3. Agent 2: Claim amount checks
    amount_findings = []
    claim_amount = Decimal(str(claim["claim_amount"]))
    coverage_amount = Decimal(str(claim["coverage_amount"]))

    if claim_amount > coverage_amount:
        amount_findings.append(
            "Claimed amount exceeds the listed policy coverage amount."
        )

    amount_outcome = (
        "review_required" if amount_findings else "no_issue_detected"
    )

    # 4. Agent 3: Completeness checks
    completeness_findings = []

    if not claim["description"] or not claim["description"].strip():
        completeness_findings.append("Claim description is missing.")

    if claim_amount <= 0:
        completeness_findings.append(
            "Claim amount must be greater than zero."
        )

    completeness_outcome = (
        "review_required"
        if completeness_findings
        else "no_issue_detected"
    )

    # 5. Agent 4: ChatGPT / AI Adjudication Agent
    ai_adjudication = _get_chatgpt_adjudication(
        claim,
        policy_findings,
        amount_findings,
        completeness_findings
    )

    adjudication_outcome = (
        "review_required"
        if ai_adjudication.get("recommendation") in ["investigate", "reject"] or ai_adjudication.get("risk_score", 0) >= 50
        else "no_issue_detected"
    )

    findings_by_agent = [
        {
            "agent_name": "policy_validation_agent",
            "findings": {
                "checks": policy_findings,
                "policy_status": claim["policy_status"],
                "policy_period": {
                    "start": str(claim["start_date"]),
                    "end": str(claim["end_date"]),
                },
            },
            "outcome": policy_outcome,
        },
        {
            "agent_name": "claim_amount_agent",
            "findings": {
                "checks": amount_findings,
                "claim_amount": str(claim_amount),
                "coverage_amount": str(coverage_amount),
            },
            "outcome": amount_outcome,
        },
        {
            "agent_name": "completeness_agent",
            "findings": {
                "checks": completeness_findings,
                "description_present": bool(
                    claim["description"]
                    and claim["description"].strip()
                ),
            },
            "outcome": completeness_outcome,
        },
        {
            "agent_name": "chatgpt_adjudication_agent",
            "findings": ai_adjudication,
            "outcome": adjudication_outcome,
        },
    ]

    needs_review = any(
        agent["outcome"] == "review_required"
        for agent in findings_by_agent
    )

    final_result = (
        "human_review_required"
        if needs_review
        else "checks_completed"
    )

    # 6. Save the run and agent findings in one transaction
    try:
        run = db.execute(
            text("""
                INSERT INTO ai_runs (
                    claim_id,
                    workflow_type,
                    status,
                    final_result
                )
                VALUES (
                    :claim_id,
                    :workflow_type,
                    :status,
                    :final_result
                )
            """),
            {
                "claim_id": claim_id,
                "workflow_type": "claim_review",
                "status": "completed",
                "final_result": final_result,
            },
        )

        run_id = run.lastrowid

        for agent in findings_by_agent:
            db.execute(
                text("""
                    INSERT INTO agent_results (
                        run_id,
                        agent_name,
                        findings,
                        outcome
                    )
                    VALUES (
                        :run_id,
                        :agent_name,
                        :findings,
                        :outcome
                    )
                """),
                {
                    "run_id": run_id,
                    "agent_name": agent["agent_name"],
                    "findings": json.dumps(agent["findings"]),
                    "outcome": agent["outcome"],
                },
            )

        # Update claim's decision_reason and status if needed
        db.execute(
            text("""
                UPDATE claims
                SET decision_reason = :reason,
                    status = CASE WHEN status = 'submitted' THEN 'in_review' ELSE status END
                WHERE claim_id = :claim_id
            """),
            {
                "claim_id": claim_id,
                "reason": f"AI Assessment [{final_result}]: Risk Score {ai_adjudication.get('risk_score', 0)}/100, Rec: {ai_adjudication.get('recommendation', 'N/A')}. {ai_adjudication.get('summary_reasoning', '')[:120]}..."
            }
        )

        db.commit()

    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Unable to save the AI review audit record: {exc}",
        ) from exc

    return {
        "run_id": run_id,
        "claim": {
            "claim_id": claim["claim_id"],
            "claim_number": claim["claim_number"],
            "claim_status": claim["claim_status"],
        },
        "workflow_type": "claim_review",
        "status": "completed",
        "final_result": final_result,
        "ai_adjudication": ai_adjudication,
        "agents": findings_by_agent,
        "notice": (
            "These are automated multi-agent assessments powered by OpenAI/rule checks. "
            "Final adjudication should be verified by a licensed human adjuster."
        ),
    }


def get_claim_reviews(claim_id: int, db: Session) -> list[dict]:
    """Retrieve all historical AI review runs for a specific claim."""
    runs = db.execute(
        text("""
            SELECT run_id, claim_id, workflow_type, status, final_result, created_at
            FROM ai_runs
            WHERE claim_id = :claim_id
            ORDER BY run_id DESC
        """),
        {"claim_id": claim_id}
    ).mappings().all()

    result = []
    for r in runs:
        run_dict = dict(r)
        run_dict["created_at"] = str(run_dict["created_at"]) if run_dict.get("created_at") else None
        agents = db.execute(
            text("""
                SELECT result_id, agent_name, findings, outcome, created_at
                FROM agent_results
                WHERE run_id = :run_id
                ORDER BY result_id ASC
            """),
            {"run_id": run_dict["run_id"]}
        ).mappings().all()

        run_dict["agents"] = []
        for a in agents:
            ad = dict(a)
            ad["created_at"] = str(ad["created_at"]) if ad.get("created_at") else None
            if isinstance(ad.get("findings"), str):
                try:
                    ad["findings"] = json.loads(ad["findings"])
                except Exception:
                    pass
            run_dict["agents"].append(ad)

        result.append(run_dict)

    return result


def get_all_audit_records(db: Session, limit: int = 50) -> list[dict]:
    """Retrieve all AI audit records across all claims for audit review."""
    runs = db.execute(
        text("""
            SELECT 
                r.run_id, r.claim_id, r.workflow_type, r.status, r.final_result, r.created_at,
                c.claim_number, c.claim_amount, c.status AS claim_status,
                p.policy_number
            FROM ai_runs r
            JOIN claims c ON r.claim_id = c.claim_id
            JOIN policies p ON c.policy_id = p.policy_id
            ORDER BY r.run_id DESC
            LIMIT :limit
        """),
        {"limit": limit}
    ).mappings().all()

    result = []
    for r in runs:
        run_dict = dict(r)
        run_dict["created_at"] = str(run_dict["created_at"]) if run_dict.get("created_at") else None
        agents = db.execute(
            text("""
                SELECT result_id, agent_name, findings, outcome
                FROM agent_results
                WHERE run_id = :run_id
                ORDER BY result_id ASC
            """),
            {"run_id": run_dict["run_id"]}
        ).mappings().all()

        run_dict["agents"] = []
        for a in agents:
            ad = dict(a)
            if isinstance(ad.get("findings"), str):
                try:
                    ad["findings"] = json.loads(ad["findings"])
                except Exception:
                    pass
            run_dict["agents"].append(ad)

        result.append(run_dict)

    return result


def get_review_run(run_id: int, db: Session) -> dict:
    """Retrieve detailed audit record for a single run ID."""
    run = db.execute(
        text("""
            SELECT 
                r.run_id, r.claim_id, r.workflow_type, r.status, r.final_result, r.created_at,
                c.claim_number, c.claim_amount, c.description, c.status AS claim_status,
                p.policy_number, p.coverage_amount
            FROM ai_runs r
            JOIN claims c ON r.claim_id = c.claim_id
            JOIN policies p ON c.policy_id = p.policy_id
            WHERE r.run_id = :run_id
        """),
        {"run_id": run_id}
    ).mappings().first()

    if not run:
        raise HTTPException(status_code=404, detail="AI review run not found")

    run_dict = dict(run)
    run_dict["created_at"] = str(run_dict["created_at"]) if run_dict.get("created_at") else None

    agents = db.execute(
        text("""
            SELECT result_id, agent_name, findings, outcome, created_at
            FROM agent_results
            WHERE run_id = :run_id
            ORDER BY result_id ASC
        """),
        {"run_id": run_id}
    ).mappings().all()

    run_dict["agents"] = []
    for a in agents:
        ad = dict(a)
        ad["created_at"] = str(ad["created_at"]) if ad.get("created_at") else None
        if isinstance(ad.get("findings"), str):
            try:
                ad["findings"] = json.loads(ad["findings"])
            except Exception:
                pass
        run_dict["agents"].append(ad)

    return run_dict