AGENT_SYSTEM_PROMPT = """
你是一个智能旅行助手。你的任务是分析用户的请求，并使用可用工具一步步地解决问题。

# 可用工具:
- `get_weather(city: str)`: 查询指定城市的实时天气。
- `get_attraction(city: str, weather: str)`: 根据城市和天气搜索推荐的旅游景点。

# 输出格式要求:
你的每次回复必须严格遵循以下格式，包含一对Thought和Action：

Thought: [你的思考过程和下一步计划]
Action: [你要执行的具体行动]

Action的格式必须是以下之一：
1. 调用工具：function_name(arg_name="arg_value")
2. 结束任务：Finish[最终答案]

# 重要提示:
- 每次只输出一对Thought-Action
- Action必须在同一行，不要换行
- 当收集到足够信息可以回答用户问题时，必须使用 Action: Finish[最终答案] 格式结束
- 以简体中文进行交互

请开始吧！
"""
import requests
import os



def get_weather(city: str) -> str:
    """
    查询指定城市的实时天气。
    使用 wttr.in 服务，返回格式化的天气信息。
    """
    url = f"https://wttr.in/{city}?format=j1"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # 检查HTTP状态码
        data = response.json()

        # 解析JSON结构
        current_condition = data['data']['current_condition'][0]
        weather_desc = current_condition['weatherDesc'][0]['value']
        temp_c = current_condition['temp_C']

        return f"{city}当前天气：{weather_desc}，气温{temp_c}摄氏度"
    except requests.exceptions.RequestException as e:
        return f"错误: 无法获取{city}的天气信息 - {e}"
    except (KeyError, IndexError) as e:
        return f"错误: 解析{city}的天气数据时出错 - 数据格式异常"
    except Exception as e:
        return f"错误: 获取{city}天气时发生未知错误 - {e}"

def get_attraction(city: str, weather: str) -> str:
    """
    根据城市和天气，使用Tavily Search API搜索并返回优化后的景点推荐。
    """
    api_key = os.environ.get('TAVILY_API_KEY')
    if not api_key:
        return f"错误: 未设置TAVILY_API_KEY环境变量"

    # 构造搜索查询
    query = f"{city} tourist attractions best to visit in {weather} weather"
    url = "https://api.tavily.com/search"

    try:
        # 准备请求数据
        data = {
            "api_key": api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": 5
        }

        response = requests.post(url, json=data, timeout=15)
        response.raise_for_status()  # 检查HTTP状态码

        result_data = response.json()

        # 检查是否有结果
        if 'results' not in result_data or not result_data['results']:
            return f"未找到{city}在{weather}天气下的景点推荐"

        # 格式化结果
        results = result_data['results']
        recommendations = []

        for i, item in enumerate(results[:5], 1):
            title = item.get('title', '无标题')
            content = item.get('content', '无描述')
            # 截取前100个字符作为简要描述
            snippet = content[:100] + "..." if len(content) > 100 else content
            recommendations.append(f"{i}. {title}: {snippet}")

        result_str = "\n".join(recommendations)
        return f"{city}在{weather}天气下的景点推荐:\n{result_str}"

    except requests.exceptions.RequestException as e:
        return f"错误: 无法获取{city}的景点推荐 - 网络错误: {e}"
    except (KeyError, ValueError) as e:
        return f"错误: 解析{city}的景点数据时出错 - 数据格式异常: {e}"
    except Exception as e:
        return f"错误: 获取{city}景点推荐时发生未知错误 - {e}"

# 加入tools
tools = {
    "get_weather": get_weather,
    "get_attraction": get_attraction
}

# langchainchatmodel
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

user_prompt = "你好，请帮我查询一下今天北京的天气，然后根据天气推荐一个合适的旅游景点。"
history_prompt = [f"user_prompt:{user_prompt}"]
model = ChatTongyi(model="qwen3-max")
prompt_text = ChatPromptTemplate.from_messages(
    [
        ("system", AGENT_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="history")
    ]
)
chain = prompt_text | model | StrOutputParser()

import re

