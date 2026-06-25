"""进化优化模块 - WorkBuddy自我进化系统的核心优化模块

该模块提供两个核心进化优化机制:
- GEPA: 基于遗传算法的提示词进化优化
- SelfReflection: 自我反思机制

主要功能:
- 提示词生成与优化 (GEPA)
- 持续学习与改进 (SelfReflection)
- 从执行经验中提取知识
- 自动调整优化策略
"""
from evolution.gepa import (
    GEPA,
    GEPAConfig,
    PromptMutationType,
    PromptFitnessMetric,
    PromptVariant,
    EvolutionResult,
    quick_evolve
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
    quick_reflect
)

__all__ = [
    # GEPA
    "GEPA",
    "GEPAConfig",
    "PromptMutationType",
    "PromptFitnessMetric",
    "PromptVariant",
    "EvolutionResult",
    "quick_evolve",
    # SelfReflection
    "SelfReflection",
    "ReflectionDepth",
    "LearningType",
    "ImpactLevel",
    "Experience",
    "Reflection",
    "Learning",
    "ImprovementAction",
    "ReflectionCycleResult",
    "quick_reflect"
]