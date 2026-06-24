import httpx
from core.config import getSettings
from core.logging import logger

JIRA_SUMMARY_MAX_LENGTH = 255


def normalize_jira_domain(domain: str) -> str:
    """Return a Jira base URL with scheme and no trailing slash."""
    normalized = domain.strip().rstrip("/")
    if not normalized.startswith("http"):
        normalized = f"https://{normalized}"
    return normalized


def build_jira_browse_url(ticket_key: str, *, domain: str | None = None) -> str:
    """Build a browse URL for a Jira issue key."""
    settings = getSettings()
    raw_domain = domain or settings.JIRA_DOMAIN
    if not raw_domain:
        return ""
    return f"{normalize_jira_domain(raw_domain)}/browse/{ticket_key}"


def text_to_adf(text: str) -> dict:
    """Convert plain text to Atlassian Document Format required by Jira Cloud API v3."""
    lines = text.split("\n")
    content: list[dict] = []
    for index, line in enumerate(lines):
        if line:
            content.append({"type": "text", "text": line})
        if index < len(lines) - 1:
            content.append({"type": "hardBreak"})
    if not content:
        content = [{"type": "text", "text": "(no description)"}]
    return {
        "type": "doc",
        "version": 1,
        "content": [{"type": "paragraph", "content": content}],
    }


def build_issue_description(
    description: str,
    *,
    user_id: str | None = None,
    conversation_id: str | None = None,
) -> str:
    """Append reporter metadata so engineering can trace the chat session."""
    sections = [description.strip()]
    metadata_lines = []
    if user_id:
        metadata_lines.append(f"Reporter user ID: {user_id}")
    if conversation_id:
        metadata_lines.append(f"Conversation ID: {conversation_id}")
    if metadata_lines:
        sections.append("---\nReported via chatbot\n" + "\n".join(metadata_lines))
    return "\n\n".join(section for section in sections if section)


async def create_jira_issue(
    title: str,
    description: str,
    *,
    user_id: str | None = None,
    conversation_id: str | None = None,
) -> str:
    """
    Creates a Jira issue in the configured project using the REST API.
    Returns the issue key (e.g. KAN-123).
    """
    settings = getSettings()

    if not all(
        [
            settings.JIRA_DOMAIN,
            settings.JIRA_EMAIL,
            settings.JIRA_API_TOKEN,
            settings.JIRA_PROJECT_KEY,
        ]
    ):
        logger.error("Jira credentials not fully configured.")
        raise ValueError(
            "Jira credentials not configured. Please configure JIRA_DOMAIN, JIRA_EMAIL, JIRA_API_TOKEN, and JIRA_PROJECT_KEY."
        )

    # Handle domain with or without https prefix
    domain = normalize_jira_domain(settings.JIRA_DOMAIN)

    url = f"{domain}/rest/api/3/issue"

    auth = (settings.JIRA_EMAIL, settings.JIRA_API_TOKEN)
    full_description = build_issue_description(
        description, user_id=user_id, conversation_id=conversation_id
    )

    payload = {
        "fields": {
            "project": {"key": settings.JIRA_PROJECT_KEY},
            "summary": title.strip()[:JIRA_SUMMARY_MAX_LENGTH],
            "description": text_to_adf(full_description),
            "issuetype": {"name": settings.JIRA_ISSUE_TYPE},
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, auth=auth, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            issue_key = data.get("key")
            if not issue_key:
                raise ValueError("Jira API response missing issue key")
            return issue_key
        except httpx.RequestError as e:
            logger.error(f"Jira request failed: {e}")
            raise Exception("Failed to connect to Jira API.") from e
        except httpx.HTTPStatusError as e:
            logger.error(f"Jira API error response: {e.response.text}")
            raise Exception(
                f"Jira API returned error status: {e.response.status_code}"
            ) from e