print(f"user-input: {user_prompt}")
# for 循环
for i in range(5):
    print(f"这是第{i+1}轮循环")
    # LLM思考
    res = chain.invoke({"history": history_prompt})

    # 多余的Thought-Action需要截断,如有截断打印
    # 使用正则匹配所有的 Thought 和 Action 对
    thought_action_pattern = r'Thought:\s*(.*?)\nAction:\s*(.*?)(?=\nThought:|$)'
    matches = re.findall(thought_action_pattern, res, re.DOTALL)
    if len(matches) > 1:
        print("已完成截断")
        # 重新构造只包含第一对 Thought-Action 的回复
        first_thought = matches[0][0].strip()
        first_action = matches[0][1].strip()
        res = f"Thought: {first_thought}\nAction: {first_action}"
        #打印一下Thought-Action  and  append history
    print(res)
    history_prompt.append(res)

#如果没有Action,Observation返回"错误: 未能解析到 Action 字段。请确保你的回复严格遵循 'Thought: ... Action: ...' 的格式。"  append history   Observation:f""
    # 先提取 Action 内容
    action_match = re.search(r'Action:\s*(.+)', res, re.DOTALL)
    if not action_match:
        # 如果没有 Action,Observation 返回错误信息
        observation = "错误：未能解析到 Action 字段。请确保你的回复严格遵循 'Thought: ... Action: ...' 的格式。"
        history_prompt.append(f"user: {observation}")
        print(observation)
        continue

    action_content = action_match.group(1).strip()

    # 检查是否是 Finish 动作 - 必须在 Action 行
    finish_match = re.match(r'^Finish\[(.*?)\]$', action_content, re.DOTALL)
    if finish_match:
        # 任务结束，输出最终答案
        final_answer = finish_match.group(1)
        print(f"最终答案：{final_answer}")
        break

    # 正则匹配工具名称，参数
    # 解析工具调用格式：function_name(arg_name="arg_value")
    tool_match = re.match(r'^(\w+)\((.*)\)$', action_content)
    if not tool_match:
        observation = "错误: Action格式不正确，应为 function_name(arg_name=\"arg_value\") 格式"
        history_prompt.append(f"user: {observation}")
        print(observation)
        continue

    tool_name = tool_match.group(1)
    args_str = tool_match.group(2)

    # 校验工具是否存在
    if tool_name not in tools:
        observation = f"错误：未定义的工具 '{tool_name}'"
        history_prompt.append(f"user: {observation}")
        print(observation)
        continue

    # 解析参数并执行工具
    # 解析参数格式：arg_name="arg_value"
    args = {}
    if args_str:
        # 匹配 key="value" 对
        arg_pattern = r'(\w+)=("[^"]*"|\'[^\']*\')'
        arg_matches = re.findall(arg_pattern, args_str)
        for key, value in arg_matches:
            # 去除引号
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            args[key] = value

    # Action - 执行工具
    try:
        tool_func = tools[tool_name]
        if args:
            result = tool_func(**args)
        else:
            result = tool_func()
    except Exception as e:
        result = f"错误: 执行工具 {tool_name} 时发生异常: {e}"

    # Observation - 添加观察结果到历史记录
    observation = f"Observation: {result}"
    history_prompt.append(f"user: {observation}")
    print(observation)


def test_get_weather():
    # 测试 get_weather 函数
    test_cities = ["北京", "上海", "New York"]
    for city in test_cities:
        result = get_weather(city)
        print(result)


def test_get_attraction():
    # 测试 get_attraction 函数
    api_key = os.environ.get('TAVILY_API_KEY')
    if not api_key:
        print("警告: 未设置TAVILY_API_KEY环境变量，跳过景点推荐测试")
        print("请设置环境变量: export TAVILY_API_KEY=your_api_key")
        return

    # 测试数据
    test_cases = [
        ("北京", "Sunny"),
        ("上海", "Partly cloudy"),
        ("New York", "Overcast")
    ]

    for city, weather in test_cases:
        print(f"\n测试 {city} 在 {weather} 天气下的景点推荐:")
        result = get_attraction(city, weather)
        print(result)

def test_model():
    print(model.invoke("你是谁").content)



# if __name__ == '__main__':
#     # test_get_weather()
#     # test_get_attraction()
#     # test_model()
#     pass