"""
RSS Email Scheduler 诊断测试工具

用途：测试调度器配置和任务执行性能
运行：python src/test_scheduler.py
"""

import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.rss_email.config import get_settings
from src.rss_email.db import create_session_factory
from src.rss_email.workflow import ingest_feeds


def test_configuration():
    """测试配置加载"""
    print("=" * 60)
    print("1. 测试配置加载")
    print("=" * 60)
    
    try:
        settings = get_settings()
        print(f"✅ 配置加载成功")
        print(f"   - RSS组数量: {len(settings.rss_groups)}")
        print(f"   - RSS源总数: {len(settings.rss_urls)}")
        print(f"   - 调度启用: {settings.enable_schedule}")
        print(f"   - 调度时间: {settings.schedule_time}")
        print(f"   - 时区: {settings.schedule_tz}")
        print(f"   - 数据库: {settings.database_url}")
        print(f"   - SMTP主机: {settings.smtp_host}")
        return settings
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return None


def test_timezone(settings):
    """测试时区配置"""
    print("\n" + "=" * 60)
    print("2. 测试时区配置")
    print("=" * 60)
    
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(settings.schedule_tz)
        now = datetime.now(tz)
        print(f"✅ 时区配置正确")
        print(f"   - 时区: {settings.schedule_tz}")
        print(f"   - 当前时间: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        return True
    except Exception as e:
        print(f"❌ 时区配置失败: {e}")
        print(f"   提示: 请检查 SCHEDULE_TZ 环境变量")
        return False


def test_database(settings):
    """测试数据库连接"""
    print("\n" + "=" * 60)
    print("3. 测试数据库连接")
    print("=" * 60)
    
    try:
        SessionLocal = create_session_factory(settings.database_url)
        with SessionLocal() as session:
            # 简单测试查询
            from sqlalchemy import text
            result = session.execute(text("SELECT 1"))
            result.fetchone()
        print(f"✅ 数据库连接成功")
        print(f"   - URL: {settings.database_url}")
        return SessionLocal
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return None


def test_rss_feeds(settings):
    """测试RSS源获取"""
    print("\n" + "=" * 60)
    print("4. 测试RSS源获取（前3个）")
    print("=" * 60)
    
    from src.rss_email.rss_client import fetch_feed
    
    test_urls = settings.rss_urls[:3]
    results = []
    
    for url in test_urls:
        start = time.time()
        try:
            entries = fetch_feed(url)
            elapsed = time.time() - start
            status = "✅"
            message = f"获取成功，{len(entries)} 条目，耗时 {elapsed:.2f}s"
            if elapsed > 10:
                status = "⚠️"
                message += " (响应较慢)"
            results.append((status, url, message))
        except Exception as e:
            elapsed = time.time() - start
            results.append(("❌", url, f"获取失败: {e}"))
    
    for status, url, message in results:
        print(f"{status} {url}")
        print(f"   {message}")
    
    return results


def test_full_cycle(settings):
    """测试完整执行周期"""
    print("\n" + "=" * 60)
    print("5. 测试完整执行周期（不发送邮件）")
    print("=" * 60)
    
    try:
        SessionLocal = create_session_factory(settings.database_url)
        start_time = time.time()
        
        print("开始执行...")
        with SessionLocal() as session:
            # 只测试ingest，不发送邮件
            ingested = ingest_feeds(settings, session)
            elapsed = time.time() - start_time
            
        print(f"✅ 执行完成")
        print(f"   - 新增条目: {ingested}")
        print(f"   - 执行时间: {elapsed:.2f}s")
        
        if elapsed > 300:  # 5分钟
            print(f"   ⚠️ 警告: 执行时间较长，可能需要优化")
        elif elapsed > 600:  # 10分钟
            print(f"   ❌ 错误: 执行时间过长，严重性能问题")
        else:
            print(f"   ✅ 执行时间正常")
        
        return elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ 执行失败 (耗时 {elapsed:.2f}s): {e}")
        return None


def test_scheduler_config(settings):
    """测试调度器配置"""
    print("\n" + "=" * 60)
    print("6. 测试调度器配置")
    print("=" * 60)
    
    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.cron import CronTrigger
        from zoneinfo import ZoneInfo
        
        tz = ZoneInfo(settings.schedule_tz)
        
        # 解析调度时间
        schedule_time = settings.schedule_time.strip()
        hour_str, minute_str = schedule_time.split(":", 1)
        hour = int(hour_str)
        minute = int(minute_str)
        
        # 创建调度器（不启动）
        scheduler = BlockingScheduler(
            timezone=tz,
            coalesce=True,
            max_instances=1,
            misfire_grace_time=3600
        )
        
        print(f"✅ 调度器配置正确")
        print(f"   - 时区: {settings.schedule_tz}")
        print(f"   - 执行时间: {hour:02d}:{minute:02d}")
        print(f"   - 最大实例数: 1")
        print(f"   - Misfire宽限时间: 3600秒 (1小时)")
        print(f"   - Coalesce: True (合并错过的运行)")
        
        # 计算下次执行时间
        now = datetime.now(tz)
        from datetime import timedelta
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
        
        print(f"   - 下次执行: {next_run.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        return True
    except Exception as e:
        print(f"❌ 调度器配置失败: {e}")
        return False


def generate_report(settings, test_results):
    """生成诊断报告"""
    print("\n" + "=" * 60)
    print("诊断报告总结")
    print("=" * 60)
    
    all_passed = all(test_results.values())
    
    if all_passed:
        print("✅ 所有测试通过！系统配置正确。")
    else:
        print("⚠️ 部分测试失败，请检查上述错误信息。")
    
    print("\n建议:")
    
    if test_results.get('execution_time', 0) and test_results['execution_time'] > 300:
        print("- ⚠️ 执行时间较长，建议:")
        print("  1. 检查网络连接")
        print("  2. 识别慢速RSS源")
        print("  3. 考虑调整调度时间到凌晨")
    
    if not test_results.get('timezone', False):
        print("- ❌ 时区配置有误，请修复 .env 中的 SCHEDULE_TZ")
    
    print("\n下一步:")
    if all_passed:
        print("1. 运行实际程序: python src/main.py")
        print("2. 观察日志输出，特别是执行时间")
        print("3. 连续运行3天以上，验证misfire问题是否解决")
    else:
        print("1. 修复上述失败的测试项")
        print("2. 重新运行诊断: python src/test_scheduler.py")


def main():
    print("\n" + "=" * 60)
    print("RSS Email Scheduler 诊断工具")
    print("=" * 60)
    print()
    
    test_results = {}
    
    # 1. 测试配置
    settings = test_configuration()
    test_results['config'] = settings is not None
    if not settings:
        print("\n配置加载失败，无法继续测试。")
        return
    
    # 2. 测试时区
    test_results['timezone'] = test_timezone(settings)
    
    # 3. 测试数据库
    session_factory = test_database(settings)
    test_results['database'] = session_factory is not None
    
    # 4. 测试RSS源
    rss_results = test_rss_feeds(settings)
    test_results['rss'] = all(r[0] == "✅" for r in rss_results)
    
    # 5. 测试完整周期
    execution_time = test_full_cycle(settings)
    test_results['execution_time'] = execution_time
    test_results['full_cycle'] = execution_time is not None
    
    # 6. 测试调度器配置
    test_results['scheduler'] = test_scheduler_config(settings)
    
    # 生成报告
    generate_report(settings, test_results)


if __name__ == "__main__":
    main()
