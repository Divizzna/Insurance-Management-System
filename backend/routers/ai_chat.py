import os
from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from openai import OpenAI

from backend.config import settings

router = APIRouter(
    prefix="/api/v1/ai",
    tags=["AI Assistant & ChatGPT"],
)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: list[ChatMessage] = []
    context: dict[str, Any] | None = None


class ConfigUpdateRequest(BaseModel):
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str | None = None


@router.get("/status")
def get_ai_status():
    """Check AI agent system status and OpenAI configuration."""
    has_key = bool(settings.openai_api_key and settings.openai_api_key.strip())
    masked_key = (
        settings.openai_api_key[:6] + "..." + settings.openai_api_key[-4:]
        if has_key and len(settings.openai_api_key) > 10
        else ("Configured" if has_key else "Not Configured")
    )

    return {
        "status": "ready",
        "chatgpt_configured": has_key,
        "api_key_masked": masked_key,
        "base_url": settings.openai_base_url or "https://api.openai.com/v1 (default)",
        "model": settings.openai_model or "gpt-4o-mini",
        "active_agents": [
            {
                "name": "policy_validation_agent",
                "role": "Validates policy status, active period, and policyholder integrity",
            },
            {
                "name": "claim_amount_agent",
                "role": "Verifies claim amounts against maximum policy coverage caps",
            },
            {
                "name": "completeness_agent",
                "role": "Inspects required fields, documentation completeness, and narrative details",
            },
            {
                "name": "chatgpt_adjudication_agent",
                "role": "Analyzes claim narrative, calculates fraud risk score, and recommends approval or human investigation",
            },
        ],
    }


@router.post("/config")
def update_ai_config(payload: ConfigUpdateRequest):
    """Dynamically update OpenAI settings for testing."""
    if payload.openai_api_key is not None:
        settings.openai_api_key = payload.openai_api_key.strip()
    if payload.openai_base_url is not None:
        settings.openai_base_url = payload.openai_base_url.strip()
    if payload.openai_model is not None and payload.openai_model.strip():
        settings.openai_model = payload.openai_model.strip()

    return {
        "message": "AI configuration updated successfully",
        "model": settings.openai_model,
        "has_key": bool(settings.openai_api_key),
    }


@router.post("/chat")
def chat_with_assistant(payload: ChatRequest):
    """
    Conversational insurance assistant powered by ChatGPT (with smart fallback if key is not set).
    """
    user_message = payload.message.strip()

    # If OpenAI is configured, call ChatGPT
    if settings.openai_api_key and settings.openai_api_key.strip():
        try:
            client_kwargs = {"api_key": settings.openai_api_key.strip()}
            if settings.openai_base_url and settings.openai_base_url.strip():
                client_kwargs["base_url"] = settings.openai_base_url.strip()

            client = OpenAI(**client_kwargs)

            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are InsureFlow AI, an intelligent, empathetic, and knowledgeable insurance enterprise copilot. "
                        "You assist customers, agents, and underwriters with policies, claims, coverage limits, payments, "
                        "and AI claim adjudication explanations. Format answers cleanly using Markdown with bullet points where appropriate."
                    ),
                }
            ]

            # Add context if provided
            if payload.context:
                messages.append({
                    "role": "system",
                    "content": f"Active System Context: {payload.context}"
                })

            for h in payload.history[-8:]:
                messages.append({"role": h.role, "content": h.content})

            messages.append({"role": "user", "content": user_message})

            response = client.chat.completions.create(
                model=settings.openai_model or "gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                max_tokens=600,
                timeout=15.0,
            )

            reply = response.choices[0].message.content
            return {
                "reply": reply,
                "provider": "OpenAI ChatGPT",
                "model": settings.openai_model or "gpt-4o-mini",
            }

        except Exception as e:
            # Fall back to heuristic answers if API fails
            pass

    # Intelligent Heuristic Fallback Assistant
    lower_msg = user_message.lower()
    
    if any(k in lower_msg for k in ["claim", "file a claim", "status"]):
        reply = (
            "### 📋 Claim Management with InsureFlow AI\n\n"
            "To file or inspect an insurance claim:\n"
            "1. **Navigate to the Claims Tab** in the dashboard.\n"
            "2. Ensure the associated policy is **active** and within its valid date range.\n"
            "3. Provide an accurate incident date, detailed description, and claim amount.\n"
            "4. Click **Run AI Review** on any claim to trigger our multi-agent adjudication pipeline!\n\n"
            "> 💡 *Tip: To enable live GPT-4o reasoning, set your `OPENAI_API_KEY` in the AI Settings.*"
        )
    elif any(k in lower_msg for k in ["policy", "coverage", "premium"]):
        reply = (
            "### 🛡️ Policy & Coverage Guidelines\n\n"
            "InsureFlow AI supports diverse product lines including **Auto**, **Health**, **Life**, and **Home** insurance.\n"
            "- **Active Status**: Policies must be in `active` status for claims to be approved.\n"
            "- **Coverage Limit**: Claims cannot exceed the stated `coverage_amount`.\n"
            "- **Payments**: Ensure monthly/annual premiums are up to date in the Payments section."
        )
    elif any(k in lower_msg for k in ["audit", "ai run", "agent", "workflow"]):
        reply = (
            "### 🤖 Multi-Agent Adjudication Pipeline\n\n"
            "Every claim review executes 4 specialized agent checks:\n"
            "1. **Policy Validation Agent**: Verifies policy status & incident date bounds.\n"
            "2. **Claim Amount Agent**: Compares claim against policy coverage caps.\n"
            "3. **Completeness Agent**: Evaluates incident narrative depth and required fields.\n"
            "4. **ChatGPT Adjudication Agent**: Performs narrative fraud scoring and recommendation.\n\n"
            "All runs and agent outputs are permanently logged to `ai_runs` and `agent_results` for complete regulatory compliance."
        )
    else:
        reply = (
            f"### Welcome to InsureFlow AI Copilot!\n\n"
            f"I can assist you with:\n"
            f"- **Explaining claim status & AI review scores**\n"
            f"- **Underwriting validation rules**\n"
            f"- **Policy creation and payment tracking**\n"
            f"- **Simulating claim risk assessments**\n\n"
            f"> ⚙️ *Currently running in InsureFlow Expert Mode. Add an `OPENAI_API_KEY` in the top-right Settings modal for live ChatGPT streaming.*"
        )

    return {
        "reply": reply,
        "provider": "InsureFlow AI Engine (Heuristic)",
        "model": "insureflow-assistant",
    }
