"""质量管道模块测试 - WorkBuddy自我进化系统

测试8阶段质量管道的导入、配置和功能:
1. WRITE - 编写/生成代码/内容
2. TYPECHECK - 类型检查
3. TEST - 运行测试
4. LINT - 代码风格检查
5. CRITIQUE - 质量评审(使用LLM)
6. REFINE - 改进优化
7. ESCALATE - 升级判断
8. ARBITER - 最终仲裁决策

作者: QA Engineer - 严过关
"""
import sys
import os
import asyncio
import pytest
from typing import Dict, List, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入被测试的模块
from quality.pipeline_8stage import (
    QualityStage,
    StageResult,
    PipelineConfig,
    PipelineResult,
    QualityPipeline,
    quick_pipeline_check,
)


class TestQualityStageEnum:
    """测试QualityStage枚举"""

    def test_stage_values(self):
        """测试所有阶段枚举值"""
        assert QualityStage.WRITE.value == "write"
        assert QualityStage.TYPECHECK.value == "typecheck"
        assert QualityStage.TEST.value == "test"
        assert QualityStage.LINT.value == "lint"
        assert QualityStage.CRITIQUE.value == "critique"
        assert QualityStage.REFINE.value == "refine"
        assert QualityStage.ESCALATE.value == "escalate"
        assert QualityStage.ARBITER.value == "arbiter"

    def test_stage_count(self):
        """测试阶段数量"""
        assert len(QualityStage) == 8

    def test_get_display_name(self):
        """测试阶段显示名称"""
        assert QualityStage.WRITE.get_display_name() == "编写"
        assert QualityStage.TYPECHECK.get_display_name() == "类型检查"
        assert QualityStage.TEST.get_display_name() == "测试"
        assert QualityStage.LINT.get_display_name() == "代码检查"
        assert QualityStage.CRITIQUE.get_display_name() == "质量评审"
        assert QualityStage.REFINE.get_display_name() == "改进优化"
        assert QualityStage.ESCALATE.get_display_name() == "升级判断"
        assert QualityStage.ARBITER.get_display_name() == "最终仲裁"


class TestStageResult:
    """测试StageResult类"""

    def test_creation(self):
        """测试StageResult创建"""
        result = StageResult(
            stage=QualityStage.WRITE,
            success=True,
            output="测试内容",
            issues=[],
            duration=1.5
        )
        assert result.success is True
        assert result.stage == QualityStage.WRITE
        assert result.duration == 1.5

    def test_to_dict(self):
        """测试转换为字典"""
        result = StageResult(
            stage=QualityStage.WRITE,
            success=True,
            output="test",
            issues=["issue1"],
            duration=1.0,
            metadata={"key": "value"}
        )
        data = result.to_dict()
        assert "stage" in data
        assert data["stage"] == "write"
        assert "issues" in data
        assert data["issues"] == ["issue1"]


class TestPipelineConfig:
    """测试PipelineConfig类"""

    def test_default_config(self):
        """测试默认配置"""
        config = PipelineConfig()
        assert config.max_refine_iterations == 3
        assert config.typecheck_enabled is True
        assert config.test_enabled is True
        assert config.lint_enabled is True
        assert config.critique_enabled is True
        assert config.auto_fix is True
        assert config.fail_fast is False
        assert config.verbose is True

    def test_custom_config(self):
        """测试自定义配置"""
        config = PipelineConfig(
            max_refine_iterations=5,
            typecheck_enabled=False,
            test_enabled=False,
            verbose=False
        )
        assert config.max_refine_iterations == 5
        assert config.typecheck_enabled is False
        assert config.test_enabled is False
        assert config.verbose is False

    def test_is_stage_enabled(self):
        """测试阶段启用检查"""
        config = PipelineConfig()

        # WRITE 阶段始终启用
        assert config.is_stage_enabled(QualityStage.WRITE) is True

        # TYPECHECK 可配置
        assert config.is_stage_enabled(QualityStage.TYPECHECK) is True

        config.typecheck_enabled = False
        assert config.is_stage_enabled(QualityStage.TYPECHECK) is False

        # REFINE, ESCALATE, ARBITER 总是启用
        assert config.is_stage_enabled(QualityStage.REFINE) is True
        assert config.is_stage_enabled(QualityStage.ESCALATE) is True
        assert config.is_stage_enabled(QualityStage.ARBITER) is True


