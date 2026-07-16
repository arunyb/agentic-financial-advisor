import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.orchestrator import run_advisory_pipeline
from app.api.deps import get_current_user
from app.core.logging import get_logger
from app.db import models
from app.db.session import get_db
from app.schemas.schemas import AgentStepOut, ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])
logger = get_logger("chat")


def _run_pipeline_safely(db: Session, user: models.User, message: str) -> dict:
    """
    The agents themselves already degrade gracefully on known LLM-availability
    issues (see PlannerAgent/RecommendationAgent). This is the last line of
    defense for anything unexpected (network blips, DB hiccups mid-pipeline,
    a future agent that doesn't handle its own errors yet) - callers should
    get a clean 503 with a useful message, never a raw traceback.
    """
    try:
        return run_advisory_pipeline(db=db, user=user, user_message=message)
    except Exception:
        logger.exception("advisory_pipeline_failed", user_id=str(user.id))
        raise HTTPException(
            status_code=503,
            detail="The advisor pipeline hit an unexpected error. Please try again in a moment.",
        )


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.session_id:
        session = (
            db.query(models.ChatSession)
            .filter(models.ChatSession.id == payload.session_id, models.ChatSession.user_id == current_user.id)
            .first()
        )
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
    else:
        session = models.ChatSession(user_id=current_user.id, title=payload.message[:60])
        db.add(session)
        db.commit()
        db.refresh(session)

    db.add(models.ChatMessage(session_id=session.id, role="user", content=payload.message))
    db.commit()

    result = _run_pipeline_safely(db, current_user, payload.message)

    for step in result["trace"]:
        db.add(
            models.ChatMessage(
                session_id=session.id,
                role="agent_trace",
                content=step["summary"],
                agent_name=step["agent"],
                trace_json=json.dumps(step["detail"], default=str),
            )
        )
    db.add(models.ChatMessage(session_id=session.id, role="assistant", content=result["reply"]))
    db.commit()

    logger.info("chat_turn_complete", session_id=str(session.id), user_id=str(current_user.id))

    return ChatResponse(
        session_id=session.id,
        reply=result["reply"],
        agent_trace=[AgentStepOut(**step) for step in result["trace"]],
        citations=result["citations"],
    )


@router.get("/sessions/{session_id}/messages")
def get_messages(
    session_id: uuid.UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(models.ChatSession)
        .filter(models.ChatSession.id == session_id, models.ChatSession.user_id == current_user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "agent_name": m.agent_name,
            "created_at": m.created_at,
        }
        for m in session.messages
    ]
