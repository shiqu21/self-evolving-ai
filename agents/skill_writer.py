"""技能编写器 - 生成和优化Skills技能模块"""
import asyncio
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import hashlib
import json
import os
from collections import defaultdict

from agents.base import BaseAgent, AgentResult, AgentType, Task
from utils.llm_client import get_llm_client
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SkillSpec:
    """技能规范"""
    name: str
    description: str
    trigger_keywords: List[str] = field(default_factory=list)
    code: str = ""
    dependencies: List[str] = field(default_factory=list)
    risk_level: str = "micro"
    category: str = "general"


@dataclass
class GeneratedSkill:
    """生成的技能"""
    skill_id: str = ""
    spec: SkillSpec = None
    code: str = ""
    quality_score: float = 0.0
    validation_results: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


class SkillWriterAgent(BaseAgent):
    """技能编写器代理
    
    负责:
    1. 生成 - 根据需求生成Skills技能模块代码
    2. 优化 - 改进现有技能代码
    3. 填补空白 - 识别系统技能缺口并补全
    """

    name: str = "skill_writer" 
    description: str = "技能编写器，生成和优化Skills技能模块"
    agent_type: AgentType = AgentType.SKILL_WRITER

    def __init__(self):
        super().__init__()
        self._llm_client = get_llm_client()
        self._generated_skills: List[GeneratedSkill] = []
        self._skill_templates = self._init_skill_templates()
        self._existing_skills = set()

    async def execute(self, task: Task) -> AgentResult:
        """执行技能编写
        
        Args:
            task: 编写任务
            
        Returns:
            AgentResult: 执行结果
        """
        start_time = datetime.now()
        
        try:
            action = task.payload.get("action", "generate")
            
            if action == "generate":
                result_data = await self.generate(task.payload)
            elif action == "optimize":
                result_data = await self.optimize(task.payload)
            elif action == "fill_gap":
                result_data = await self.fill_gap(task.payload)
            elif action == "validate":
                result_data = await self.validate(task.payload)
            else:
                result_data = {"message": f"未知操作: {action}"}
            
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return AgentResult(
                success=True,
                data=result_data,
                metadata={
                    "action": action,
                    "skills_generated": len(self._generated_skills)
                },
                agent_type=self.agent_type.value,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            logger.error(f"技能编写执行失败: {e}", exc_info=True)
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            return AgentResult(
                success=False,
                error=str(e),
                agent_type=self.agent_type.value,
                execution_time_ms=execution_time
            )

    async def generate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """生成技能
        
        根据需求描述生成Skills技能代码
        
        Args:
            payload: 生成参数，包含name、description、use_case等
            
        Returns:
            Dict[str, Any]: 生成的技能
        """
        skill_name = payload.get("name", "")
        description = payload.get("description", "")
        use_case = payload.get("use_case", payload.get("description", ""))
        category = payload.get("category", "general")
        
        logger.info(f"开始生成技能: {skill_name}")
        
        # 检查是否已有类似技能
        if self._skill_exists(skill_name, description):
            logger.warning(f"技能可能已存在: {skill_name}")
        
        # 确定触发关键词
        trigger_keywords = self._extract_keywords(skill_name, description)
        
        # 生成技能代码
        if self._llm_client:
            code = await self._generate_with_llm(skill_name, description, use_case)
        else:
            code = self._generate_from_template(skill_name, description, category)
        
        # 创建技能规范
        spec = SkillSpec(
            name=skill_name,
            description=description,
            trigger_keywords=trigger_keywords,
            code=code,
            category=category,
            risk_level=self._assess_risk(code)
        )
        
        # 验证生成的代码
        validation = await self._validate_skill_code(code, spec)
        
        # 创建生成记录
        skill_id = f"skill_{hashlib.md5(skill_name.encode()).hexdigest()[:8]}"
        generated = GeneratedSkill(
            skill_id=skill_id,
            spec=spec,
            code=code,
            quality_score=validation.get("score", 0.0),
            validation_results=validation
        )
        
        self._generated_skills.append(generated)
        
        result = {
            "skill_id": skill_id,
            "name": skill_name,
            "description": description,
            "trigger_keywords": trigger_keywords,
            "code": code,
            "category": category,
            "risk_level": spec.risk_level,
            "validation": validation,
            "quality_score": generated.quality_score,
            "timestamp": generated.created_at.isoformat()
        }
        
        logger.info(f"技能生成完成: {skill_name}, 质量评分: {generated.quality_score}")
        return result

    async def optimize(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """优化技能
        
        改进现有技能代码
        
        Args:
            payload: 优化参数，包含现有代码和改进目标
            
        Returns:
            Dict[str, Any]: 优化结果
        """
        existing_code = payload.get("code", "")
        skill_name = payload.get("name", "optimized_skill")
        optimization_goal = payload.get("goal", "improve")
        
        logger.info(f"开始优化技能: {skill_name}")
        
        # 分析现有代码问题
        issues = await self._analyze_code_issues(existing_code)
        
        # 生成优化版本
        if self._llm_client:
            optimized_code = await self._optimize_with_llm(existing_code, optimization_goal)
        else:
            optimized_code = self._basic_optimize(existing_code)
        
        # 验证优化后的代码
        validation = await self._validate_skill_code(optimized_code, SkillSpec(name=skill_name, description=""))
        
        # 计算改进度
        improvements = self._calculate_improvements(existing_code, optimized_code, issues)
        
        result = {
            "original_code": existing_code,
            "optimized_code": optimized_code,
            "issues_found": issues,
            "improvements": improvements,
            "validation": validation,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"技能优化完成: 发现{len(issues)}个问题，改进{improvements.get('total', 0)}处")
        return result

    async def fill_gap(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """填补技能空白
        
        识别系统技能缺口并生成对应技能
        
        Args:
            payload: 空白填补参数
            
        Returns:
            Dict[str, Any]: 填补结果
        """
        domain = payload.get("domain", "general")
        required_capabilities = payload.get("capabilities", [])
        
        logger.info(f"开始填补技能空白: {domain}")
        
        # 识别技能缺口
        gaps = await self._identify_skill_gaps(domain, required_capabilities)
        
        # 为每个缺口生成技能
        generated_skills = []
        
        for gap in gaps:
            skill_result = await self.generate({
                "name": gap.get("name", "new_skill"),
                "description": gap.get("description", ""),
                "use_case": gap.get("use_case", ""),
                "category": domain
            })
            generated_skills.append(skill_result)
        
        result = {
            "gaps_identified": gaps,
            "skills_generated": len(generated_skills),
            "generated_skills": generated_skills,
            "domain": domain,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"技能空白填补完成: 识别{len(gaps)}个空白，生成{len(generated_skills)}个技能")
        return result

    async def validate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """验证技能
        
        验证技能代码的正确性和完整性
        
        Args:
            payload: 验证参数
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        code = payload.get("code", "")
        skill_spec = payload.get("spec", {})
        
        logger.info("开始验证技能代码")
        
        # 基本语法验证
        syntax_valid = self._check_syntax(code)
        
        # 完整性检查
        completeness = self._check_completeness(code, skill_spec)
        
        # 触发词检查
        triggers_valid = self._check_triggers(code, skill_spec.get("trigger_keywords", []))
        
        # 计算验证分数
        score = (1.0 if syntax_valid else 0) * 0.4 + completeness * 0.4 + triggers_valid * 0.2
        
        result = {
            "valid": syntax_valid and completeness >= 0.8,
            "syntax_valid": syntax_valid,
            "completeness": completeness,
            "triggers_valid": triggers_valid,
            "score": round(score, 2),
            "issues": self._get_validation_issues(syntax_valid, completeness, triggers_valid),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"技能验证完成: 分数={score}, 有效={result['valid']}")
        return result

    async def _generate_with_llm(
        self, 
        name: str, 
        description: str, 
        use_case: str
    ) -> str:
        """使用LLM生成技能代码
        
        Args:
            name: 技能名称
            description: 技能描述
            use_case: 使用场景
            
        Returns:
            str: 生成的代码
        """
        prompt = f"""生成一个WorkBuddy Skills技能模块代码。

技能名称: {name}
描述: {description}
使用场景: {use_case}

请生成完整的Python技能代码，包含:
1. 导入必要的模块
2. Skill类定义
3. skill_manifest函数返回技能元数据
4. 处理函数实现

技能应该能够响应用户的请求并执行相应的操作。

请直接返回代码，不要有额外说明。"""

        try:
            result = self._llm_client.chat(prompt)
            return result if result else self._generate_from_template(name, description, "general")
        except Exception as e:
            logger.warning(f"LLM生成失败: {e}, 使用模板")
            return self._generate_from_template(name, description, "general")

    def _generate_from_template(
        self, 
        name: str, 
        description: str, 
        category: str
    ) -> str:
        """从模板生成技能代码
        
        Args:
            name: 技能名称
            description: 技能描述
            category: 类别
            
        Returns:
            str: 生成的代码
        """
        template = self._skill_templates.get(category, self._skill_templates["general"])
        
        # 替换模板变量
        code = template.format(
            skill_name=name.replace(" ", "_").replace("-", "_").lower(),
            skill_name_caps=name.replace("-", "_").upper(),
            skill_description=description,
            year=datetime.now().year,
            date=datetime.now().strftime("%Y-%m-%d")
        )
        
        return code

    async def _validate_skill_code(self, code: str, spec: SkillSpec) -> Dict[str, Any]:
        """验证技能代码
        
        Args:
            code: 技能代码
            spec: 技能规范
            
        Returns:
            Dict: 验证结果
        """
        # 语法检查
        syntax_valid = self._check_syntax(code)
        
        # 完整性检查
        has_skill_class = "class Skill" in code or "class skill" in code.lower()
        has_manifest = "skill_manifest" in code
        has_handler = "def " in code and "handle" in code.lower()
        
        completeness = sum([has_skill_class, has_manifest, has_handler]) / 3
        
        # 触发词检查
        triggers_valid = len(spec.trigger_keywords) > 0 if spec else True
        
        score = (1.0 if syntax_valid else 0) * 0.3 + completeness * 0.5 + (1.0 if triggers_valid else 0) * 0.2
        
        return {
            "syntax_valid": syntax_valid,
            "has_skill_class": has_skill_class,
            "has_manifest": has_manifest,
            "has_handler": has_handler,
            "completeness": completeness,
            "triggers_valid": triggers_valid,
            "score": round(score, 2)
        }

    def _check_syntax(self, code: str) -> bool:
        """检查Python语法
        
        Args:
            code: 代码字符串
            
        Returns:
            bool: 是否有效
        """
        try:
            compile(code, "<string>", "exec")
            return True
        except SyntaxError:
            return False

    def _check_completeness(self, code: str, spec: Dict) -> float:
        """检查代码完整性
        
        Args:
            code: 代码
            spec: 技能规范
            
        Returns:
            float: 完整性分数 (0-1)
        """
        required_elements = [
            "import",  # 有导入
            "def ",    # 有函数定义
            "class "   # 有类定义(大多数技能需要)
        ]
        
        score = sum(1 for el in required_elements if el in code) / len(required_elements)
        return score

    def _check_triggers(self, code: str, keywords: List[str]) -> bool:
        """检查触发词
        
        Args:
            code: 代码
            keywords: 关键词列表
            
        Returns:
            bool: 是否有效
        """
        if not keywords:
            return True  # 没有关键词也可以
            
        return any(kw.lower() in code.lower() for kw in keywords)

    def _get_validation_issues(
        self, 
        syntax_valid: bool, 
        completeness: float, 
        triggers_valid: bool
    ) -> List[str]:
        """获取验证问题列表
        
        Args:
            syntax_valid: 语法是否有效
            completeness: 完整性
            triggers_valid: 触发词是否有效
            
        Returns:
            List[str]: 问题列表
        """
        issues = []
        
        if not syntax_valid:
            issues.append("代码语法错误")
        if completeness < 0.8:
            issues.append(f"代码完整性不足 ({int(completeness*100)}%)")
        if not triggers_valid:
            issues.append("缺少触发关键词")
            
        return issues

    def _extract_keywords(self, name: str, description: str) -> List[str]:
        """提取触发关键词
        
        Args:
            name: 技能名称
            description: 技能描述
            
        Returns:
            List[str]: 关键词列表
        """
        # 简单实现:从名称和描述提取关键词
        text = f"{name} {description}".lower()
        
        # 去除常见词
        stop_words = {"的", "和", "或", "一个", "进行", "实现", "处理", "支持", "the", "a", "an", "and", "or", "to", "for", "in"}
        
        words = re.findall(r'\w+', text)
        keywords = [w for w in words if w not in stop_words and len(w) >= 2]
        
        return keywords[:10]  # 最多10个关键词

    def _skill_exists(self, name: str, description: str) -> bool:
        """检查技能是否已存在
        
        Args:
            name: 技能名称
            description: 技能描述
            
        Returns:
            bool: 是否存在
        """
        # 简单实现:检查名称是否已生成过
        for skill in self._generated_skills:
            if skill.spec and skill.spec.name == name:
                return True
        return False

    def _assess_risk(self, code: str) -> str:
        """评估技能风险等级
        
        Args:
            code: 技能代码
            
        Returns:
            str: 风险等级
        """
        # 检查危险操作
        dangerous_patterns = [
            r"os\.system",
            r"subprocess",
            r"eval\s*\(",
            r"exec\s*\(",
            r"__import__",
            r"open\s*\(.*,\s*['\"]w['\"]",
            r"requests\.post",  # 可能发送敏感数据
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, code):
                return "high"
        
        # 检查网络操作
        if "requests" in code or "urllib" in code or "http" in code:
            return "medium"
        
        return "micro"

    async def _analyze_code_issues(self, code: str) -> List[Dict[str, Any]]:
        """分析代码问题
        
        Args:
            code: 代码
            
        Returns:
            List[Dict]: 问题列表
        """
        issues = []
        
        # 简单检查
        if "except:" in code:
            issues.append({"type": "style", "message": "避免捕获所有异常，应指定具体异常类型"})
        
        if len(code.split('\n')) > 200:
            issues.append({"type": "style", "message": "建议将代码拆分，函数应保持简洁"})
            
        if "print(" in code and "logger" not in code:
            issues.append({"type": "best_practice", "message": "建议使用logger替代print"})
        
        return issues

    async def _optimize_with_llm(self, code: str, goal: str) -> str:
        """使用LLM优化代码
        
        Args:
            code: 原始代码
            goal: 优化目标
            
        Returns:
            str: 优化后的代码
        """
        prompt = f"""优化以下Python技能代码:

目标: {goal}

原始代码:
{code}

请优化这段代码，保持功能不变但改进:
1. 代码风格和可读性
2. 错误处理
3. 性能
4. 最佳实践

只返回优化后的代码，不要有其他说明。"""

        try:
            return self._llm_client.chat(prompt)
        except:
            return self._basic_optimize(code)

    def _basic_optimize(self, code: str) -> str:
        """基础优化
        
        Args:
            code: 原始代码
            
        Returns:
            str: 优化后的代码
        """
        # 简单的基础优化
        optimized = code
        
        # 添加logger
        if "logger" not in code and "import logging" in code:
            optimized = optimized.replace(
                "import logging",
                "import logging\n\nlogger = logging.getLogger(__name__)"
            )
        
        return optimized

    def _calculate_improvements(
        self, 
        original: str, 
        optimized: str, 
        issues: List[Dict]
    ) -> Dict[str, int]:
        """计算改进
        
        Args:
            original: 原始代码
            optimized: 优化后代码
            issues: 发现的问题
            
        Returns:
            Dict: 改进统计
        """
        # 计算行数变化
        orig_lines = len(original.split('\n'))
        opt_lines = len(optimized.split('\n'))
        
        # 简单比较
        improvements = {
            "issues_fixed": len(issues),
            "lines_changed": abs(opt_lines - orig_lines),
            "total": len(issues) + (1 if opt_lines != orig_lines else 0)
        }
        
        return improvements

    async def _identify_skill_gaps(
        self, 
        domain: str, 
        capabilities: List[str]
    ) -> List[Dict[str, str]]:
        """识别技能缺口
        
        Args:
            domain: 领域
            capabilities: 需要的能力
            
        Returns:
            List[Dict]: 缺口列表
        """
        # 常见技能模板
        common_skills = {
            "general": [
                {"name": "data_analyst", "description": "数据分析技能", "use_case": "分析用户数据"},
                {"name": "text_processor", "description": "文本处理技能", "use_case": "处理和转换文本"},
                {"name": "file_manager", "description": "文件管理技能", "use_case": "管理文件和目录"},
            ],
            "code": [
                {"name": "code_generator", "description": "代码生成技能", "use_case": "生成代码片段"},
                {"name": "bug_finder", "description": "Bug查找技能", "use_case": "查找代码中的bug"},
                {"name": "code_explainer", "description": "代码解释技能", "use_case": "解释代码功能"},
            ],
            "analysis": [
                {"name": "stock_analyzer", "description": "股票分析技能", "use_case": "分析股票数据"},
                {"name": "trend_detector", "description": "趋势检测技能", "use_case": "检测数据趋势"},
            ]
        }
        
        # 返回该领域的建议技能
        return common_skills.get(domain, common_skills["general"])

    def _init_skill_templates(self) -> Dict[str, str]:
        """初始化技能模板
        
        Returns:
            Dict: 模板字典
        """
        return {
            "general": '''"""通用技能模块 - {skill_name}

{skill_description}

触发关键词: {skill_name}
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class {skill_name_caps}Skill:
    """{skill_name}技能类"""
    
    def __init__(self):
        self.name = "{skill_name}"
        self.version = "1.0.0"
        self.logger = logging.getLogger(__name__)
    
    def handle(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求
        
        Args:
            context: 请求上下文
            
        Returns:
            Dict: 处理结果
        """
        self.logger.info(f"处理请求: {{self.name}}")
        
        # 实现技能逻辑
        result = {{
            "status": "success",
            "message": "技能执行完成",
            "data": {{}}
        }}
        
        return result
    
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """验证输入数据
        
        Args:
            data: 输入数据
            
        Returns:
            bool: 是否有效
        """
        return True


def skill_manifest() -> Dict[str, Any]:
    """技能清单定义
    
    Returns:
        Dict: 技能元数据
    """
    return {{
        "name": "{skill_name}",
        "version": "1.0.0",
        "description": "{skill_description}",
        "category": "general",
        "trigger_keywords": {skill_name},
        "risk_level": "micro",
        "author": "AI Generated",
        "created_date": "{date}"
    }}


# 技能入口点
def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    """技能执行入口
    
    Args:
        context: 执行上下文
        
    Returns:
        Dict: 执行结果
    """
    skill = {skill_name_caps}Skill()
    return skill.handle(context)


if __name__ == "__main__":
    # 测试技能
    test_context = {{"input": "test"}}
    result = execute(test_context)
    print(f"Result: {{result}}")
''',
            "analysis": '''"""分析类技能模块 - {skill_name}

{skill_description}

触发关键词: {skill_name}
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class {skill_name_caps}Skill:
    """{skill_name}技能类"""
    
    def __init__(self):
        self.name = "{skill_name}"
        self.version = "1.0.0"
        self.logger = logging.getLogger(__name__)
    
    def analyze(self, data: Any) -> Dict[str, Any]:
        """分析数据
        
        Args:
            data: 待分析数据
            
        Returns:
            Dict: 分析结果
        """
        self.logger.info(f"开始分析: {{self.name}}")
        
        # 实现分析逻辑
        result = {{
            "status": "success",
            "analysis": {{}},
            "timestamp": datetime.now().isoformat()
        }}
        
        return result
    
    def handle(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求
        
        Args:
            context: 请求上下文
            
        Returns:
            Dict: 处理结果
        """
        data = context.get("data", context)
        return self.analyze(data)


def skill_manifest() -> Dict[str, Any]:
    """技能清单定义
    
    Returns:
        Dict: 技能元数据
    """
    return {{
        "name": "{skill_name}",
        "version": "1.0.0",
        "description": "{skill_description}",
        "category": "analysis",
        "trigger_keywords": {skill_name},
        "risk_level": "micro",
        "author": "AI Generated",
        "created_date": "{date}"
    }}


def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    """技能执行入口"""
    skill = {skill_name_caps}Skill()
    return skill.handle(context)


if __name__ == "__main__":
    test_data = {{"values": [1, 2, 3, 4, 5]}}
    result = execute({{"data": test_data}})
    print(f"Result: {{result}}")
''',
        }
    
    def add_existing_skill(self, skill_name: str):
        """添加已存在的技能
        
        Args:
            skill_name: 技能名称
        """
        self._existing_skills.add(skill_name.lower())