class TestPipelineResult:
    """测试PipelineResult类"""

    def test_creation(self):
        """测试PipelineResult创建"""
        stage_results = [
            StageResult(QualityStage.WRITE, True, "content", [], 1.0),
            StageResult(QualityStage.TYPECHECK, True, "content", [], 0.5),
        ]
        result = PipelineResult(
            content="原始内容",
            final_content="最终内容",
            stage_results=stage_results,
            total_duration=2.5,
            passed=True,
            decision="approve",
            decision_reason="所有检查通过",
            escalation_required=False
        )
        assert result.passed is True
        assert result.decision == "approve"
        assert result.escalation_required is False

    def test_to_dict(self):
        """测试转换为字典"""
        stage_results = [StageResult(QualityStage.WRITE, True, "c", [], 1.0)]
        result = PipelineResult(
            content="c",
            final_content="c",
            stage_results=stage_results,
            total_duration=1.0,
            passed=True,
            decision="approve"
        )
        data = result.to_dict()
        assert "passed" in data
        assert "decision" in data
        assert len(data["stage_results"]) == 1


class TestQualityPipelineCreation:
    """测试QualityPipeline创建"""

    def test_default_creation(self):
        """测试默认创建"""
        pipeline = QualityPipeline()
        assert pipeline is not None
        assert pipeline.config is not None

    def test_custom_creation(self):
        """测试自定义配置创建"""
        config = PipelineConfig(max_refine_iterations=5, verbose=False)
        pipeline = QualityPipeline(config)
        assert pipeline.config.max_refine_iterations == 5
        assert pipeline.config.verbose is False


class TestQualityPipelineStages:
    """测试质量管道各阶段"""

    @pytest.mark.asyncio
    async def test_write_stage(self):
        """测试WRITE阶段"""
        pipeline = QualityPipeline(PipelineConfig(verbose=False))
        content = "def hello():\n    print('hello')"

        result = await pipeline.execute(content, QualityStage.WRITE)
        assert result is not None
        assert result.success is True  # 有效内容应该通过
        assert result.stage == QualityStage.WRITE

    @pytest.mark.asyncio
    async def test_write_stage_empty_content(self):
        """测试WRITE阶段 - 空内容"""
        pipeline = QualityPipeline(PipelineConfig(verbose=False))

        result = await pipeline.execute("", QualityStage.WRITE)
        assert result.success is False

    @pytest.mark.asyncio
    async def test_write_stage_short_content(self):
        """测试WRITE阶段 - 过短内容"""
        pipeline = QualityPipeline(PipelineConfig(verbose=False))

        result = await pipeline.execute("hi", QualityStage.WRITE)
        assert result.success is False

    @pytest.mark.asyncio
    async def test_typecheck_stage_python(self):
        """测试TYPECHECK阶段 - Python"""
        pipeline = QualityPipeline(PipelineConfig(verbose=False))
        content = "def add(a: int, b: int) -> int:\n    return a + b"

        result = await pipeline.execute(content, QualityStage.TYPECHECK)
        assert result is not None

    @pytest.mark.asyncio
    async def test_typecheck_stage_js(self):
        """测试TYPECHECK阶段 - JavaScript"""
        pipeline = QualityPipeline(PipelineConfig(verbose=False))
        content = "function add(a, b) { return a + b; }"

        result = await pipeline.execute(content, QualityStage.TYPECHECK, {"language": "javascript"})
        assert result is not None

    @pytest.mark.asyncio
    async def test_test_stage(self):
        """测试TEST阶段"""
        pipeline = QualityPipeline(PipelineConfig(verbose=False))
        content = '''
def test_example():
    assert 1 + 1 == 2

class TestExample:
    def test_method(self):
        pass
'''

        result = await pipeline.execute(content, QualityStage.TEST)
        assert result is not None

    @pytest.mark.asyncio
    async def test_lint_stage(self):
        """测试LINT阶段"""
        pipeline = QualityPipeline(PipelineConfig(verbose=False))
        content = "def test():\n    pass"

        result = await pipeline.execute(content, QualityStage.LINT)
        assert result is not None

    @pytest.mark.asyncio
    async def test_critique_stage(self):
        """测试CRITIQUE阶段"""
        pipeline = QualityPipeline(PipelineConfig(verbose=False))
        content = "def test():\n    pass"

        result = await pipeline.execute(content, QualityStage.CRITIQUE)
        assert result is not None
        # CRITIQUE 阶段即使有问题也应该通过
        assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_refine_stage(self):
        """测试REFINE阶段"""
        pipeline = QualityPipeline(PipelineConfig(verbose=False))
        content = "def test():\n    pass"

        result = await pipeline.execute(content, QualityStage.REFINE)
        assert result is not None
        # REFINE 总是尝试优化

    @pytest.mark.asyncio
    async def test_escalate_stage_no_issues(self):
        """测试ESCALATE阶段 - 无问题"""
        pipeline = QualityPipeline(PipelineConfig(verbose=False))
        content = "def test():\n    pass"

        result = await pipeline.execute(content, QualityStage.ESCALATE)
        assert result.success is True
        assert result.metadata is not None

    @pytest.mark.asyncio
    async def test_escalate_stage_with_dangerous_code(self):
        """测试ESCALATE阶段 - 危险代码"""
        pipeline = QualityPipeline(PipelineConfig(verbose=False))
        content = "eval('dangerous code')"

        result = await pipeline.execute(content, QualityStage.ESCALATE)
        assert result.success is True
        assert result.metadata.get("should_escalate") is True

    @pytest.mark.asyncio
    async def test_arbiter_stage(self):
        """测试ARBITER阶段"""
        pipeline = QualityPipeline(PipelineConfig(verbose=False))
        content = "def test():\n    pass"

        result = await pipeline.execute(content, QualityStage.ARBITER)
        assert result is not None
        assert result.output is not None


