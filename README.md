# RSS to Email (Papers) / RSS 邮件推送

EN: For researchers, students, and avid learners, staying on top of the latest publications can feel like a full-time job. This tool automates that process. Simply configure the RSS feeds from your favorite journals or topics, and let it send a curated list of new papers to your inbox daily. Reclaim your time for deep work instead of endless browsing.

ZH: 科研人员、学生和知识爱好者常被追踪最新论文的负担所困扰。本工具旨在将此过程自动化：您只需配置关注期刊或主题的RSS源，即可每天在邮箱中收到一份精心整理的最新论文列表。将您的时间从繁琐的信息检索中解放出来，更专注于深度思考。


---
## Environment Requirements (EN)
- Python 3.10-3.12 (greater than 3.12 may have SQLAlchemy compatibility issues).
- Dependencies listed in `requirements.txt`.

## Who It’s For & What You Get (EN)
- Research groups / labs tracking journals and conferences: fetch multiple RSS sources, deduplicate, store in SQLite, and deliver grouped digest emails (HTML + text) per topic.
- Teams with separate recipient lists: per-group to/cc/bcc via `GROUP_RECIPIENTS_FILE`, with batch limits to avoid inbox flooding.
- Busy schedulers: daily automation via APScheduler; falls back to one-off runs if scheduling is off.
- Security-conscious users: secrets and recipient files stay out of git (`.env`, `group_recipients.json`), with safe templates for sharing.
- Lightweight deployers: SQLite + stdlib email works on Windows/macOS/Linux with minimal setup (copy `.env.example`, add `rss_groups.json` + recipients, run).

## Quick Start (EN)
1) Create venv & install
```bash
python -m venv .venv
.venv/Scripts/activate  # Windows
pip install -r requirements.txt
```
2) Copy env template
```bash
cp .env.example .env
```
3) Prepare `rss_groups.json` (required)
```json
{
  "Elsevier": ["https://example.com/rss1"],
  "Springer": ["https://example.com/rss2"]
}
```
Optional per-group recipients (`group_recipients.json`):
```json
{
  "Elsevier": {"to": ["elsevier_to@example.com"], "cc": ["elsevier_cc@example.com"], "bcc": []},
  "Springer": {"to": ["springer_to@example.com"], "cc": [], "bcc": ["springer_bcc@example.com"]}
}
```
4) Run once (fetch + send)
```bash
python -m src.main
```
5) Send test email (uses first available group recipients)
```bash
python -m src.test_email
```
6) Optional daily schedule at 08:30
- Set `ENABLE_SCHEDULE=true`, `SCHEDULE_TIME=08:30`, `SCHEDULE_TZ=Asia/Shanghai`
- Then run `python -m src.main` to start the scheduler.
7) Per-group emails
- Sources come only from `rss_groups.json` (`RSS_GROUPS_FILE` can change the path).
- Each group gets its own email; if no new papers, a "no new papers" notice is sent.

