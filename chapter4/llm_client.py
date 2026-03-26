from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Optional, Any
import os
import sys


class HelloAgentsLLM:
    """LLM客户端类，支持流式调用和配置管理"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        """
        初始化LLM客户端

        Args:
            base_url: API基础URL，如果为None则从.env文件读取
            api_key: API密钥，如果为None则从.env文件读取
            model: 模型名称，如果为None则从.env文件读取
            timeout: 超时时间（秒），如果为None则从.env文件读取
        """
        # 加载环境变量
        load_dotenv()

        # 优先使用传入参数，其次使用环境变量
        self.base_url = base_url or os.getenv("LLM_BASE_URL")
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.model = model or os.getenv("LLM_MODEL")
        self.timeout = timeout or int(os.getenv("LLM_TIMEOUT", 60))

        # 验证必要参数
        if not self.base_url:
            raise ValueError("base_url is required. Provide it as argument or set LLM_BASE_URL in .env file")
        if not self.api_key:
            raise ValueError("api_key is required. Provide it as argument or set LLM_API_KEY in .env file")
        if not self.model:
            raise ValueError("model is required. Provide it as argument or set LLM_MODEL in .env file")

        # 初始化OpenAI客户端
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.timeout
        )

        print(f"HelloAgentsLLM initialized with model: {self.model}, base_url: {self.base_url}")

    def think(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = True
    ) -> str:
        """
        调用大模型进行思考（流式调用）

        Args:
            messages: 消息列表，格式如 [{"role": "user", "content": "Hello"}]
            temperature: 温度参数，控制随机性
            max_tokens: 最大输出token数
            stream: 是否使用流式输出

        Returns:
            完整的模型响应文本
        """
        try:
            response_content = ""

            if stream:
                # 流式调用
                print("开始流式调用...")
                stream_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True
                )

                # 处理流式响应
                for chunk in stream_response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        chunk_content = chunk.choices[0].delta.content
                        print(chunk_content, end="", flush=True)
                        response_content += chunk_content

                print()  # 换行
                print("流式调用完成")
            else:
                # 非流式调用
                print("开始非流式调用...")
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=False
                )

                response_content = response.choices[0].message.content
                print(f"非流式调用完成，响应长度: {len(response_content)}")

            return response_content

        except Exception as e:
            print(f"调用大模型时出错: {e}", file=sys.stderr)
            raise

    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return {
            "base_url": self.base_url,
            "model": self.model,
            "timeout": self.timeout,
            "api_key": self.api_key[:10] + "..." if self.api_key else None  # 部分隐藏API密钥
        }


def main():
    """示例用法"""
    # 从环境变量初始化
    llm = HelloAgentsLLM()

    # 显示配置
    config = llm.get_config()
    print("当前配置:", config)

    # 测试调用
    messages = [
        {"role": "user", "content": "请用中文回答：什么是人工智能？"}
    ]

    try:
        response = llm.think(messages, temperature=0.7, max_tokens=500)
        print("\n完整响应:")
        print("-" * 50)
        print(response)
        print("-" * 50)
    except Exception as e:
        print(f"测试失败: {e}")


if __name__ == "__main__":
    main()