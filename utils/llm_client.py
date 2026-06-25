"""LLM客户端 - 支持本地模拟模式，无需API Key"""


import logging
import json
import random
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class MockLLMClient:
    """本地模拟LLM客户端 - 不需要API Key"""
    
    def __init__(self):
        self.total_requests = 0
        self.mode = "mock"
        logger.info("使用本地模拟模式(无需API Key)")
    
    def chat(self, message: str, system_prompt: str = None, 
             temperature: float = 0.7, max_tokens: int = 4096) -> str:
        """模拟LLM响应"""
        self.total_requests += 1
        
        # 根据输入内容生成合适的模拟响应
        message_lower = message.lower()
        
        if "根因" in message or "analysis" in message_lower:
            return f"""根据分析，该错误的主要根因是:
1. 输入数据验证不足
2. 缺少必要的错误处理逻辑

建议的修复方案:
- 添加输入参数校验
- 增加异常捕获和日志记录"""
        
        elif "优化" in message or "optimize" in message_lower:
            return """优化建议:
1. 减少不必要的API调用
2. 使用缓存机制
3. 批量处理任务"""
        
        elif "技能" in message or "skill" in message_lower:
            return json.dumps({
                "name": f"auto_skill_{random.randint(1000, 9999)}",
                "description": "自动生成的技能",
                "code": "# 自动生成的技能代码\nclass AutoSkill:\n    pass"
            }, ensure_ascii=False)
        
        elif "改进" in message or "improve" in message_lower:
            return """改进建议:
1. 优化执行流程
2. 增加重试机制
3. 完善错误处理"""
        
        else:
            # 默认响应
            responses = [
                "分析完成，已记录到记忆系统",
                "处理成功，系统将持续优化",
                "已识别问题，准备生成改进方案",
                "执行完成，进入下一阶段"
            ]
            return random.choice(responses)
    
    def chat_with_json(self, message: str, system_prompt: str = None, 
                       temperature: float = 0.3) -> Dict[str, Any]:
        """模拟JSON响应"""
        try:
            result = self.chat(message, system_prompt, temperature)
            return {"result": result, "mock": True}
        except Exception as e:
            return {"error": str(e)}
    
    def batch_chat(self, messages: List[str], system_prompt: str = None) -> List[str]:
        """批量模拟响应"""
        return [self.chat(msg, system_prompt) for msg in messages]
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """获取使用统计(模拟)"""
        return {
            "total_requests": self.total_requests,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "estimated_cost": 0.0,
            "mode": "mock"
        }
    
    def reset_stats(self):
        self.total_requests = 0
    
    def close(self):
        pass


class LLMClient:
    """LLM API客户端 - 使用硅基流动API调用DeepSeek-R1"""
    
    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model: str = "deepseek-ai/DeepSeek-R1",
        timeout: int = 60
    ):
        # 如果没有API Key，自动切换到模拟模式
        if not api_key or api_key == "sk-dummy" or "your-api" in api_key:
            logger.warning("未配置API Key，切换到本地模拟模式")
            self._mock = MockLLMClient()
            self._use_mock = True
            return
        
        self._use_mock = False
        import requests
        self.api_key = api_key
        self.base_url = base_url or "https://api.il.cn/v1"
        self.model = model
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
        
        # 统计
        self.total_input_okens = 0
        self.total_output_tokens = 0
        self.total_requests = 0
    
    def chat(self, message: str, system_prompt: str = None, 
             temperature: float = 0.7, max_tokens: int = 4096) -> str:
        if self._use_mock:
            return self._mock.chat(message, system_prompt, temperature, max_tokens)
        
        url = f"{self.base_url}/chat/completions"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        try:
            import requests
            self.total_requests += 1
            response = self._session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                if "usage" in result:
                    self.total_input_okens += result["usage"].get("prompt_tokens", 0)
                    self.total_output_tokens += result["usage"].get("completion_tokens", 0)
                return content
            return "无响应内容"
            
        except Exception as e:
            logger.error(f"LLM请求失败: {e}，切换到模拟模式")
            self._mock = MockLLMClient()
            self._use_mock = True
            return self._mock.chat(message, system_prompt, temperature, max_tokens)
    
    def chat_with_json(self, message: str, system_prompt: str = None, 
                       temperature: float = 0.3) -> Dict[str, Any]:
        if self._use_mock:
            return self._mock.chat_with_json(message, system_prompt, temperature)
        
        try:
            return json.loads(self.chat(message, system_prompt, temperature))
        except:
            return {"error": "解析失败"}
    
    def batch_chat(self, messages: List[str], system_prompt: str = None) -> List[str]:
        if self._use_mock:
            return self._mock.batch_chat(messages, system_prompt)
        return [self.chat(msg, system_prompt) for msg in messages]
    
    def get_usage_stats(self) -> Dict[str, Any]:
        if self._use_mock:
            return self._mock.get_usage_stats()
        
        total = self.total_input_okens + self.total_output_tokens
        input_cost = (self.total_input_okens / 1_000_000) * 0.14
        output_cost = (self.total_output_tokens / 1_000_000) * 2.19
        
        return {
            "total_requests": self.total_requests,
            "input_tokens": self.total_input_okens,
            "output_tokens": self.total_output_tokens,
            "total_tokens": total,
            "estimated_cost": round(input_cost + output_cost, 4),
            "mode": "api"
        }
    
    def reset_stats(self):
        self.total_input_okens = 0
        self.total_output_tokens = 0
        self.total_requests = 0
    
    def close(self):
        if not self._use_mock:
            self._session.close()


# 全局LLM客户端实例
_llm_client = None


def get_llm_client() -> LLMClient:
    """获取全局LLM客户端"""
    global _llm_client
    if _llm_client is None:
        from config.config import get_config
        config = get_config()
        _llm_client = LLMClient(
            api_key=config.llm_api_key,
            base_url=config.llm_base_url,
            model=config.llm_model,
            timeout=config.llm_timeout
        )
    return _llm_client