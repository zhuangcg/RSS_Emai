import json
import os
import re
from dataclasses import dataclass
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv()


def _split_env(value: str) -> List[str]:
    parts = re.split(r"[,\n;]+", value)
    return [item.strip() for item in parts if item.strip()]


def _get_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _split_optional(value: str) -> List[str]:
    if not value:
        return []
    return _split_env(value)


def _dedup_preserve_order(items: List[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _parse_recipient_entry(value) -> List[str]:
    if isinstance(value, list):
        value = ",".join(str(v) for v in value)
    if not isinstance(value, str):
        return []
    return _dedup_preserve_order(_split_optional(value))


def _load_groups_from_file() -> Dict[str, List[str]]:
    path = os.getenv("RSS_GROUPS_FILE", "rss_groups.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"RSS groups file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("RSS groups file must contain a JSON object mapping group -> list of URLs")

    groups: Dict[str, List[str]] = {}
    for g, urls in data.items():
        if isinstance(urls, list):
            cleaned = [str(u).strip() for u in urls if str(u).strip()]
            if cleaned:
                groups[str(g)] = _dedup_preserve_order(cleaned)
    if not groups:
        raise ValueError("RSS groups file has no valid groups or URLs")
    return groups


def _load_group_recipients_from_file() -> Dict[str, Dict[str, List[str]]]:
    path = os.getenv("GROUP_RECIPIENTS_FILE")
    if not path:
        return {}
    if not os.path.exists(path):
        raise FileNotFoundError(f"Group recipients file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Group recipients file must be a JSON object mapping group -> recipients")

    result: Dict[str, Dict[str, List[str]]] = {}
    for group, rec in data.items():
        if not isinstance(rec, dict):
            continue
        to_list = _parse_recipient_entry(rec.get("to", ""))
        cc_list = _parse_recipient_entry(rec.get("cc", ""))
        bcc_list = _parse_recipient_entry(rec.get("bcc", ""))
        result[str(group)] = {"to": to_list, "cc": cc_list, "bcc": bcc_list}
    return result


def _build_url_maps(groups: Dict[str, List[str]]) -> tuple[Dict[str, str], List[str]]:
    url_to_group: Dict[str, str] = {}
    all_urls: List[str] = []
    for group_name, urls in groups.items():
        for u in urls:
            if u not in url_to_group:
                url_to_group[u] = group_name
            all_urls.append(u)
    dedup_urls = _dedup_preserve_order(all_urls)
    return url_to_group, dedup_urls


@dataclass
class Settings:
    rss_urls: List[str]
    rss_groups: Dict[str, List[str]]
    url_to_group: Dict[str, str]
    group_recipients: Dict[str, Dict[str, List[str]]]
    database_url: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_pass: str
    smtp_sender: str
    mail_subject_prefix: str
    batch_limit: int
    enable_schedule: bool
    schedule_time: str
    schedule_tz: str


def get_settings() -> Settings:
    groups = _load_groups_from_file()
    url_to_group, dedup_urls = _build_url_maps(groups)
    group_recipients = _load_group_recipients_from_file()

    if not group_recipients:
        raise ValueError("GROUP_RECIPIENTS_FILE is required and must define recipients per group")

    return Settings(
        rss_urls=dedup_urls,
        rss_groups=groups,
        url_to_group=url_to_group,
        group_recipients=group_recipients,
        database_url=os.getenv("DATABASE_URL", "sqlite:///data/rss.db"),
        smtp_host=os.getenv("SMTP_HOST", ""),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_user=os.getenv("SMTP_USER", ""),
        smtp_pass=os.getenv("SMTP_PASS", ""),
        smtp_sender=os.getenv("SMTP_SENDER", ""),
        mail_subject_prefix=os.getenv("MAIL_SUBJECT_PREFIX", "[Papers]"),
        batch_limit=int(os.getenv("BATCH_LIMIT", "20")),
        enable_schedule=_get_bool(os.getenv("ENABLE_SCHEDULE"), False),
        schedule_time=os.getenv("SCHEDULE_TIME", "08:30"),
        schedule_tz=os.getenv("SCHEDULE_TZ", "Asia/Shanghai"),
    )
