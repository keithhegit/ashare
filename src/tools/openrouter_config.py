import os
import time
from google import genai
from dotenv import load_dotenv
from dataclasses import dataclass
import backoff
from src.utils.logging_config import setup_logger, SUCCESS_ICON, ERROR_ICON, WAIT_ICON
from src.utils.llm_clients import LLMClientFactory

# 设置日志记录
logger = setup_logger('api_calls')


@dataclass
class ChatMessage:
    content: str


@dataclass
class ChatChoice:
    message: ChatMessage


@dataclass
class ChatCompletion:
    choices: list[ChatChoice]


# 获取项目根目录
project_root = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(project_root, '.env')

# 加载环境变量
if os.path.exists(env_path):
    load_dotenv(env_path, override=True)
    logger.info(f"{SUCCESS_ICON} 已加载环境变量: {env_path}")
else:
    logger.warning(f"{ERROR_ICON} 未找到环境变量文件: {env_path}")

# 移除全局环境变量校验和 Gemini 客户端初始化

def get_chat_completion(messages, model=None, max_retries=3, initial_retry_delay=1,
                        client_type="auto", api_key=None, base_url=None):
    """
    获取聊天完成结果，包含重试逻辑
    Args:
        messages: 消息列表，OpenAI 格式
        model: 模型名称（可选）
        max_retries: 最大重试次数
        initial_retry_delay: 初始重试延迟（秒）
        client_type: 客户端类型 ("auto", "gemini", "openai_compatible")
        api_key: API 密钥（可选，仅用于 OpenAI Compatible API）
        base_url: API 基础 URL（可选，仅用于 OpenAI Compatible API）
    Returns:
        str: 模型回答内容或 None（如果出错）
    """
    try:
        # 创建客户端（延迟初始化，自动选择）
        client = LLMClientFactory.create_client(
            client_type=client_type,
            api_key=api_key,
            base_url=base_url,
            model=model
        )
        # 获取回答
        return client.get_completion(
            messages=messages,
            max_retries=max_retries,
            initial_retry_delay=initial_retry_delay
        )
    except Exception as e:
        logger.error(f"{ERROR_ICON} get_chat_completion 发生错误: {str(e)}")
        return None
