import os
from dotenv import load_dotenv
from openai import OpenAI
from typing import List, Dict, Any

load_dotenv()

# class HelloAgentsLLM:
# 	def __init__(base_url: str = None, api_key, model, timeout):
# 		client
#
# 	def think(messages: List[Dict[str,Any]]) -> str:
# 		client.create
# 		for 流式打印，返回完整结果

class HelloAgentsLLM:
    def __init__(self, base_url: str = None, api_key: str = None, model: str = None, timeout: int = None):
        self.base_url = base_url or os.getenv("LLM_BASE_URL")
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.model = model or os.getenv("LLM_MODEL")
        self.timeout = timeout or int(os.getenv("LLM_TIMEOUT"))
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)

    def think(self, messages: List[Dict[str, Any]]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.5,
            stream=True
        )
        result_str = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                result_str += chunk.choices[0].delta.content
                print(chunk.choices[0].delta.content, end="", flush=True)

        print()
        return result_str

if __name__ == '__main__':
    llm_client = HelloAgentsLLM()
    question = '你是谁'
    messages = [{"role": "user", "content": question}]
    result = llm_client.think(messages)
    print(f"\n<<<最终完整结果:{result}>>>")