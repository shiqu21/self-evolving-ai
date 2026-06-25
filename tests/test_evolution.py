"""进化模块测试 - WorkBuddy自我进化系统

测试进化模块的导入和功能:
- GEPA: Genetic-Pareto Prompt Evolution (遗传Pareto提示词进化)
- SelfReflection: 自我反思机制

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
from evolution.gepa import (
    GEPA,
    GEPAConfig,
    GEPA as GEPAModule,  # 测试从evolution包导入
    GEPAConfig as GEPAConfigModule,
    PromptMutationType,
    PromptFitnessMetric,
    PromptVariant,
    EvolutionResult,
    quick_evolve,
    PromptEvolutionRepository,
)

from evolution.self_reflection import (
    SelfReflection,
    ReflectionDepth,
    LearningType,
    ImpactLevel,
    Experience,
    Reflection,
    Learning,
    ImprovementAction,
    ReflectionCycleResult,
    quick_reflect,
)


# ==================== GEPA测试 ====================

class TestGEPAImports:
    """测试GEPA模块导入"""

    def test_import_gepa(self):
        """测试导入GEPA"""
        assert GEPA is not None

    def test_import_gepa_config(self):
        """测试导入GEPAConfig"""
        assert GEPAConfig is not None

    def test_import_prompt_mutation_type(self):
        """测试导入变异类型"""
        assert PromptMutationType is not None

    def test_import_prompt_fitness_metric(self):
        """测试导入适应度指标"""
        assert PromptFitnessMetric is not None

    def test_import_prompt_variant(self):
        """测试导入提示词变体"""
        assert PromptVariant is not None

    def test_import_evolution_result(self):
        """测试导入进化结果"""
        assert EvolutionResult is not None

    def test_import_quick_evolve(self):
        """测试导入快速进化函数"""
        assert quick_evolve is not None


class TestPromptMutationType:
    """测试提示词变异类型枚举"""

    def test_mutation_type_values(self):
        """测试变异类型值"""
        assert PromptMutationType.REWRITE.value == "rewrite"
        assert PromptMutationType.EXPAND.value == "expand"
        assert PromptMutationType.CONTRACT.value == "contract"
        assert PromptMutationType.SPECIFY.value == "specify"
        assert PromptMutationType.ABSTRACT.value == "abstract"
        assert PromptMutationType.ADD_CONTEXT.value == "add_context"
        assert PromptMutationType.ADD_CONSTRAINT.value == "add_constraint"
        assert PromptMutationType.CHANGE_PERSPECTIVE.value == "change_perspective"
        assert PromptMutationType.ADD_EXAMPLE.value == "add_example"
        assert PromptMutationType.ADD_FORMAT.value == "add_format"

    def test_mutation_type_count(self):
        """测试变异类型数量"""
        assert len(PromptMutationType) == 10


class TestPromptFitnessMetric:
    """测试适应度指标枚举"""

    def test_metric_values(self):
        """测试指标值"""
        assert PromptFitnessMetric.QUALITY.value == "quality"
        assert PromptFitnessMetric.TOKEN_EFFICIENCY.value == "token_efficiency"
        assert PromptFitnessMetric.SUCCESS_RATE.value == "success_rate"
        assert PromptFitnessMetric.CONSISTENCY.value == "consistency"
        assert PromptFitnessMetric.CLARITY.value == "clarity"

    def test_metric_count(self):
        """测试指标数量"""
        assert len(PromptFitnessMetric) == 5


class TestGEPAConfig:
    """测试GEPA配置"""

    def test_default_config(self):
        """测试默认配置"""
        config = GEPAConfig()
        assert config.population_size == 10
        assert config.elite_size == 2
        assert config.mutation_rate == 0.3
        assert config.crossover_rate == 0.2
        assert config.max_generations == 5
        assert config.tournament_size == 3
        assert config.min_fitness_threshold == 0.8
        assert config.convergence_threshold == 0.01
        assert config.max_retries == 3

    def test_custom_config(self):
        """测试自定义配置"""
        config = GEPAConfig(
            population_size=20,
            elite_size=5,
            max_generations=10,
            mutation_rate=0.5
        )
        assert config.population_size == 20
        assert config.elite_size == 5
        assert config.max_generations == 10
        assert config.mutation_rate == 0.5


class TestPromptVariant:
    """测试提示词变体"""

    def test_creation(self):
        """测试创建变体"""
        variant = PromptVariant(
            id="test_001",
            content="测试提示词内容",
            parent_id=None,
            mutation_type=PromptMutationType.REWRITE,
            fitness=0.85,
            generation=1
        )
        assert variant.id == "test_001"
        assert variant.content == "测试提示词内容"
        assert variant.fitness == 0.85

    def test_creation_with_default(self):
        """测试默认参数创建"""
        variant = PromptVariant(
            id="test_002",
            content="另一个测试"
        )
        assert variant.fitness == 0.0
        assert variant.mutation_type == PromptMutationType.REWRITE
        assert variant.generation == 1

    def test_to_dict(self):
        """测试转换为字典"""
        variant = PromptVariant(
            id="test_003",
            content="测试",
            fitness=0.9
        )
        data = variant.to_dict()
        assert "id" in data
        assert "content" in data
        assert data["fitness"] == 0.9


class TestEvolutionResult:
    """测试进化结果"""

    def test_creation(self):
        """测试创建进化结果"""
        variants = [
            PromptVariant(id="v1", content="内容1", fitness=0.8),
            PromptVariant(id="v2", content="内容2", fitness=0.9),
        ]
        result = EvolutionResult(
            best_prompt="最佳提示词",
            best_fitness=0.9,
            variants=variants,
            generations=3,
            total_evaluations=30,
            duration=10.5,
            converged=True
        )
        assert result.best_prompt == "最佳提示词"
        assert result.best_fitness == 0.9
        assert len(result.variants) == 2
        assert result.generations == 3
        assert result.converged is True


class TestGEPAInstance:
    """测试GEPA实例"""

    def test_creation(self):
        """测试GEPA创建"""
        gepa = GEPA()
        assert gepa is not None

    def test_creation_with_config(self):
        """测试带配置的创建"""
        config = GEPAConfig(population_size=5, max_generations=2)
        gepa = GEPA(config)
        assert gepa.config.population_size == 5
        assert gepa.config.max_generations == 2

    def test_generate_variants(self):
        """测试生成变体"""
        gepa = GEPA(GEPAConfig(population_size=3, max_generations=1))
        base_prompt = "请写一个Python函数"
        variants = gepa.generate_variants(base_prompt, n=3)
        assert len(variants) == 3
        assert all(isinstance(v, PromptVariant) for v in variants)

    def test_calculate_fitness(self):
        """测试计算适应度"""
        gepa = GEPA()
        metrics = {
            PromptFitnessMetric.QUALITY: 0.9,
            PromptFitnessMetric.SUCCESS_RATE: 0.8,
            PromptFitnessMetric.CLARITY: 0.7,
            PromptFitnessMetric.CONSISTENCY: 0.85,
            PromptFitnessMetric.TOKEN_EFFICIENCY: 0.6,
        }
        fitness = gepa.calculate_fitness(metrics)
        assert 0 <= fitness <= 1

    def test_select_parents(self):
        """测试选择父本"""
        gepa = GEPA(GEPAConfig(tournament_size=2))
        variants = [
            PromptVariant(id="v1", content="c1", fitness=0.3),
            PromptVariant(id="v2", content="c2", fitness=0.8),
            PromptVariant(id="v3", content="c3", fitness=0.5),
        ]
        parents = gepa.select_parents(variants, n=2)
        assert len(parents) == 2
        assert all(isinstance(p, PromptVariant) for p in parents)

    def test_select_parents_with_small_population(self):
        """测试小种群选择父本"""
        gepa = GEPA(GEPAConfig(tournament_size=3))
        variants = [
            PromptVariant(id="v1", content="c1", fitness=0.3),
            PromptVariant(id="v2", content="c2", fitness=0.8),
        ]
        parents = gepa.select_parents(variants, n=2)
        assert len(parents) == 2

    def test_crossover(self):
        """测试交叉操作"""
        gepa = GEPA()
        parent1 = PromptVariant(id="p1", content="第一行\n第二行\n第三行", fitness=0.9)
        parent2 = PromptVariant(id="p2", content="第四行\n第五行\n第六行", fitness=0.8)
        child = gepa.crossover(parent1, parent2)
        assert isinstance(child, PromptVariant)
        assert child.parent_id == parent1.id

    def test_mutate(self):
        """测试变异操作"""
        gepa = GEPA(GEPAConfig(mutation_rate=1.0))  # 强制变异
        variant = PromptVariant(id="v1", content="测试内容", fitness=0.5)
        mutated = gepa.mutate(variant)
        assert isinstance(mutated, PromptVariant)
        # 变异后的内容可能不同

    def test_mutate_no_mutation(self):
        """测试不触发变异"""
        gepa = GEPA(GEPAConfig(mutation_rate=0.0))  # 不变异
        variant = PromptVariant(id="v1", content="测试内容", fitness=0.5)
        mutated = gepa.mutate(variant)
        assert mutated.id == variant.id  # 相同ID表示未变异

    def test_select_elite(self):
        """测试选择精英"""
        gepa = GEPA(GEPAConfig(elite_size=2))
        variants = [
            PromptVariant(id="v1", content="c1", fitness=0.3),
            PromptVariant(id="v2", content="c2", fitness=0.9),
            PromptVariant(id="v3", content="c3", fitness=0.7),
            PromptVariant(id="v4", content="c4", fitness=0.5),
        ]
        elite = gepa.select_elite(variants)
        assert len(elite) == 2
        assert elite[0].fitness >= elite[1].fitness  # 排序正确

    def test_get_evolution_history(self):
        """测试获取进化历史"""
        gepa = GEPA()
        history = gepa.get_evolution_history()
        assert isinstance(history, list)

    def test_generate_id(self):
        """测试生成唯一ID"""
        gepa = GEPA()
        id1 = gepa._generate_id("测试内容1")
        id2 = gepa._generate_id("测试内容2")
        assert id1 != id2


class TestGEPAEvolution:
    """测试GEPA进化过程"""

    @pytest.mark.asyncio
    async def test_evolve(self):
        """测试完整进化过程"""
        gepa = GEPA(GEPAConfig(population_size=3, max_generations=2))
        base_prompt = "请写一个Python函数计算斐波那契数列"

        result = await gepa.evolve(base_prompt, iterations=1)
        assert isinstance(result, EvolutionResult)
        assert result.generations >= 1

    @pytest.mark.asyncio
    async def test_evaluate_variant(self):
        """测试评估变体"""
        gepa = GEPA()
        variant = PromptVariant(id="test", content="测试提示词", fitness=0.0)
        evaluated = await gepa.evaluate_variant(variant)
        assert evaluated.fitness >= 0  # 应该有评分

    @pytest.mark.asyncio
    async def test_evaluate_with_test_cases(self):
        """测试使用测试用例评估"""
        gepa = GEPA()
        prompt = "测试提示词"
        test_cases = [
            {"input": "test1", "expected_type": "text"},
            {"input": "test2", "expected_type": "text"}
        ]
        metrics = await gepa.evaluate(prompt, test_cases)
        assert isinstance(metrics, dict)
        assert PromptFitnessMetric.QUALITY in metrics


class TestQuickEvolve:
    """测试快速进化函数"""

    @pytest.mark.asyncio
    async def test_quick_evolve(self):
        """测试快速进化"""
        base_prompt = "写一个测试函数"
        result = await quick_evolve(base_prompt, iterations=1)
        assert isinstance(result, EvolutionResult)


# ==================== 自我反思测试 ====================

class TestSelfReflectionImports:
    """测试自我反思模块导入"""

    def test_import_self_reflection(self):
        """测试导入SelfReflection"""
        assert SelfReflection is not None

    def test_import_reflection_depth(self):
        """测试导入ReflectionDepth"""
        assert ReflectionDepth is not None

    def test_import_learning_type(self):
        """测试导入LearningType"""
        assert LearningType is not None

    def test_import_impact_level(self):
        """测试导入ImpactLevel"""
        assert ImpactLevel is not None

    def test_import_experience(self):
        """测试导入Experience"""
        assert Experience is not None

    def test_import_reflection(self):
        """测试导入Reflection"""
        assert Reflection is not None

    def test_import_learning(self):
        """测试导入Learning"""
        assert Learning is not None

    def test_import_improvement_action(self):
        """测试导入ImprovementAction"""
        assert ImprovementAction is not None

    def test_import_quick_reflect(self):
        """测试导入quick_reflect"""
        assert quick_reflect is not None


class TestReflectionDepth:
    """测试反思深度枚举"""

    def test_depth_values(self):
        """测试深度值"""
        assert ReflectionDepth.SURFACE.value == "surface"
        assert ReflectionDepth.CAUSAL.value == "causal"
        assert ReflectionDepth.META.value == "meta"
        assert ReflectionDepth.INTEGRATIVE.value == "integrative"

    def test_depth_count(self):
        """测试深度数量"""
        assert len(ReflectionDepth) == 4


class TestLearningType:
    """测试学习类型枚举"""

    def test_learning_type_values(self):
        """测试学习类型值"""
        assert LearningType.ERROR_CORRECTION.value == "error_correction"
        assert LearningType.SUCCESS_PATTERN.value == "success_pattern"
        assert LearningType.STRATEGY_ADAPTATION.value == "strategy_adaptation"
        assert LearningType.KNOWLEDGE_ACQUISITION.value == "knowledge_acquisition"
        assert LearningType.PERSPECTIVE_SHIFT.value == "perspective_shift"

    def test_learning_type_count(self):
        """测试学习类型数量"""
        assert len(LearningType) == 5


class TestImpactLevel:
    """测试影响级别枚举"""

    def test_impact_level_values(self):
        """测试影响级别值"""
        assert ImpactLevel.LOW.value == 1
        assert ImpactLevel.MEDIUM.value == 2
        assert ImpactLevel.HIGH.value == 3
        assert ImpactLevel.CRITICAL.value == 4


class TestExperience:
    """测试Experience类"""

    def test_creation(self):
        """测试创建经验"""
        exp = Experience(
            id="exp_001",
            context={"action": "test"},
            action="execute",
            result="success",
            expected="success",
            outcome_type="success"
        )
        assert exp.id == "exp_001"
        assert exp.outcome_type == "success"

    def test_get_outcome_score(self):
        """测试获取结果评分"""
        success_exp = Experience(
            id="e1", context={}, action="a", result="r", expected="e", outcome_type="success"
        )
        partial_exp = Experience(
            id="e2", context={}, action="a", result="r", expected="e", outcome_type="partial"
        )
        fail_exp = Experience(
            id="e3", context={}, action="a", result="r", expected="e", outcome_type="failure"
        )

        assert success_exp.get_outcome_score() == 1.0
        assert partial_exp.get_outcome_score() == 0.5
        assert fail_exp.get_outcome_score() == 0.0


class TestReflection:
    """测试Reflection类"""

    def test_creation(self):
        """测试创建反思"""
        ref = Reflection(
            experience_id="exp_001",
            depth=ReflectionDepth.CAUSAL,
            question="为什么成功？",
            insights=["洞察1", "洞察2"],
            root_cause=["原因1"]
        )
        assert ref.experience_id == "exp_001"
        assert ref.depth == ReflectionDepth.CAUSAL
        assert len(ref.insights) == 2


class TestLearning:
    """测试Learning类"""

    def test_creation(self):
        """测试创建学习"""
        learning = Learning(
            id="learn_001",
            type=LearningType.ERROR_CORRECTION,
            content="学习内容",
            source_experience_id="exp_001",
            impact_level=ImpactLevel.HIGH
        )
        assert learning.id == "learn_001"
        assert learning.type == LearningType.ERROR_CORRECTION
        assert learning.impact_level == ImpactLevel.HIGH


class TestImprovementAction:
    """测试ImprovementAction类"""

    def test_creation(self):
        """测试创建改进行动"""
        action = ImprovementAction(
            id="imp_001",
            description="优化代码",
            priority=9,
            estimated_impact=0.8
        )
        assert action.id == "imp_001"
        assert action.priority == 9


class TestReflectionCycleResult:
    """测试ReflectionCycleResult类"""

    def test_creation(self):
        """测试创建反思循环结果"""
        exp = Experience(
            id="e1", context={}, action="a", result="r", expected="e", outcome_type="success"
        )
        ref = Reflection(experience_id="e1", depth=ReflectionDepth.CAUSAL, question="?")
        learnings = [
            Learning(id="l1", type=LearningType.SUCCESS_PATTERN, content="c", source_experience_id="e1")
        ]
        improvements = [
            ImprovementAction(id="i1", description="d", priority=5, estimated_impact=0.5)
        ]

        result = ReflectionCycleResult(
            cycle_id="cycle_001",
            experience=exp,
            reflection=ref,
            learnings=learnings,
            improvements=improvements,
            execution_summary="完成",
            duration=1.5,
            success=True
        )
        assert result.success is True
        assert len(result.learnings) == 1


class TestSelfReflectionInstance:
    """测试SelfReflection实例"""

    def test_creation(self):
        """测试创建SelfReflection"""
        reflection = SelfReflection()
        assert reflection is not None
        assert len(reflection._experiences) == 0
        assert len(reflection._reflections) == 0
        assert len(reflection._learnings) == 0


class TestSelfReflectionMethods:
    """测试SelfReflection方法"""

    @pytest.mark.asyncio
    async def test_record_experience_success(self):
        """测试记录成功经验"""
        reflection = SelfReflection()
        exp = await reflection.record_experience(
            context={"action": "test"},
            action="write_code",
            result="success",
            expected="success"
        )
        assert isinstance(exp, Experience)
        assert exp.outcome_type == "success"

    @pytest.mark.asyncio
    async def test_record_experience_failure(self):
        """测试记录失败经验"""
        reflection = SelfReflection()
        exp = await reflection.record_experience(
            context={"action": "test"},
            action="write_code",
            result="error",
            expected="success"
        )
        assert exp.outcome_type == "failure"

    @pytest.mark.asyncio
    async def test_record_experience_partial(self):
        """测试记录部分成功经验"""
        reflection = SelfReflection()
        exp = await reflection.record_experience(
            context={"action": "test"},
            action="analyze",
            result="分析基本正确",
            expected="分析准确"
        )
        assert exp.outcome_type in ["success", "partial", "failure"]

    @pytest.mark.asyncio
    async def test_reflect(self):
        """测试反思方法"""
        reflection = SelfReflection()
        # 先记录经验
        await reflection.record_experience(
            context={},
            action="test_action",
            result="success"
        )
        # 执行反思
        ref = await reflection.reflect()
        assert isinstance(ref, Reflection)
        assert len(ref.learnings) > 0

    @pytest.mark.asyncio
    async def test_reflect_with_experience(self):
        """测试带经验的反思"""
        reflection = SelfReflection()
        exp = Experience(
            id="test_exp",
            context={"action": "test"},
            action="execute",
            result="failure",
            expected="success",
            outcome_type="failure"
        )
        ref = await reflection.reflect(experience=exp)
        assert ref.experience_id == "test_exp"

    @pytest.mark.asyncio
    async def test_learn(self):
        """测试学习方法"""
        reflection = SelfReflection()
        exp = Experience(
            id="e1",
            context={},
            action="test",
            result="error",
            expected="success",
            outcome_type="failure"
        )
        ref = Reflection(
            experience_id="e1",
            depth=ReflectionDepth.CAUSAL,
            question="?",
            root_causes=["原因1"]
        )
        learnings = await reflection.learn(exp, ref)
        assert len(learnings) > 0

    @pytest.mark.asyncio
    async def test_improve(self):
        """测试改进方法"""
        reflection = SelfReflection()
        learnings = [
            Learning(
                id="l1",
                type=LearningType.ERROR_CORRECTION,
                content="修复错误",
                source_experience_id="e1"
            )
        ]
        improvements = await reflection.improve(learnings)
        assert len(improvements) > 0

    @pytest.mark.asyncio
    async def test_execute_cycle(self):
        """测试执行完整反思循环"""
        reflection = SelfReflection()
        result = await reflection.execute_cycle(
            context={"action": "test_action"},
            action="test",
            result="成功",
            expected="成功"
        )
        assert isinstance(result, ReflectionCycleResult)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_cycle_failure(self):
        """测试失败场景的反思循环"""
        reflection = SelfReflection()
        result = await reflection.execute_cycle(
            context={"action": "analyze", "input": ""},
            action="analyze",
            result="错误: 输入为空",
            expected="分析结果"
        )
        assert isinstance(result, ReflectionCycleResult)
        assert result.success is False
        assert len(result.learnings) > 0

    def test_get_recent_learnings(self):
        """测试获取最近学习成果"""
        reflection = SelfReflection()
        learnings = reflection.get_recent_learnings(n=5)
        assert isinstance(learnings, list)

    def test_get_success_strategies(self):
        """测试获取成功策略"""
        reflection = SelfReflection()
        strategies = reflection.get_success_strategies()
        assert isinstance(strategies, list)

    def test_get_failure_patterns(self):
        """测试获取失败模式"""
        reflection = SelfReflection()
        patterns = reflection.get_failure_patterns()
        assert isinstance(patterns, list)

    def test_get_cycle_history(self):
        """测试获取反思历史"""
        reflection = SelfReflection()
        history = reflection.get_cycle_history()
        assert isinstance(history, list)


class TestQuickReflect:
    """测试快速反思函数"""

    @pytest.mark.asyncio
    async def test_quick_reflect(self):
        """测试快速反思"""
        result = await quick_reflect(
            context={"action": "test"},
            action="execute",
            result="success",
            expected="success"
        )
        assert isinstance(result, ReflectionCycleResult)


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])