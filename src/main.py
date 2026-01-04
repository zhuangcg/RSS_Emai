import sys
from datetime import datetime
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
            from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
            try:
                from zoneinfo import ZoneInfo
                tz = ZoneInfo(settings.schedule_tz)
            except Exception:
                tz = None

            scheduler = BlockingScheduler(
                timezone=tz,
                coalesce=True,
                max_instances=1,
                misfire_grace_time=3600
            )

            # Parse schedule_time (format: "HH:MM")
            try:
                schedule_time = settings.schedule_time.strip()
                if ":" not in schedule_time:
                    raise ValueError(f"Invalid SCHEDULE_TIME format: {schedule_time}. Expected 'HH:MM'")
                hour_str, minute_str = schedule_time.split(":", 1)
                hour = int(hour_str)
                minute = int(minute_str)
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    raise ValueError(f"Invalid time values: {schedule_time}")
            except Exception as e:
                print(f"Error parsing SCHEDULE_TIME '{settings.schedule_time}': {e}")
                print("Falling back to 08:30")
                hour, minute = 8, 30

            def job_full_cycle():
                start_time = datetime.now()
                print(f"[{start_time.strftime('%Y-%m-%d %H:%M:%S')}] Starting scheduled job...")
                try:
                    with SessionLocal() as session:
                        result = run_cycle(settings, session, email_client)
                        sent = result.get("sent", 0)
                        groups = result.get("groups", 0)
                        end_time = datetime.now()
                        duration = (end_time - start_time).total_seconds()
                        print(
                            f"[{end_time.strftime('%Y-%m-%d %H:%M:%S')}] "
                            f"Completed in {duration:.2f}s: "
                            f"Ingested {result['ingested']} new items; "
                            f"sent {sent} papers across {groups} groups."
                        )
                except Exception as e:
                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()
                    print(f"[{end_time.strftime('%Y-%m-%d %H:%M:%S')}] Job failed after {duration:.2f}s: {e}")
                    raise

            # Add event listeners for monitoring
            def job_listener(event):
                if event.exception:
                    print(f"[SCHEDULER ERROR] Job crashed: {event.exception}")
                elif event.code == EVENT_JOB_MISSED:
                    print(f"[SCHEDULER WARNING] Job was missed at {datetime.now()}")
                elif event.code == EVENT_JOB_EXECUTED:
                    print(f"[SCHEDULER INFO] Job executed successfully")

            scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED)

            # Schedule daily execution at the specified time
            scheduler.add_job(
                job_full_cycle,
                trigger=CronTrigger(hour=hour, minute=minute, timezone=tz),
                id="daily_cycle",
                misfire_grace_time=3600,
                coalesce=True,
                max_instances=1
            )

            print(
                f"Scheduler running. Daily execution at {hour:02d}:{minute:02d} "
                f"(timezone={settings.schedule_tz})."
            )
            print("Starting immediately for first run...")

            # Run immediately on startup
            job_full_cycle()

            print("Scheduler started. Waiting for next scheduled run...")
            scheduler.start()
            return
        except Exception as e:
            print(f"Failed to start scheduler: {e}. Falling back to one-off run.")

    # Fallback: one-off run
    with SessionLocal() as session:
        result = run_cycle(settings, session, email_client)
        sent = result.get("sent", 0)
        groups = result.get("groups", 0)
        print(
            f"Ingested {result['ingested']} new items; sent {sent} papers across {groups} groups."
        )


if __name__ == "__main__":
    main()
