# tools.py
# 	def search(query: str) -> str:
# 	"""
#   一个基于SerpApi的实战网页搜索引擎工具。
#   它会智能地解析搜索结果，优先返回直接答案或知识图谱信息。
#   """
from serpapi import SerpApiClient
from dotenv import load_dotenv
from typing import Dict, List, Any
import os

load_dotenv()


def search(query: str) -> str:
    """
    一个基于SerpApi的实战网页搜索引擎工具。
    它会智能地解析搜索结果，优先返回直接答案或知识图谱信息。
    """
    # print(f"🔍 正在执行 [SerpApi] 网页搜索: {query}")
    try:
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return "错误：SERPAPI_API_KEY 未在 .env 文件中配置。"

        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "gl": "cn",  # 国家代码
            "hl": "zh-cn",  # 语言代码
        }

        client = SerpApiClient(params)
        results = client.get_dict()

        # 智能解析：优先寻找最直接的答案
        if "answer_box_list" in results:
            return "\n".join(results["answer_box_list"])
        if "answer_box" in results and "answer" in results["answer_box"]:
            return results["answer_box"]["answer"]
        if "knowledge_graph" in results and "description" in results["knowledge_graph"]:
            return results["knowledge_graph"]["description"]
        if "organic_results" in results and results["organic_results"]:
            # 如果没有直接答案，则返回前三个有机结果的摘要
            snippets = [
                f"[{i + 1}] {res.get('title', '')}\n{res.get('snippet', '')}"
                for i, res in enumerate(results["organic_results"][:3])
            ]
            return "\n\n".join(snippets)

        return f"对不起，没有找到关于 '{query}' 的信息。"

    except Exception as e:
        return f"搜索时发生错误: {e}"

#   class ToolExecutor:
#   """
#   一个工具执行器，负责管理和执行工具。
#   """
#   def init:
#   tools: Dict[str,Dict[str,Any]]
class ToolExecutor:
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}

#   def registerTool(name: str, description: str, func: callable):
#   """
#   向工具箱中注册一个新工具。
#   """
#   检查name是否在tools,覆盖，注册
    def registerTool(self, name: str, description: str, func: callable):
        if name in self.tools:
            print(f"工具 {name} 已存在，已覆盖")
        self.tools[name] = {
            "description": description,
            "func": func
        }

#   def getTool(name: str) -> callable:
#   """
#   根据名称获取一个工具的执行函数
#   """
    def getTool(self, name: str) -> callable:
        return self.tools[name]["func"]

#   def getAvailableTools() -> str:
#   """
#   获得所有可用工具的格式化描述字符串
#   """
    def getAvailableTools(self) -> str:
        descriptions = [f"{name}: {tool['description']}" for name, tool in self.tools.items()]
        return "\n".join(descriptions)

if __name__ == '__main__':
    # print(search("英伟达最新的GPU型号是什么"))
    tool_executor = ToolExecutor()
    tool_executor.registerTool("search", "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。", search)
    print(tool_executor.getAvailableTools())
    print(tool_executor.getTool("search")("英伟达最新的GPU型号是什么"))