class TestQualityPipelineFull:
    """测试完整管道执行"""

    @pytest.mark.asyncio
    async def test_execute_8stages(self):
        """测试执行全部8个阶段"""
        pipeline = QualityPipeline(PipelineConfig(verbose=False))
        content = '''
def calculate_sum(numbers):
    """计算列表总和"""
    total = 0
    for n in numbers:
        total += n
    return total

if __name__ == "__main__":
    result = calculate_sum([1, 2, 3, 4, 5])
    print(f"Sum: {result}")
'''

        results = await pipeline.execute_full(content)
        assert len(results) == 8  # 8个阶段
        assert all(isinstance(r, StageResult) for r in results)

    @pytest.mark.asyncio
    async def test_execute_with_disabled_stages(self):
        """测试禁用某些阶段"""
        config = PipelineConfig(
            typecheck_enabled=False,
            test_enabled=False,
            lint_enabled=False,
            verbose=False
        )
        pipeline = QualityPipeline(config)
        content = "def test():\n    pass"

        results = await pipeline.execute_full(content)
        # 应该跳过 TYPECHECK, TEST, LINT
        assert len(results) < 8

    @pytest.mark.asyncio
    async def test_execute_ful_pipeline(self):
        """测试execute_ful_pipeline方法"""
        pipeline = QualityPipeline(PipelineConfig(verbose=False))
        content = "def test():\n    pass"

        result = await pipeline.execute_full_pipeline(content)
        assert isinstance(result, PipelineResult)
        assert result.total_duration > 0
        assert len(result.stage_results) > 0


class TestQuickPipelineCheck:
    """测试快速管道检查"""

    @pytest.mark.asyncio
    async def test_quick_check(self):
        """测试快速检查"""
        content = '''
def hello():
    print("Hello, World!")
'''
        result = await quick_pipeline_check(content)
        assert isinstance(result, PipelineResult)
        assert result.content == content


class TestPipelineLanguageDetection:
    """测试语言检测"""

    def test_detect_python(self):
        """测试Python检测"""
        pipeline = QualityPipeline()
        content = "def test():\n    pass\nimport os"
        lang = pipeline._detect_language(content)
        assert lang == "python"

    def test_detect_javascript(self):
        """测试JavaScript检测"""
        pipeline = QualityPipeline()
        content = "function test() { return true; }"
        lang = pipeline._detect_language(content)
        assert lang == "javascript"

    def test_detect_typescript(self):
        """测试TypeScript检测"""
        pipeline = QualityPipeline()
        content = "function test(name: string): number { return 1; }"
        lang = pipeline._detect_language(content)
        assert lang == "typescript"


class TestPipelineHistory:
    """测试阶段历史"""

    def test_get_stage_history(self):
        """测试获取阶段历史"""
        pipeline = QualityPipeline()
        history = pipeline.get_stage_history()
        assert isinstance(history, dict)

    def test_reset(self):
        """测试重置管道"""
        pipeline = QualityPipeline()
        pipeline.reset()
        history = pipeline.get_stage_history()
        assert len(history) == 0


class TestPipelineEdgeCases:
    """测试边界情况"""

    @pytest.mark.asyncio
    async def test_very_long_lines(self):
        """测试超长行"""
        pipeline = QualityPipeline(PipelineConfig(verbose=False))
        long_line = "x = " + "a" * 200
        content = f"def test():\n    {long_line}\n"

        result = await pipeline.execute(content, QualityStage.LINT)
        # 应该检测到行太长
        assert any("120字符" in issue for issue in result.issues)

    @pytest.mark.asyncio
    async def test_bracket_mismatch(self):
        """测试括号不匹配"""
        pipeline = QualityPipeline(PipelineConfig(verbose=False))
        content = "function test() { return 1;"  # 缺少 }

        result = await pipeline.execute(content, QualityStage.TYPECHECK, {"language": "javascript"})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_fail_fast_mode(self):
        """测试快速失败模式"""
        config = PipelineConfig(fail_fast=True, verbose=False)
        pipeline = QualityPipeline(config)
        content = "invalid python code @#$%"

        # 由于第一个阶段就会失败，后续阶段应该被跳过
        results = await pipeline.execute_full(content)
        # 快速失败模式会在第一个失败后停止


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])