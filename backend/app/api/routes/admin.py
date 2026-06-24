from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Security, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth.service import get_current_active_user
from core.database import get_db
from core.errors import (
    BadRequest,
    ConflictError,
    NotFoundError,
    ServiceUnavailableError,
    UnknownError,
)
from core.logging import logger
from schemas.models import PendingJiraTicket, User
from schemas.schema import PendingJiraTicketResponse, AdminActionResponse
from services.jira import create_jira_issue
from services.email import send_approval_email, send_rejection_email

admin_router = APIRouter(prefix="/admin")


async def _fetch_ticket_for_update(
    db: AsyncSession, ticket_id: UUID
) -> PendingJiraTicket | None:
    """Load a ticket row with a pessimistic lock for state transitions."""
    stmt = (
        select(PendingJiraTicket)
        .options(selectinload(PendingJiraTicket.user))
        .where(PendingJiraTicket.id == ticket_id)
        .with_for_update()
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


@admin_router.get(
    "/pending-tickets",
    response_model=list[PendingJiraTicketResponse],
    status_code=status.HTTP_200_OK,
)
async def get_pending_tickets(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Security(get_current_active_user, scopes=["ticket:manage"]),
):
    """Retrieve all pending Jira tickets."""
    stmt = (
        select(PendingJiraTicket)
        .options(selectinload(PendingJiraTicket.user))
        .where(PendingJiraTicket.status == "pending")
        .order_by(PendingJiraTicket.created_at.desc())
    )
    result = await db.execute(stmt)
    tickets = result.scalars().all()

    return [
        PendingJiraTicketResponse(
            id=ticket.id,
            user_id=ticket.user_id,
            user_email=ticket.user.email,
            title=ticket.title,
            description=ticket.description,
            status=ticket.status,
            created_at=ticket.created_at,
        )
        for ticket in tickets
    ]


@admin_router.post(
    "/approve-ticket/{ticket_id}",
    response_model=AdminActionResponse,
    status_code=status.HTTP_200_OK,
)
async def approve_ticket(
    ticket_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Security(get_current_active_user, scopes=["ticket:manage"]),
):
    """Approve a pending ticket, create a Jira issue, and notify the user via email."""
    ticket = await _fetch_ticket_for_update(db, ticket_id)

    if not ticket:
        raise NotFoundError("Pending ticket not found")

    if ticket.jira_key:
        if ticket.status != "approved":
            ticket.status = "approved"
            ticket.approved_at = ticket.approved_at or datetime.now(timezone.utc)
            ticket.approved_by = ticket.approved_by or current_user.id
            await db.commit()

        return AdminActionResponse(
            success=True,
            message=f"Ticket was already approved. Jira issue: {ticket.jira_key}",
            jira_key=ticket.jira_key,
        )

    if ticket.status == "processing":
        raise ConflictError("Ticket approval is already in progress.")

    if ticket.status != "pending":
        raise BadRequest(
            f"Ticket cannot be approved because its status is '{ticket.status}'"
        )

    try:
        # Hold the row lock for the full transition to prevent duplicate Jira issues.
        ticket.status = "processing"
        await db.flush()

        jira_key = await create_jira_issue(
            title=ticket.title,
            description=ticket.description,
            user_id=str(ticket.user_id),
            conversation_id=(
                str(ticket.conversation_id) if ticket.conversation_id else None
            ),
        )

        ticket.status = "approved"
        ticket.jira_key = jira_key
        ticket.approved_at = datetime.now(timezone.utc)
        ticket.approved_by = current_user.id
        await db.commit()

        email_sent = await send_approval_email(
            user_email=ticket.user.email,
            ticket_key=jira_key,
            ticket_title=ticket.title,
        )

        msg = "Ticket successfully approved and Jira issue created."
        if not email_sent:
            msg += " However, the email notification failed to send."

        return AdminActionResponse(
            success=True,
            message=msg,
            jira_key=jira_key,
        )

    except (BadRequest, ConflictError, NotFoundError, ServiceUnavailableError):
        await db.rollback()
        raise
    except ValueError:
        await db.rollback()
        logger.exception("Jira is not configured while approving ticket %s", ticket_id)
        raise ServiceUnavailableError(
            "Jira integration is not configured. Please contact support."
        )
    except Exception:
        await db.rollback()
        logger.exception("Failed to approve ticket %s", ticket_id)
        raise ServiceUnavailableError(
            "Unable to create Jira issue. Please try again later."
        )


@admin_router.post(
    "/reject-ticket/{ticket_id}",
    response_model=AdminActionResponse,
    status_code=status.HTTP_200_OK,
)
async def reject_ticket(
    ticket_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Security(get_current_active_user, scopes=["ticket:manage"]),
):
    """Reject a pending ticket and notify the user via email."""
    ticket = await _fetch_ticket_for_update(db, ticket_id)

    if not ticket:
        raise NotFoundError("Pending ticket not found")

    if ticket.status == "processing":
        raise ConflictError("Cannot reject a ticket while approval is in progress.")

    if ticket.status != "pending":
        raise BadRequest(
            f"Ticket cannot be rejected because its status is '{ticket.status}'"
        )

    try:
        ticket.status = "rejected"
        await db.commit()

        email_sent = await send_rejection_email(
            user_email=ticket.user.email,
            ticket_title=ticket.title,
        )

        msg = "Ticket successfully rejected and user notified."
        if not email_sent:
            msg = "Ticket successfully rejected. However, the email notification failed to send."

        return AdminActionResponse(
            success=True,
            message=msg,
        )

    except (BadRequest, ConflictError, NotFoundError):
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        logger.exception("Failed to reject ticket %s", ticket_id)
        raise UnknownError(
            "Failed to process ticket rejection. Please try again or contact support."
        )
