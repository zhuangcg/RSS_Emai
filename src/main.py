import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.rss_email.config import get_settings
from src.rss_email.db import create_session_factory
from src.rss_email.email_client import EmailClient
from src.rss_email.workflow import run_cycle


def main() -> None:
    settings = get_settings()

    if not settings.rss_urls:
        print("RSS groups are empty; nothing to fetch.")
        return
    if not settings.smtp_host:
        print("SMTP settings are incomplete; set SMTP_* to send mail.")
        return

    SessionLocal = create_session_factory(settings.database_url)
    email_client = EmailClient(
        settings.smtp_host,
        settings.smtp_port,
        settings.smtp_user,
        settings.smtp_pass,
        settings.smtp_sender,
    )

    if settings.enable_schedule:
        try:
            from apscheduler.schedulers.blocking import BlockingScheduler
            from apscheduler.triggers.cron import CronTrigger
            try:
                from zoneinfo import ZoneInfo
                tz = ZoneInfo(settings.schedule_tz)
            except Exception:
                tz = None

            scheduler = BlockingScheduler(timezone=tz)

            def job():
                with SessionLocal() as session:
                    result = run_cycle(settings, session, email_client)
                    sent = result.get("sent", 0)
                    groups = result.get("groups", 0)
                    print(
                        f"[Scheduled] Ingested {result['ingested']} new items; sent {sent} papers across {groups} groups."
                    )

            hour, minute = map(int, settings.schedule_time.split(":"))
            trigger = CronTrigger(hour=hour, minute=minute)
            scheduler.add_job(job, trigger)
            print(
                f"Scheduler running: daily at {settings.schedule_time} ({settings.schedule_tz})"
            )
            scheduler.start()
            return
        except Exception as e:
            print(f"Failed to start scheduler: {e}. Falling back to one-off run.")

    with SessionLocal() as session:
        result = run_cycle(settings, session, email_client)
        sent = result.get("sent", 0)
        groups = result.get("groups", 0)
        print(
            f"Ingested {result['ingested']} new items; sent {sent} papers across {groups} groups."
        )


if __name__ == "__main__":
    main()
