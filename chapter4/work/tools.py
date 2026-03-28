from dotenv import load_dotenv
import os
from typing import List, Dict, Any

load_dotenv()
# def search(question: str) -> str:
# 	一个网页搜索工具，当你回答事实，实事，热点或搜索相关的内容时，调用此工具。
def search(question: str) -> str:
    """
    一个网页搜索工具，当你回答事实，时事，热点或搜索相关的内容时，调用此工具。
    :param question:
    :return: str
    """
    import requests
    import json

    # 从环境变量获取百度API密钥
    api_key = os.getenv("BAIDU_API_KEY")
    if not api_key:
        return "错误：未找到BAIDU_API_KEY环境变量。请检查.env文件。"

    url = "https://qianfan.baidubce.com/v2/ai_search/web_search"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # 构建请求体，参考官方文档
    payload = {
        "messages": [
            {
                "content": question,
                "role": "user"
            }
        ],
        "resource_type_filter": [
            {
                "type": "web",
                "top_k": 3  # 减少数量以加快响应
            }
        ],
        "edition": "standard",
        "search_filter": {
            "match": {
                "site": []
            },
            "range": {
                "page_time": {
                    "gte": "",
                    "lte": ""
                }
            }
        },
        "search_recency_filter": "noTimeLimit"
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()  # 检查HTTP错误

        data = response.json()

        # 解析响应
        if "references" not in data:
            return "未找到相关搜索结果。"

        references = data["references"]
        if not references:
            return "未找到相关搜索结果。"

        # 格式化结果
        results = []
        for ref in references[:5]:  # 限制前5个结果
            title = ref.get("title", "无标题")
            content = ref.get("content", "无内容")
            url = ref.get("url", "")
            date = ref.get("date", "")

            # 清理内容中的特殊字符
            content = content.replace("\u0004", "").replace("\u0005", "").strip()

            result = f"标题: {title}\n内容: {content[:200]}..." if len(content) > 200 else f"标题: {title}\n内容: {content}"
            if url:
                result += f"\n链接: {url}"
            if date:
                result += f"\n日期: {date}"
            results.append(result)

        return f"找到 {len(references)} 个搜索结果:\n\n" + "\n\n".join(results)

    except requests.exceptions.Timeout:
        return "请求超时，请稍后重试。"
    except requests.exceptions.ConnectionError:
        return "网络连接错误，请检查网络设置。"
    except requests.exceptions.HTTPError as e:
        return f"HTTP错误: {e}"
    except json.JSONDecodeError:
        return "响应解析错误，返回格式无效。"
    except Exception as e:
        return f"未知错误: {str(e)}"


# class ToolsExecutor:
# 	def __init__():
# 		tools: Dict[Dict[str,Any]] = {}
#
# 	def registerTool(name, description, func: callable):
# 		覆盖
#
# 	def getAvailableTools() -> str:
# 		name: description
#
# 	def getTool(name: str) -> callable:

class ToolsExecutor:
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}

    def registerTool(self, name: str, description: str, func: callable):
        if name in self.tools:
            print(f"工具 {name} 已存在，已覆盖")
        self.tools[name] = {
            "description": description,
            "func": func
        }

    def getAvailableTools(self) -> str:
        return "\n".join([f"{name}: {info['description']}" for name, info in self.tools.items()])

    def getTool(self, name: str) -> callable:
        return self.tools[name]["func"]

if __name__ == '__main__':
    # result= search('小米公司最新大模型咨询')
    # print(result)
    tool_executor = ToolsExecutor()
    tool_executor.registerTool("search", "一个网页搜索工具，当你回答事实，时事，热点或搜索相关的内容时，调用此工具。", search)
    print(tool_executor.getAvailableTools())
    print(tool_executor.getTool("search")('小米公司最新大模型咨询'))