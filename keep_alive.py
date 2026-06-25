"""
Keep Alive - 确保自我进化系统永不丢失
功能:
  1. 监控系统是否运行
  2. 如果未运行则自动启动
  3. 每分钟检查一次
"""
import subprocess
import time
import sys
from pathlib import Path

PYTHON = r"C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python..exe"
SCRIPT = r"C:\Users\Administrator\WorkBuddy\Claw\evolution\auto_run.py"

def is_running():
    """检查进程是否运行"""
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq python.exe"],
            capture_output=True, text=True
        )
        return "auto_run.py" in result.stdout
    except:
        return False

def start_evolution():
    """启动进化系统"""
    print("[KEEP-ALIVE] Starting evolution system...")
    subprocess.Popen(
        [PYTHON, SCRIPT],
        cwd=str(Path(SCRIPT).parent),
        env={**subprocess.os.environ, "PYTHONIOENCODING": "utf-8"},
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
    )

def main():
    print("[KEEP-ALIVE] Monitor started. Checking every 60 seconds...")
    while True:
        if not is_running():
            print("[KEEP-ALIVE] System not running! Starting...")
            start_evolution()
        time.sleep(60)

if __name__ == "__main__":
    main()