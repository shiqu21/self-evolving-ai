#!/usr/bin/env python3
"""自我进化守护进程 - 持续在后台运行"""
import subprocess
import time
import sys
from pathlib import Path

EVOLUTION_DIR = Path(__file__).parent
LOG_FILE = EVOLUTION_DIR / "logs" / "daemon_loop.log"
DESKTOP_LOG = Path.home() / "Desktop" / "evolution_log.txt"

def get_latest_evolution_log():
    """读取最新的进化详细日志"""
    try:
        logs_dir = EVOLUTION_DIR / "logs"
        log_files = list(logs_dir.glob("evolution_2026-06-*.log"))
        if not log_files:
            return "无进化日志文件"
        latest = max(log_files, key=lambda p: p.stat().st_mtime)
        # 读取最后20行
        lines = latest.read_text(encoding="utf-8", errors="ignore").splitlines()
        return "\n".join(lines[-20:])
    except Exception as e:
        return f"读取日志失败: {e}"

def run_cycle():
    """运行一次进化循环"""
    try:
        result = subprocess.run(
            [sys.executable, "run.py", "--once"],
            cwd=str(EVOLUTION_DIR),
            capture_output=True,
            text=True,
            timeout=120
        )
        # 获取详细日志
        detail_log = get_latest_evolution_log()
        # 构造完整日志内容
        log_content = f"=== {time.strftime('%Y-%m-%d %H:%M:%S')} 进化#{time.strftime('%H%M%S')} ===\n{detail_log}\n\n"
        # 写入桌面日志
        with open(DESKTOP_LOG, "a", encoding="utf-8") as f:
            f.write(log_content)
        return result.returncode == 0
    except Exception as e:
        err_msg = f"ERROR: {e}\n"
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(err_msg)
        with open(DESKTOP_LOG, "a", encoding="utf-8") as f:
            f.write(err_msg)
        return False

def main():
    print(f"启动自我进化守护进程...")
    print(f"日志: {LOG_FILE}")
    print(f"每60秒运行一次进化循环")

    cycle = 0
    while True:
        cycle += 1
        success = run_cycle()
        status = "OK" if success else "FAIL"
        print(f"[{cycle}] {time.strftime('%H:%M:%S')} - {status}")
        time.sleep(60)

if __name__ == "__main__":
    main()