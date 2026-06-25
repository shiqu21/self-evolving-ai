"""代码评审员 - 代码质量评审、漏洞检测、改进建议"""
import asyncio
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import hashlib
import ast

from agents.base import BaseAgent, AgentResult, AgentType, Task
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CodeIssue:
    """代码问题"""
    issue_id: str = ""
    severity: str = ""  # critical, error, warning, info
    category: str = ""  # security, bug, performance, style, best_practice
    message: str = ""
    line_number: int = 0
    code_snippet: str = ""
    suggestion: str = ""
    cwe_id: str = ""  # Common Weakness Enumeration

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "line_number": self.line_number,
            "code_snippet": self.code_snippet,
            "suggestion": self.suggestion,
            "cwe_id": self.cwe_id
        }


@dataclass
class ReviewReport:
    """评审报告"""
    review_id: str = ""
    file_path: str = ""
    language: str = ""
    lines_of_code: int = 0
    issues: List[CodeIssue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class CodeReviewerAgent(BaseAgent):
    """代码评审员代理

    负责:
    1. 代码质量评审 - 检查代码风格、结构和可维护性
    2. 漏洞检测 - 发现安全漏洞和潜在bug
    3. 改进建议 - 提供具体的改进方案
    """

    name: str = "code_reviewer"
    description: str = "代码评审员，提供代码质量评审和漏洞检测" 
    agent_type: AgentType = AgentType.CODE_REVIEWER

    def __init__(self):
        super().__init__()
        self._review_history: List[ReviewReport] = []
        self._security_patterns = self._init_security_patterns()
        self._best_practices = self._init_best_practices()

    async def execute(self, task: Task) -> AgentResult:
        """执行代码评审

        Args:
            task: 评审任务

        Returns:
            AgentResult: 评审结果
        """
        start_time = datetime.now()

        try:
            action = task.payload.get("action", "review")

            if action == "review":
                result_data = await self.review(task.payload)
            elif action == "detect_issues":
                result_data = await self.detect_issues(task.payload)
            elif action == "suggest_improvements":
                result_data = await self.suggest_improvements(task.payload)
            elif action == "full_review":
                result_data = await self.full_review(task.payload)
            else:
                result_data = {"message": f"未知操作: {action}"}

            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            return AgentResult(
                success=True,
                data=result_data,
                metadata={
                    "action": action,
                    "reviews_completed": len(self._review_history)
                },
                agent_type=self.agent_type.value,
                execution_time_ms=execution_time
            )

        except Exception as e:
            logger.error(f"代码评审执行失败: {e}", exc_info=True)
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            return AgentResult(
                success=False,
                error=str(e),
                agent_type=self.agent_type.value,
                execution_time_ms=execution_time
            )

    async def review(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """代码质量评审

        Args:
            payload: 评审参数

        Returns:
            Dict[str, Any]: 评审结果
        """
        code = payload.get("code", "")
        file_path = payload.get("file_path", "unknown")
        language = payload.get("language", self._detect_language(file_path))

        logger.info(f"开始评审代码文件: {file_path}")

        # 检测问题
        issues = await self.detect_issues({"code": code, "language": language})

        # 计算代码度量
        metrics = self._calculate_metrics(code, language)

        # 生成评分
        score = self._calculate_score(issues.get("issues", []))

        # 生成建议
        recommendations = await self.suggest_improvements({
            "issues": issues.get("issues", []),
            "language": language
        })

        # 创建报告
        review = ReviewReport(
            review_id=f"review_{len(self._review_history) + 1}",
            file_path=file_path,
            language=language,
            lines_of_code=metrics.get("lines", 0),
            issues=[CodeIssue(**i) if isinstance(i, dict) else i for i in issues.get("issues", [])],
            metrics=metrics,
            score=score,
            recommendations=recommendations.get("recommendations", [])
        )

        self._review_history.append(review)

        result = {
            "review_id": review.review_id,
            "file_path": file_path,
            "language": language,
            "lines_of_code": review.lines_of_code,
            "issues_count": len(issues.get("issues", [])),
            "issues": issues.get("issues", []),
            "metrics": metrics,
            "score": score,
            "recommendations": recommendations.get("recommendations", []),
            "timestamp": review.timestamp.isoformat()
        }

        logger.info(f"评审完成: 发现 {len(issues.get('issues', []))} 个问题，评分: {score:.1f}/100")
        return result

    async def detect_issues(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """检测代码问题

        Args:
            payload: 检测参数

        Returns:
            Dict[str, Any]: 检测结果
        """
        code = payload.get("code", "")
        language = payload.get("language", "python")
        check_types = payload.get("check_types", ["security", "bug", "performance", "style"])

        logger.info(f"检测代码问题 (检查类型: {check_types})")

        issues: List[Dict[str, Any]] = []
        lines = code.split('\n')

        # 安全检查
        if "security" in check_types:
            issues.extend(self._check_security_vulnerabilities(code, lines))

        # Bug检测
        if "bug" in check_types:
            issues.extend(self._check_potential_bugs(code, lines))

        # 性能检查
        if "performance" in check_types:
            issues.extend(self._check_performance(code, lines))

        # 代码风格检查
        if "style" in check_types:
            issues.extend(self._check_code_style(code, lines))

        # 按严重程度排序
        severity_order = {"critical": 0, "error": 1, "warning": 2, "info": 3}
        issues.sort(key=lambda x: severity_order.get(x.get("severity", "info"), 3))

        return {
            "issues": issues,
            "total_issues": len(issues),
            "by_severity": self._count_by_severity(issues),
            "by_category": self._count_by_category(issues)
        }

    async def suggest_improvements(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """提供改进建议

        Args:
            payload: 改进建议参数

        Returns:
            Dict[str, Any]: 改进建议
        """
        issues = payload.get("issues", [])
        language = payload.get("language", "python")

        logger.info(f"生成改进建议 (共 {len(issues)} 个问题)")

        recommendations = []
        seen_messages = set()

        for issue in issues:
            severity = issue.get("severity", "info")
            category = issue.get("category", "")
            message = issue.get("message", "")
            suggestion = issue.get("suggestion", "")

            if message in seen_messages:
                continue

            seen_messages.add(message)

            # 优先级建议
            if severity in ["critical", "error"]:
                recommendations.insert(0, suggestion or f"高优先级: {message}")
            elif severity == "warning":
                recommendations.append(f"建议修复: {message}")
            else:
                recommendations.append(f"优化建议: {message}")

        # 添加通用建议
        if not recommendations:
            recommendations.append("代码质量良好，继续保持!")
        else:
            # 限制建议数量
            recommendations = recommendations[:10]

        return {
            "recommendations": recommendations,
            "total_recommendations": len(recommendations),
            "high_priority_count": sum(1 for r in recommendations if r.startswith("高优先级"))
        }

    async def full_review(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """完整代码评审

        执行完整的评审流程:检测+建议

        Args:
            payload: 评审参数

        Returns:
            Dict[str, Any]: 完整评审结果
        """
        logger.info("开始完整代码评审流程")

        # 1. 检测问题
        issues_result = await self.detect_issues(payload)

        # 2. 生成建议
        suggestions_result = await self.suggest_improvements({
            "issues": issues_result.get("issues", []),
            "language": payload.get("language", "python")
        })

        # 3. 生成评分
        score = self._calculate_score(issues_result.get("issues", []))

        return {
            "issues": issues_result.get("issues", []),
            "issues_count": len(issues_result.get("issues", [])),
            "recommendations": suggestions_result.get("recommendations", []),
            "score": score,
            "by_severity": issues_result.get("by_severity", {}),
            "by_category": issues_result.get("by_category", {}),
            "review_completed": True,
            "timestamp": datetime.now().isoformat()
        }

    def _check_security_vulnerabilities(self, code: str, lines: List[str]) -> List[Dict]:
        """检查安全漏洞

        Args:
            code: 完整代码
            lines: 代码行列表

        Returns:
            List[Dict]: 发现的问题
        """
        issues = []
        issue_id = 1

        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            line_num = i

            # 硬编码密码/密钥检测
            if re.search(r'(password|passwd|pwd|secret|api[_-]?key|token)\s*=\s*["\'](?!.*\$\{|.*\{)', line, re.IGNORECASE):
                if not line_stripped.startswith('#'):
                    issues.append({
                        "issue_id": f"sec_{issue_id}",
                        "severity": "critical",
                        "category": "security",
                        "message": "检测到硬编码的敏感信息",
                        "line_number": line_num,
                        "code_snippet": line_stripped[:60],
                        "suggestion": "使用环境变量或安全的密钥管理服务",
                        "cwe_id": "CWE-798"
                    })
                    issue_id += 1

            # SQL注入风险
            if re.search(r'(execute|fetch|cursor)\s*\(.*\+', line, re.IGNORECASE) or \
               re.search(r'(select|insert|update|delete).*\+', line, re.IGNORECASE):
                if 'f"' not in line and '%' not in line:  # 排除参数化查询
                    issues.append({
                        "issue_id": f"sec_{issue_id}",
                        "severity": "critical",
                        "category": "security",
                        "message": "可能存在SQL注入风险",
                        "line_number": line_num,
                        "code_snippet": line_stripped[:60],
                        "suggestion": "使用参数化查询或ORM",
                        "cwe_id": "CWE-89"
                    })
                    issue_id += 1

            # 命令注入风险
            if re.search(r'(os\.system|subprocess|shell=True)', line):
                if 'shell=True' in line or re.search(r'system\s*\(.*\+', line):
                    issues.append({
                        "issue_id": f"sec_{issue_id}",
                        "severity": "critical",
                        "category": "security",
                        "message": "可能存在命令注入风险",
                        "line_number": line_num,
                        "code_snippet": line_stripped[:60],
                        "suggestion": "避免使用shell=True，使用参数列表",
                        "cwe_id": "CWE-78"
                    })
                    issue_id += 1

            # 不安全的随机数
            if re.search(r'random\.(random|randint)\(', line):
                if 'Secrets' not in line:  # 排除安全的Secrets模块
                    issues.append({
                        "issue_id": f"sec_{issue_id}",
                        "severity": "warning",
                        "category": "security",
                        "message": "使用random模块生成随机数不够安全",
                        "line_number": line_num,
                        "code_snippet": line_stripped[:60],
                        "suggestion": "使用secrets模块生成加密安全的随机数",
                        "cwe_id": "CWE-338"
                    })
                    issue_id += 1

            # 危险的文件操作
            if re.search(r'\.read\s*\(\s*\)|open\s*\(.*,\s*["\']r["\']\s*\)', line):
                if 'safe' not in line.lower():
                    issues.append({
                        "issue_id": f"sec_{issue_id}",
                        "severity": "warning",
                        "category": "security",
                        "message": "读取文件需要验证路径，防止路径遍历攻击",
                        "line_number": line_num,
                        "code_snippet": line_stripped[:60],
                        "suggestion": "验证文件路径，使用pathlib的resolve()检查路径",
                        "cwe_id": "CWE-22"
                    })
                    issue_id += 1

        return issues

    def _check_potential_bugs(self, code: str, lines: List[str]) -> List[Dict]:
        """检查潜在bug

        Args:
            code: 完整代码
            lines: 代码行列表

        Returns:
            List[Dict]: 发现的问题
        """
        issues = []
        issue_id = 1

        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            line_num = i

            # 赋值vs比较
            if re.search(r'if\s+\w+\s*=\s*\w+', line) and '==' not in line:
                if not line_stripped.startswith('#'):
                    issues.append({
                        "issue_id": f"bug_{issue_id}",
                        "severity": "error",
                        "category": "bug",
                        "message": "疑似使用赋值(=)而非比较(==)",
                        "line_number": line_num,
                        "code_snippet": line_stripped[:60],
                        "suggestion": "使用 == 进行比较",
                        "cwe_id": ""
                    })
                    issue_id += 1

            # 空比较
            if re.search(r'==\s*(None|True|False)|is\s+(None|True|False)', line):
                if re.search(r'==\s+(None|True|False)', line):
                    issues.append({
                        "issue_id": f"bug_{issue_id}",
                        "severity": "warning",
                        "category": "bug",
                        "message": "建议使用 'is' 进行None/True/False比较",
                        "line_number": line_num,
                        "code_snippet": line_stripped[:60],
                        "suggestion": "使用 'is None' 或 'is True/False'",
                        "cwe_id": ""
                    })
                    issue_id += 1

            # 捕获所有异常
            if re.search(r'except\s*:\s*$', line):
                issues.append({
                    "issue_id": f"bug_{issue_id}",
                    "severity": "warning",
                    "category": "bug",
                    "message": "捕获所有异常过于宽泛",
                    "line_number": line_num,
                    "code_snippet": line_stripped[:60],
                    "suggestion": "捕获具体异常类型",
                    "cwe_id": ""
                })
                issue_id += 1

            # 未使用的变量
            if re.search(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*', line):
                var_name = re.search(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*=', line)
                if var_name:
                    # 检查后续是否使用
                    var = var_name.group(1)
                    if var not in ['self', 'cls', 'config', 'logger']:
                        remaining = '\n'.join(lines[i:])
                        if remaining and f' {var}(' not in remaining and f',{var},' not in remaining and f'[{var}]' not in remaining:
                            # 简化判断，容忍函数定义等
                            if 'def ' not in line and 'class ' not in line:
                                issues.append({
                                    "issue_id": f"bug_{issue_id}",
                                    "severity": "info",
                                    "category": "bug",
                                    "message": f"变量 '{var}' 可能未使用",
                                    "line_number": line_num,
                                    "code_snippet": line_stripped[:60],
                                    "suggestion": "确认变量是否需要或使用下划线前缀标记未使用",
                                    "cwe_id": ""
                                })
                                issue_id += 1

            # 字符串拼接优化
            if '+' in line and ('"' in line or "'" in line):
                if len(re.findall(r'["\'][^+"\']*["\']', line)) >= 3:
                    issues.append({
                        "issue_id": f"bug_{issue_id}",
                        "severity": "info",
                        "category": "performance",
                        "message": "建议使用f-string或join进行字符串拼接",
                        "line_number": line_num,
                        "code_snippet": line_stripped[:60],
                        "suggestion": "使用 f'{a}{b}{c}' 或 ''.join([...]) 替代 + 拼接",
                        "cwe_id": ""
                    })
                    issue_id += 1

        return issues

    def _check_performance(self, code: str, lines: List[str]) -> List[Dict]:
        """检查性能问题

        Args:
            code: 完整代码
            lines: 代码行列表

        Returns:
            List[Dict]: 发现的问题
        """
        issues = []
        issue_id = 1

        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            line_num = i

            # 循环内的重复计算
            if re.search(r'for\s+.*in\s+.*:', line):
                # 检查下一行或后续是否有重复计算
                if i < len(lines):
                    next_lines = '\n'.join(lines[i:min(i+10, len(lines))])
                    if re.search(r'\.len\(\)|len\(.*\)', next_lines):
                        if 'range(' not in next_lines:
                            issues.append({
                                "issue_id": f"perf_{issue_id}",
                                "severity": "warning",
                                "category": "performance",
                                "message": "循环中可能存在重复计算",
                                "line_number": line_num,
                                "code_snippet": line_stripped[:60],
                                "suggestion": "将重复计算移到循环外",
                                "cwe_id": ""
                            })
                            issue_id += 1

            # 未使用列表推导式
            if re.search(r'for\s+\w+\s+in\s+.*:.*\w+\.append\(', line):
                issues.append({
                    "issue_id": f"perf_{issue_id}",
                    "severity": "info",
                    "category": "performance",
                    "message": "可使用列表推导式优化",
                    "line_number": line_num,
                    "code_snippet": line_stripped[:60],
                    "suggestion": "使用 result = [f(x) for x in items]",
                    "cwe_id": ""
                })
                issue_id += 1

        return issues

    def _check_code_style(self, code: str, lines: List[str]) -> List[Dict]:
        """检查代码风格

        Args:
            code: 完整代码
            lines: 代码行列表

        Returns:
            List[Dict]: 发现的问题
        """
        issues = []
        issue_id = 1
        prev_line = ""

        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            line_num = i

            # 行过长
            if len(line) > 120:
                issues.append({
                    "issue_id": f"style_{issue_id}",
                    "severity": "info",
                    "category": "style",
                    "message": f"行长度超过120字符 ({len(line)}字符)",
                    "line_number": line_num,
                    "code_snippet": line_stripped[:60] + "...",
                    "suggestion": "将长行拆分为多行",
                    "cwe_id": ""
                })
                issue_id += 1

            # 缺少文档字符串
            if line_stripped.startswith('def ') or line_stripped.startswith('class '):
                has_docstring = False
                if i < len(lines) and '"""' in lines[i]:
                    has_docstring = True
                if not has_docstring and 'def ' in line_stripped:
                    issues.append({
                        "issue_id": f"style_{issue_id}",
                        "severity": "info",
                        "category": "style",
                        "message": "函数/类缺少文档字符串",
                        "line_number": line_num,
                        "code_snippet": line_stripped[:60],
                        "suggestion": "添加docstring描述函数用途、参数和返回值",
                        "cwe_id": ""
                    })
                    issue_id += 1

            # 空格问题
            if '  ' in line_stripped and not line_stripped.startswith(' '):
                issues.append({
                    "issue_id": f"style_{issue_id}",
                    "severity": "info",
                    "category": "style",
                    "message": "检测到连续空格",
                    "line_number": line_num,
                    "code_snippet": line_stripped[:60],
                    "suggestion": "使用单空格进行缩进",
                    "cwe_id": ""
                })
                issue_id += 1

            prev_line = line_stripped

        return issues

    def _calculate_metrics(self, code: str, language: str) -> Dict[str, Any]:
        """计算代码度量

        Args:
            code: 代码
            language: 编程语言

        Returns:
            Dict: 度量结果
        """
        lines = code.split('\n')
        non_empty_lines = [l for l in lines if l.strip()]

        # 注释统计
        comment_lines = [l for l in lines if l.strip().startswith('#') or l.strip().startswith('//')]

        # 函数/方法计数
        functions = len(re.findall(r'def\s+\w+', code))
        classes = len(re.findall(r'class\s+\w+', code))

        # 导入统计
        imports = len(re.findall(r'^import\s+|^from\s+\w+\s+import', code, re.MULTILINE))

        # 复杂度(简化)
        complexity = len(re.findall(r'\bif\b|\bfor\b|\bwhile\b|\bexcept\b', code))

        return {
            "total_lines": len(lines),
            "lines": len(non_empty_lines),
            "comment_lines": len(comment_lines),
            "blank_lines": len(lines) - len(non_empty_lines),
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "complexity": complexity,
            "comment_ratio": round(len(comment_lines) / max(len(non_empty_lines), 1), 2)
        }

    def _calculate_score(self, issues: List[Dict]) -> float:
        """计算质量评分

        Args:
            issues: 问题列表

        Returns:
            float: 评分 (0-100)
        """
        if not issues:
            return 100.0

        base_score = 100.0

        # 扣分
        deductions = {
            "critical": 15,
            "error": 10,
            "warning": 5,
            "info": 1
        }

        for issue in issues:
            severity = issue.get("severity", "info")
            deduction = deductions.get(severity, 1)
            base_score -= deduction

        return max(0.0, round(base_score, 1))

    def _detect_language(self, file_path: str) -> str:
        """检测编程语言

        Args:
            file_path: 文件路径

        Returns:
            str: 语言类型
        """
        ext = file_path.split('.')[-1].lower() if '.' in file_path else ""

        lang_map = {
            "py": "python",
            "js": "javascript",
            "ts": "typescript",
            "java": "java",
            "go": "go",
            "rs": "rust",
            "cpp": "cpp",
            "c": "c",
            "cs": "csharp",
            "rb": "ruby",
            "php": "php"
        }

        return lang_map.get(ext, "unknown")

    def _count_by_severity(self, issues: List[Dict]) -> Dict[str, int]:
        """按严重程度统计

        Args:
            issues: 问题列表

        Returns:
            Dict: 统计结果
        """
        counts = defaultdict(int)
        for issue in issues:
            severity = issue.get("severity", "info")
            counts[severity] += 1
        return dict(counts)

    def _count_by_category(self, issues: List[Dict]) -> Dict[str, int]:
        """按类别统计

        Args:
            issues: 问题列表

        Returns:
            Dict: 统计结果
        """
        counts = defaultdict(int)
        for issue in issues:
            category = issue.get("category", "unknown")
            counts[category] += 1
        return dict(counts)

    def _init_security_patterns(self) -> Dict:
        """初始化安全模式"""
        return {
            "hardcoded_creds": r'(password|passwd|secret|key)\s*=\s*["\']',
            "sql_injection": r'execute\s*\(.*\+',
            "command_injection": r'subprocess.*shell\s*=\s*True'
        }

    def _init_best_practices(self) -> List[str]:
        """初始化最佳实践"""
        return [
            "使用类型注解",
            "添加文档字符串",
            "异常处理要具体",
            "使用日志而非print",
            "保持函数简短"
        ]