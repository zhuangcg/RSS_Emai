"""Utility script to verify SMTP email delivery using current .env settings.

Uses the first group in GROUP_RECIPIENTS_FILE for recipients (to/cc/bcc).
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.rss_email.config import get_settings
from src.rss_email.email_client import EmailClient


def main() -> None:
    settings = get_settings()

    if not settings.smtp_host:
        print("SMTP settings are incomplete; set SMTP_* in your .env before testing.")
        return

    if not settings.group_recipients:
        print("GROUP_RECIPIENTS_FILE is missing or empty; cannot send test email.")
        return

    first_group = next(iter(settings.group_recipients.keys()))
    recips = settings.group_recipients[first_group]
    to_list = recips.get("to", [])
    cc_list = recips.get("cc", [])
    bcc_list = recips.get("bcc", [])
    if not (to_list or cc_list or bcc_list):
        print(f"Group '{first_group}' has no recipients configured; cannot send test email.")
        return

    email_client = EmailClient(
        settings.smtp_host,
        settings.smtp_port,
        settings.smtp_user,
        settings.smtp_pass,
        settings.smtp_sender,
    )

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    subject = f"{settings.mail_subject_prefix} SMTP test"
    html_body = f"<p>This is a test email sent at {now}.</p>"
    text_body = f"This is a test email sent at {now}."

    email_client.send(
        to_list,
        subject,
        html_body,
        text_body,
        cc=cc_list,
        bcc=bcc_list,
    )
    all_targets = to_list + cc_list + bcc_list
    print(f"Sent test email to group '{first_group}': {', '.join(all_targets)}")


if __name__ == "__main__":
    main()