## Configuration (EN)
- `RSS_GROUPS_FILE`: required; JSON file mapping group -> list of RSS URLs (default `rss_groups.json`).
- `GROUP_RECIPIENTS_FILE`: required for sending; JSON mapping group -> {to, cc, bcc}. If a group has empty lists, sending will fail for that group.
- `DATABASE_URL`: SQLAlchemy URL (default `sqlite:///data/rss.db`).
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`: SMTP credentials.
- `SMTP_SENDER`: From address.
- (Recipients) Use `GROUP_RECIPIENTS_FILE` only; define `to/cc/bcc` per group.
- `MAIL_SUBJECT_PREFIX`: optional subject prefix.
- `BATCH_LIMIT`: max unsent items per email (default 20; empty means no limit).
- `ENABLE_SCHEDULE`: `true/false` to enable APScheduler.
- `SCHEDULE_TIME`: `HH:MM` (default `08:30`).
- `SCHEDULE_TZ`: timezone (default `Asia/Shanghai`).
- `FETCH_INTERVAL_MINUTES`: interval (minutes) to fetch RSS when scheduling is enabled (default 1440 = 24h).
- `SEND_INTERVAL_MINUTES`: interval (minutes) to send queued papers when scheduling is enabled (default 1440 = 24h).

## Notes (EN)
- Items are deduped by fingerprint of entry ID/link + published time.
- SQLite DB lives under `data/` by default; folder auto-created.
- Scheduler can be internal (APScheduler) or external (cron/Task Scheduler).

### Security & Privacy (EN)
- Do not commit real secrets or recipient lists. `.gitignore` ignores `.env` and `group_recipients.json`.
- Keep `GROUP_RECIPIENTS_FILE` outside the repo if needed (e.g., `C:\Users\you\secrets\group_recipients.json`).
- Use `.env.example` as a template; copy to `.env` and fill values locally.

---
## 环境要求 (ZH)
- Python 3.10-3.12, 大于3.12可能存在SQLAlchemy兼容性问题。
- 依赖见 `requirements.txt`。

## 适用人群与价值 (ZH)
- 研究/实验室团队或个人：按主题分组抓取多路 RSS，指纹去重后存入 SQLite，并按分组发送 HTML + 文本摘要邮件。
- 多收件人场景：`GROUP_RECIPIENTS_FILE` 为各分组配置 to/cc/bcc，批次上限可控，避免邮箱轰炸。
- 需要定时的用户：APScheduler 支持每日自动运行，关闭定时则回退单次执行。
- 注重安全的团队：凭据与收件人文件不入库（`.env`、`group_recipients.json` 已忽略），提供示例模板便于安全分享。
- 追求轻量部署：SQLite + 标准库邮件，跨平台快速落地；复制 `.env.example`，准备 `rss_groups.json` 与收件人文件即可运行。

## 快速开始 (ZH)
1）创建虚拟环境并安装依赖
```bash
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
```
2）复制环境模板
```bash
cp .env.example .env
```
3）准备必需的 `rss_groups.json`，示例：
```json
{
  "Elsevier": ["https://example.com/rss1"],
  "Springer": ["https://example.com/rss2"]
}
```
4）单次运行（抓取 + 发送）
```bash
python -m src.main
```
5）测试邮件发送（使用分组收件人文件中的第一个分组）
```bash
python -m src.test_email
```
6）可选：每天 08:30 定时
- 设置 `ENABLE_SCHEDULE=true`、`SCHEDULE_TIME=08:30`、`SCHEDULE_TZ=Asia/Shanghai`
- 运行 `python -m src.main` 启动调度。
7）按分组发送
- 仅从 `rss_groups.json` 读取源（可用 `RSS_GROUPS_FILE` 指定路径）。
- 可选 `group_recipients.json` 为分组设置不同收件人，结构：`{"Group": {"to": [..], "cc": [..], "bcc": [..]}}`（可用 `GROUP_RECIPIENTS_FILE` 指定路径）。
- 每个分组单独邮件；若无新论文，会发送“无新论文”提醒。

## 配置项 (ZH)
- `RSS_GROUPS_FILE`：必填，JSON 文件，键为分组名、值为 RSS 列表（默认 `rss_groups.json`）。
- `DATABASE_URL`：数据库连接，默认 SQLite `sqlite:///data/rss.db`。
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`：SMTP 凭据。
- `SMTP_SENDER`：发件人地址。
- （收件人）仅通过 `GROUP_RECIPIENTS_FILE` 配置各分组的 `to/cc/bcc`；若某分组为空将导致该分组无法发送。
- `MAIL_SUBJECT_PREFIX`：主题前缀。
- `BATCH_LIMIT`：单次发送的未发送论文上限（默认 20，留空表示不限制）。
- `ENABLE_SCHEDULE`：是否启用 APScheduler。
- `SCHEDULE_TIME`：发送时间，格式 `HH:MM`，默认 `08:30`。
- `SCHEDULE_TZ`：时区，默认 `Asia/Shanghai`。
- `FETCH_INTERVAL_MINUTES`：启用调度时，抓取 RSS 的分钟间隔（默认 1440，即 24 小时）。
- `SEND_INTERVAL_MINUTES`：启用调度时，发送邮件的分钟间隔（默认 1440，即 24 小时）。
 - `GROUP_RECIPIENTS_FILE`：必填（发送所需），按分组指定 `to/cc/bcc`；若该分组为空则该分组无法发送。

## 说明 (ZH)
- 通过条目 ID/链接与发布时间指纹去重。
- 默认 SQLite 数据库位于 `data/`，目录自动创建。
- 可使用内置 APScheduler 或外部计划任务（cron/任务计划程序）。

### 安全与隐私 (ZH)
- 请勿提交真实的凭据与收件人列表。仓库已通过 `.gitignore` 忽略 `.env` 与 `group_recipients.json`。
- 如需更安全，可将 `GROUP_RECIPIENTS_FILE` 放在仓库外部路径（如 `C:\Users\you\secrets\group_recipients.json`）。
- 使用 `.env.example` 作为模板，在本地复制为 `.env` 并填写实际值。
## 故障排查 (Troubleshooting)

### APScheduler Misfire 错误
如果遇到类似以下错误：
```
Run time of job "main.<locals>.job_full_cycle" was missed by 0:00:01.233123
```

**原因：** 任务执行时间过长，超过了下一次调度时间。

**解决方案：**
1. **已修复：** 代码已更新，增加了 `misfire_grace_time` 到3600秒（1小时）
2. **运行诊断工具：**
   ```bash
   python src/test_scheduler.py
   ```
   这将测试所有配置并报告潜在问题

3. **查看详细日志：**
   修复后的代码会输出执行时间：
   ```
   [2025-12-31 08:30:00] Starting scheduled job...
   [2025-12-31 08:30:45] Completed in 45.32s: Ingested 15 new items...
   ```

4. **优化建议：**
   - 如果执行时间超过5分钟，考虑调整到凌晨执行（`SCHEDULE_TIME=03:00`）
   - 检查慢速RSS源（诊断工具会标识出来）
   - 查看 [SCHEDULER_FIX.md](SCHEDULER_FIX.md) 了解详细修复说明
   - 查看 [CONFIG_RECOMMENDATIONS.md](CONFIG_RECOMMENDATIONS.md) 了解最佳实践

### 其他常见问题

**Q: RSS源获取失败**
```bash
# 测试单个RSS源
python -c "from src.rss_email.rss_client import fetch_feed; print(fetch_feed('YOUR_URL'))"
```

**Q: 数据库连接错误**
- 确保 `data/` 目录存在且可写
- SQLite文件路径正确（默认：`data/rss.db`）

**Q: 邮件发送失败**
- 验证SMTP配置（主机、端口、用户名、密码）
- 检查是否需要应用专用密码（如Gmail）
- 运行测试脚本：`python src/test_email.py`

**Q: 时区问题**
- Windows: 运行 `Get-TimeZone` 检查系统时区
- 确保 `SCHEDULE_TZ` 与服务器时区一致（如 `Asia/Shanghai`）

详细文档请参考：
- [SCHEDULER_FIX.md](SCHEDULER_FIX.md) - 调度器修复详解
- [CONFIG_RECOMMENDATIONS.md](CONFIG_RECOMMENDATIONS.md) - 配置和性能优化建议