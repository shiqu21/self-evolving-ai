"""Token优化器 - 优化提示词、减少Token使用"""
import asyncio
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import Counter
import json
import hashlib
from functools import lru_cache

from agents.base import BaseAgent, AgentResult, AgentType, Task
from utils.llm_client import get_llm_client
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class OptimizationResult:
    """优化结果"""
    original_prompt: str = ""
    optimized_prompt: str = ""
    original_token_count: int = 0
    optimized_token_count: int = 0
    reduction: float = 0.0
    changes: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_prompt": self.original_prompt,
            "optimized_prompt": self.optimized_prompt,
            "original_token_count": self.original_token_count,
            "optimized_token_count": self.optimized_token_count,
            "reduction": self.reduction,
            "changes": self.changes,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class CompressionStats:
    """压缩统计"""
    total_prompts: int = 0
    total_tokens_saved: int = 0
    avg_reduction: float = 0.0
    techniques_used: Dict[str, int] = field(default_factory=dict)


class TokenOptimizerAgent(BaseAgent):
    """Token优化器代理
    
    负责:
    1. 优化 - 优化提示词以减少Token使用
    2. 压缩 - 压缩提示词同时保留关键信息
    3. 建议 - 提供Token使用优化建议
    """

    name: str = "token_optimizer"
    description: str = "Token优化器，优化提示词、减少Token使用"
    agent_type: AgentType = AgentType.TOKEN_OPTIMIZER

    def __init__(self):
        super().__init__()
        self._llm_client = get_llm_client()
        self._optimization_history: List[OptimizationResult] = []
        self._compression_stats = CompressionStats()
        
        # 常用词汇表(用于压缩)
        self._vocabulary: Dict[str, str] = {}
        self._common_phrases: Set[str] = self._init_common_phrases()

    async def execute(self, task: Task) -> AgentResult:
        """执行Token优化
        
        Args:
            task: 优化任务
            
        Returns:
            AgentResult: 优化结果
        """
        start_time = datetime.now()
        
        try:
            action = task.payload.get("action", "optimize")
            
            if action == "optimize":
                result_data = await self.optimize(task.payload)
            elif action == "compress":
                result_data = await self.compress(task.payload)
            elif action == "suggest":
                result_data = await self.suggest(task.payload)
            elif action == "analyze":
                result_data = await self.analyze_tokens(task.payload)
            else:
                result_data = {"message": f"未知操作: {action}"}
            
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return AgentResult(
                success=True,
                data=result_data,
                metadata={
                    "action": action,
                    "optimizations_count": len(self._optimization_history),
                    "stats": {
                        "total_tokens_saved": self._compression_stats.total_tokens_saved,
                        "avg_reduction": self._compression_stats.avg_reduction
                    }
                },
                agent_type=self.agent_type.value,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            logger.error(f"Token优化执行失败: {e}", exc_info=True)
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            return AgentResult(
                success=False,
                error=str(e),
                agent_type=self.agent_type.value,
                execution_time_ms=execution_time
            )

    async def optimize(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """优化提示词
        
        对提示词进行多维度优化，减少Token使用
        
        Args:
            payload: 优化参数，包含prompt
            
        Returns:
            Dict[str, Any]: 优化结果
        """
        original_prompt = payload.get("prompt", "")
        context = payload.get("context", "")
        preserve_format = payload.get("preserve_format", True)
        
        logger.info(f"开始优化提示词 (原始长度: {len(original_prompt)})")
        
        # 计算原始Token数
        original_count = self._estimate_tokens(original_prompt)
        
        changes = []
        optimized = original_prompt
        
        # 1. 移除冗余空白
        if self._has_excess_whitespace(optimized):
            optimized = self._compress_whitespace(optimized)
            changes.append({"type": "whitespace", "description": "移除冗余空白"})
        
        # 2. 合并重复内容
        merged, dup_count = self._merge_duplicates(optimized)
        if dup_count > 0:
            optimized = merged
            changes.append({"type": "deduplication", "count": dup_count, "description": "合并重复内容"})
        
        # 3. 简化格式化
        if preserve_format:
            optimized, fmt_changes = self._simplify_formatting(optimized)
            if fmt_changes:
                changes.append({"type": "formatting", "description": "简化格式", "count": fmt_changes})
        
        # 4. 移除冗余说明
        optimized, redundancy_changes = self._remove_redundancy(optimized)
        changes.extend(redundancy_changes)
        
        # 5. 压缩常用短语
        optimized, phrase_changes = self._compress_phrases(optimized)
        changes.extend(phrase_changes)
        
        # 计算优化后Token数
        optimized_count = self._estimate_tokens(optimized)
        
        # 计算节省
        reduction = (original_count - optimized_count) / max(original_count, 1) * 100
        
        # 创建优化结果
        result = OptimizationResult(
            original_prompt=original_prompt,
            optimized_prompt=optimized,
            original_token_count=original_count,
            optimized_token_count=optimized_count,
            reduction=round(reduction, 2),
            changes=changes
        )
        
        self._optimization_history.append(result)
        self._update_stats(result)
        
        final_result = {
            "original_prompt": original_prompt,
            "optimized_prompt": optimized,
            "original_token_count": original_count,
            "optimized_token_count": optimized_count,
            "tokens_saved": original_count - optimized_count,
            "reduction_percent": round(reduction, 2),
            "changes": changes,
            "timestamp": result.timestamp.isoformat()
        }
        
        logger.info(f"优化完成: {original_count} -> {optimized_count} tokens (节省 {reduction:.1f}%)")
        return final_result

    async def compress(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """压缩提示词
        
        对提示词进行深度压缩
        
        Args:
            payload: 压缩参数
            
        Returns:
            Dict[str, Any]: 压缩结果
        """
        prompt = payload.get("prompt", "")
        target_ratio = payload.get("target_ratio", 0.5)  # 目标压缩比例
        preserve_key_info = payload.get("preserve_key_info", True)
        
        logger.info(f"开始压缩提示词 (目标压缩: {target_ratio*100}%)")
        
        original_count = self._estimate_tokens(prompt)
        optimized = prompt
        
        # 多轮压缩
        for round_num in range(3):
            # 检查是否达到目标
            current_ratio = self._estimate_tokens(optimized) / max(original_count, 1)
            if current_ratio <= target_ratio:
                break
            
            # 每一轮应用不同的压缩技术
            if round_num == 0:
                # 移除所有多余空白
                optimized = self._compress_whitespace(optimized)
            elif round_num == 1:
                # 简化句子
                optimized = self._shorten_sentences(optimized)
            else:
                # 移除次要信息
                optimized = self._remove_secondary_info(optimized)
        
        optimized_count = self._estimate_tokens(optimized)
        
        # 确保关键信息被保留
        if preserve_key_info:
            optimized = self._ensure_key_info(optimized, prompt)
            optimized_count = self._estimate_tokens(optimized)
        
        # 额外优化
        final_optimize = await self.optimize({"prompt": optimized, "preserve_format": False})
        optimized = final_optimize.get("optimized_prompt", optimized)
        optimized_count = final_optimize.get("optimized_token_count", optimized_count)
        
        return {
            "original_prompt": prompt,
            "compressed_prompt": optimized,
            "original_token_count": original_count,
            "compressed_token_count": optimized_count,
            "compression_ratio": round(optimized_count / max(original_count, 1), 2),
            "tokens_saved": original_count - optimized_count,
            "target_achieved": optimized_count <= original_count * target_ratio
        }

    async def suggest(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """提供优化建议
        
        分析提示词并给出优化建议
        
        Args:
            payload: 分析参数
            
        Returns:
            Dict[str, Any]: 建议结果
        """
        prompt = payload.get("prompt", "")
        
        logger.info("开始分析提示词以提供建议")
        
        # 分析提示词
        issues = []
        suggestions = []
        
        # 检查长度
        token_count = self._estimate_tokens(prompt)
        if token_count > 4000:
            issues.append("提示词过长")
            suggestions.append("将长提示词拆分为多个短提示词")
        
        # 检查重复
        lines = prompt.split('\n')
        if len(lines) != len(set(lines)):
            issues.append("存在重复行")
            suggestions.append("移除重复内容")
        
        # 检查格式化
        if prompt.count('```') > 10:
            issues.append("代码块过多")
            suggestions.append("考虑使用简短示例替代完整代码块")
        
        # 检查冗余词
        redundant_words = ["非常", "极其", "特别", "十分", "相当"]
        found_redundant = [w for w in redundant_words if w in prompt]
        if found_redundant:
            issues.append(f"存在冗余修饰词: {found_redundant}")
            suggestions.append("移除或简化程度副词")
        
        # 检查不必要的说明
        if "请注意" in prompt or "需要说明的是" in prompt:
            issues.append("存在不必要的开场白")
            suggestions.append("直接切入主题，删除冗余说明")
        
        # 检查列表使用
        if prompt.count('\n- ') > 15:
            issues.append("列表项过多")
            suggestions.append("合并相关项或使用更简洁的表达")
        
        # 生成总体建议
        total_issues = len(issues)
        if total_issues == 0:
            recommendation = "提示词结构良好，无需大幅修改"
        elif total_issues <= 2:
            recommendation = "存在少量问题，建议进行优化"
        else:
            recommendation = "存在多个问题，建议进行系统优化"
        
        return {
            "issues": issues,
            "suggestions": suggestions,
            "token_count": token_count,
            "estimated_tokens_per_100_chars": round(token_count / max(len(prompt), 1) * 100, 1),
            "recommendation": recommendation,
            "priority_fixes": suggestions[:3] if suggestions else []
        }

    async def analyze_tokens(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """分析Token使用
        
        详细分析提示词的Token使用
        
        Args:
            payload: 分析参数
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        prompt = payload.get("prompt", "")
        
        # 基本统计
        char_count = len(prompt)
        word_count = len(prompt.split())
        token_count = self._estimate_tokens(prompt)
        line_count = len(prompt.split('\n'))
        
        # Token来源分析
        token_breakdown = self._analyze_token_breakdown(prompt)
        
        # 关键词频率
        keyword_freq = self._analyze_keyword_frequency(prompt)
        
        # 压缩潜力评估
        compression_potential = self._estimate_compression_potential(prompt)
        
        return {
            "basic_stats": {
                "char_count": char_count,
                "word_count": word_count,
                "token_count": token_count,
                "line_count": line_count,
                "avg_chars_per_token": round(char_count / max(token_count, 1), 1)
            },
            "token_breakdown": token_breakdown,
            "top_keywords": keyword_freq,
            "compression_potential": compression_potential,
            "recommendations": self._get_analysis_recommendations(token_breakdown, keyword_freq)
        }

    def _estimate_tokens(self, text: str) -> int:
        """估算Token数量
        
        简单估算: 英文约4字符/token, 中文约1.5字符/token
        
        Args:
            text: 文本
            
        Returns:
            int: 估算的Token数
        """
        if not text:
            return 0
        
        # 估算公式:混合文本约3字符/token
        return max(1, len(text) // 3)

    def _has_excess_whitespace(self, text: str) -> bool:
        """检查是否有过多空白
        
        Args:
            text: 文本
            
        Returns:
            bool: 是否有过多空白
        """
        return '\n\n' in text or '  ' in text

    def _compress_whitespace(self, text: str) -> str:
        """压缩空白
        
        Args:
            text: 原始文本
            
        Returns:
            str: 压缩后的文本
        """
        # 移除多余空行
        lines = text.split('\n')
        non_empty = [line.rstrip() for line in lines if line.strip()]
        
        # 合并多个空行为单个空行
        compressed = '\n'.join(non_empty)
        
        # 移除行尾多余空格
        compressed = '\n'.join(line.rstrip() for line in compressed.split('\n'))
        
        return compressed.strip()

    def _merge_duplicates(self, text: str) -> Tuple[str, int]:
        """合并重复内容
        
        Args:
            text: 文本
            
        Returns:
            Tuple[str, int]: (处理后的文本, 合并的数量)
        """
        lines = text.split('\n')
        seen = set()
        merged_lines = []
        dup_count = 0
        
        for line in lines:
            stripped = line.strip()
            # 跳过完全相同的行
            if stripped and stripped not in seen:
                seen.add(stripped)
                merged_lines.append(line)
            elif stripped and stripped in seen:
                dup_count += 1
        
        return '\n'.join(merged_lines), dup_count

    def _simplify_formatting(self, text: str) -> Tuple[str, int]:
        """简化格式化
        
        Args:
            text: 文本
            
        Returns:
            Tuple[str, int]: (处理后的文本, 简化数量)
        """
        changes = 0
        
        # 简化Markdown标题
        if '####' in text:
            text = text.replace('#### ', '### ')
            changes += 1
        
        # 简化强调标记(保留关键)
        bold_count = text.count('**')
        if bold_count > 10:
            # 只保留第一个和最后一个的强调
            text = text  # 简化逻辑可在此扩展
            changes += 1
        
        return text, changes

    def _remove_redundancy(self, text: str) -> Tuple[str, List[Dict]]:
        """移除冗余内容
        
        Args:
            text: 文本
            
        Returns:
            Tuple[str, List[Dict]]: (处理后的文本, 变更记录)
        """
        changes = []
        original = text
        
        # 移除冗余开场白
        redundant_openings = [
            "以下是",
            "请注意",
            "需要说明的是",
            "下面",
            "接下来"
        ]
        
        for opening in redundant_openings:
            if opening in text:
                # 检查是否在开头
                idx = text.find(opening)
                if idx < 20:  # 在开头附近
                    # 找到该句子的结束位置
                    end_idx = text.find('.', idx)
                    if end_idx > 0:
                        text = text[:idx] + text[end_idx+1:]
                        changes.append({"type": "opening", "removed": opening})
        
        return text.strip(), changes

    def _compress_phrases(self, text: str) -> Tuple[str, List[Dict]]:
        """压缩常用短语
        
        Args:
            text: 文本
            
        Returns:
            Tuple[str, List[Dict]]: (处理后的文本, 变更记录)
        """
        changes = []
        
        # 定义常用短语替换
        replacements = [
            ("请确保", "确保"),
            ("请注意", "注意"),
            ("需要实现", "实现"),
            ("可以进行", "可"),
            ("需要完成", "完成"),
            ("具有以下功能", "功能"),
            ("执行以下操作", "执行"),
            ("首先", ""),
            ("然后", "，"),
            ("接下来", "，")
        ]
        
        for old, new in replacements:
            if old in text:
                text = text.replace(old, new)
                if new:  # 只记录非空替换
                    changes.append({"type": "phrase", "old": old, "new": new})
                else:
                    changes.append({"type": "remove", "removed": old})
        
        return text, changes

    def _shorten_sentences(self, text: str) -> str:
        """缩短句子
        
        Args:
            text: 文本
            
        Returns:
            str: 处理后的文本
        """
        # 简化复合句
        sentences = text.split('. ')
        shortened = []
        
        for sentence in sentences:
            # 移除冗余连接词
            sentence = sentence.replace('，然后', '，')
            sentence = sentence.replace('，接下来', '，')
            shortened.append(sentence)
        
        return '. '.join(shortened)

    def _remove_secondary_info(self, text: str) -> str:
        """移除次要信息
        
        Args:
            text: 文本
            
        Returns:
            str: 处理后的文本
        """
        # 移除详细解释
        lines = text.split('\n')
        important_lines = []
        
        for line in lines:
            # 保留标题和简短说明
            if len(line) < 100 or line.strip().startswith('#'):
                important_lines.append(line)
            # 或者行中有关键词
            elif any(kw in line.lower() for kw in ['重要', '必须', '关键', 'primary', 'important', 'must']):
                important_lines.append(line)
        
        return '\n'.join(important_lines)

    def _ensure_key_info(self, optimized: str, original: str) -> str:
        """确保关键信息被保留
        
        Args:
            optimized: 优化后的文本
            original: 原始文本
            
        Returns:
            str: 确保关键信息后的文本
        """
        # 提取关键信息
        key_phrases = []
        
        # 保留以特定关键词开头的行
        for line in original.split('\n'):
            stripped = line.strip()
            if stripped.startswith(('# ', '## ', '### ')):
                key_phrases.append(line)
            elif any(stripped.startswith(kw) for kw in ['请', '请务必', '必须']):
                key_phrases.append(line)
        
        # 如果关键信息丢失，添加回去
        for phrase in key_phrases:
            if phrase not in optimized:
                optimized = phrase + '\n' + optimized
        
        return optimized

    def _analyze_token_breakdown(self, text: str) -> Dict[str, Any]:
        """分析Token使用分布
        
        Args:
            text: 文本
            
        Returns:
            Dict: 分析结果
        """
        total = self._estimate_tokens(text)
        
        # 估算各部分Token
        code_blocks = len(re.findall(r'```[\s\S]*?```', text))
        code_tokens = code_blocks * 50  # 估算
        
        list_items = text.count('\n- ') + text.count('\n* ')
        list_tokens = list_items * 3
        
        prompt_text_tokens = total - code_tokens - list_tokens
        
        return {
            "total_tokens": total,
            "estimated_code_tokens": code_tokens,
            "estimated_list_tokens": list_tokens,
            "estimated_text_tokens": prompt_text_tokens,
            "code_block_count": code_blocks,
            "list_item_count": list_items
        }

    def _analyze_keyword_frequency(self, text: str) -> List[Tuple[str, int]]:
        """分析关键词频率
        
        Args:
            text: 文本
            
        Returns:
            List[Tuple[str, int]]: (关键词, 频率)
        """
        # 简单分词
        words = re.findall(r'\b\w{4,}\b', text.lower())
        
        # 过滤停用词
        stop_words = {'请注意', '需要', '可以', '进行', '实现', '以下', '这个', '那个'}
        words = [w for w in words if w not in stop_words]
        
        # 统计频率
        counter = Counter(words)
        
        return counter.most_common(10)

    def _estimate_compression_potential(self, text: str) -> Dict[str, Any]:
        """估算压缩潜力
        
        Args:
            text: 文本
            
        Returns:
            Dict: 估算结果
        """
        potential = 0
        
        # 多余空白
        if '\n\n' in text or '  ' in text:
            potential += 10
        
        # 重复内容
        lines = text.split('\n')
        if len(lines) != len(set(lines)):
            potential += 15
        
        # 冗余词
        redundant = ['请确保', '请注意', '非常', '特别']
        if any(w in text for w in redundant):
            potential += 10
        
        # 长列表
        if text.count('\n- ') > 10:
            potential += 15
        
        return {
            "compression_potential_percent": min(potential, 50),
            "estimated_savings_tokens": int(self._estimate_tokens(text) * potential / 100)
        }

    def _get_analysis_recommendations(
        self, 
        breakdown: Dict, 
        keywords: List[Tuple]
    ) -> List[str]:
        """获取分析建议
        
        Args:
            breakdown: Token分布
            keywords: 关键词频率
            
        Returns:
            List[str]: 建议列表
        """
        recommendations = []
        
        if breakdown.get("code_block_count", 0) > 5:
            recommendations.append("考虑减少代码块数量，使用描述替代示例")
        
        if breakdown.get("list_item_count", 0) > 15:
            recommendations.append("列表项过多，考虑合并或删除次要项")
        
        if keywords and keywords[0][1] > 10:
            recommendations.append(f"关键词 '{keywords[0][0]}' 出现频率过高")
        
        if not recommendations:
            recommendations.append("Token使用合理，保持当前格式")
        
        return recommendations

    def _update_stats(self, result: OptimizationResult):
        """更新统计信息
        
        Args:
            result: 优化结果
        """
        self._compression_stats.total_prompts += 1
        self._compression_stats.total_tokens_saved += (
            result.original_token_count - result.optimized_token_count
        )
        
        # 更新平均节省
        if self._compression_stats.total_prompts > 0:
            self._compression_stats.avg_reduction = (
                self._compression_stats.total_tokens_saved / 
                max(sum(r.original_token_count for r in self._optimization_history), 1) * 100
            )
        
        # 记录使用的技术
        for change in result.changes:
            tech = change.get("type", "unknown")
            self._compression_stats.techniques_used[tech] = \
                self._compression_stats.techniques_used.get(tech, 0) + 1

    def _init_common_phrases(self) -> Set[str]:
        """初始化常用短语
        
        Returns:
            Set[str]: 常用短语集合
        """
        return {
            "请确保",
            "请注意",
            "需要注意",
            "需要实现",
            "具有以下",
            "执行以下",
            "请完成",
            "请执行"
        }

    def get_statistics(self) -> Dict[str, Any]:
        """获取优化统计
        
        Returns:
            Dict: 统计信息
        """
        return {
            "total_optimizations": len(self._optimization_history),
            "total_tokens_saved": self._compression_stats.total_tokens_saved,
            "avg_reduction_percent": round(self._compression_stats.avg_reduction, 2),
            "techniques_used": self._compression_stats.techniques_used,
            "recent_results": [r.to_dict() for r in self._optimization_history[-5:]]
        }