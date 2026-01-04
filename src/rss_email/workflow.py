from datetime import datetime, timedelta
from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import Settings
from .db import Paper, get_paper
from .email_client import EmailClient
from .rss_client import fetch_feed


def _resolve_recipients(settings: Settings, group_name: str) -> tuple[List[str], List[str], List[str]]:
    has_override = settings.group_recipients and group_name in settings.group_recipients
    if has_override:
        override = settings.group_recipients.get(group_name, {}) or {}
        to_list = override.get("to", []) or []
        cc_list = override.get("cc", []) or []
        bcc_list = override.get("bcc", []) or []
        return to_list, cc_list, bcc_list
    raise ValueError(f"No recipient configuration for group '{group_name}'")


def ingest_feeds(settings: Settings, session: Session) -> int:
    created = 0
    for group_name, urls in settings.rss_groups.items():
        for url in urls:
            try:
                entries = fetch_feed(url)
                for entry in entries:
                    if get_paper(session, entry.fingerprint):
                        continue
                    paper = Paper(
                        id=entry.fingerprint,
                        title=entry.title,
                        authors=entry.authors,
                        summary=entry.summary,
                        link=entry.link,
                        published_at=entry.published_at,
                        source=url,
                        inserted_at=datetime.utcnow(),
                    )
                    session.add(paper)
                    created += 1
            except Exception as e:
                print(f"[ERROR] Failed to ingest feed {url}: {e}")
                continue
    session.commit()
    return created


def _format_date(dt: datetime | None) -> str:
    if not dt:
        return ""
    return dt.strftime("%Y-%m-%d %H:%M")


def _build_email_html(papers: List[Paper], group_name: str) -> str:
    items = []
    for p in papers:
        published = _format_date(p.published_at)
        items.append(
            f"<li><a href='{p.link}'>{p.title}</a>"
            f"<br/><small>{p.authors or ''} | {published} | {p.source}</small>"
            f"<p>{p.summary}</p></li>"
        )
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    body = """
    <html>
        <body>
            <p>Latest papers for group: {group}</p>
            <ul>
                {items}
            </ul>
            <p>Generated at {ts}</p>
        </body>
    </html>
    """
    return body.format(items="\n".join(items), ts=timestamp, group=group_name)


def _build_email_text(papers: List[Paper], group_name: str) -> str:
    lines = []
    lines.append(f"Group: {group_name}\n")
    for p in papers:
        published = _format_date(p.published_at)
        lines.append(f"{p.title}\n{p.authors or 'Unknown authors'} | {published} | {p.source}\n{p.link}\n")
    return "\n".join(lines)


def _build_no_new_html(group_name: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    body = """
    <html>
      <body>
        <p>No new papers for group: {group}</p>
        <p>Generated at {ts}</p>
      </body>
    </html>
    """
    return body.format(group=group_name, ts=timestamp)


def _build_no_new_text(group_name: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"No new papers for group: {group_name}\nGenerated at {timestamp}"


def _get_unsent_recent(session: Session, days: int = 15) -> List[Paper]:
    cutoff = datetime.now() - timedelta(days=days)
    stmt = (
        select(Paper)
        .where(Paper.sent.is_(False))
        .where(Paper.inserted_at >= cutoff)
        .order_by(Paper.published_at.desc().nullslast(), Paper.created_at.desc())
    )
    return list(session.execute(stmt).scalars())


def send_unsent(settings: Settings, session: Session, email_client: EmailClient) -> dict:
    unsent = _get_unsent_recent(session, days=15)

    grouped: Dict[str, List[Paper]] = {}
    for paper in unsent:
        group = settings.url_to_group.get(paper.source, "Default")
        grouped.setdefault(group, []).append(paper)

    configured_groups = list(settings.rss_groups.keys()) if settings.rss_groups else ["Default"]
    all_groups = list({*configured_groups, *grouped.keys()})

    total_sent = 0
    for group_name in all_groups:
        papers = grouped.get(group_name, [])
        batch = papers[: settings.batch_limit] if settings.batch_limit else papers
        to_list, cc_list, bcc_list = _resolve_recipients(settings, group_name)

        print(
            f"[Mail Plan] Group={group_name} To={to_list or ['(none)']} CC={cc_list or ['(none)']} BCC={bcc_list or ['(none)']} Items={len(batch)}"
        )

        if batch:
            subject = f"{settings.mail_subject_prefix} [{group_name}] {len(batch)} new papers"
            html_body = _build_email_html(batch, group_name)
            text_body = _build_email_text(batch, group_name)
            email_client.send(to_list, subject, html_body, text_body, cc=cc_list, bcc=bcc_list)
            for p in batch:
                p.sent = True
            total_sent += len(batch)
        else:
            subject = f"{settings.mail_subject_prefix} [{group_name}] No new papers"
            html_body = _build_no_new_html(group_name)
            text_body = _build_no_new_text(group_name)
            email_client.send(to_list, subject, html_body, text_body, cc=cc_list, bcc=bcc_list)

    session.commit()
    return {"sent": total_sent, "groups": len(all_groups)}


def run_cycle(settings: Settings, session: Session, email_client: EmailClient) -> dict:
    ingested = ingest_feeds(settings, session)
    sent_info = send_unsent(settings, session, email_client)
    return {"ingested": ingested, **sent_info}
