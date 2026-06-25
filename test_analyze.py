import os
import json
from datetime import datetime

# 模拟测试_Phase_anal方法
os.chdir(r"C:\Users\Administrator\WorkBuddy\Claw\evolution")

import sys
sys.path.insert(0, '.')

# 导入模块
from storage.database import Database
from core.engine import EvolutionEngine

# 初始化
db = Database()
engine = EvolutionEngine(db)

# 模拟一些测试问题
test_issues = [
    {"id": 1, "message": "name 'os' is not defined", "event_type": "error_occurred", "file": "test.py", "line": 10, "created_at": "2026-06-24 10:00:00"},
    {"id": 2, "message": "IndexError: list index out of range", "event_type": "error_occurred", "file": "main.py", "line": 25, "created_at": "2026-06-24 10:05:00"},
    {"id": 3, "message": "AttributeError: 'NoneType' object has no attribute", "event_type": "error_occurred", "file": "utils.py", "line": 50, "created_at": "2026-06-24 10:10:00"},
]

# 运行分析
print("=== 测试增强的深度分析 ===")
result = engine._phase_analyze(test_issues)

analyses = result.get("analyses", [])

print(f"\n分析数量: {len(analyses)}")
print("\n详细分析结果:")
for i, a in enumerate(analyses, 1):
    print(f"\n--- 问题 {i} ---")
    print(f"  规则: {a.get('rule_name')}")
    print(f"  严重程度: {a.get('severity')}")
    print(f"  置信度: {a.get('confidence')}")
    print(f"  根因: {a.get('root_cause')}")
    print(f"  修复建议: {a.get('fix_suggestion')}")
    print(f"  优先级: {a.get('priority_score')}")
    print(f"  文件: {a.get('file')}:{a.get('line')}")