# FirstAgentTest

##  提示词

*  角色 指令 上下文 例子 输入 输出 严谨的执行顺序步骤。


```python
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

请开始吧！
"""
```



## 工具

> 工具使用AI编写即可.

def get_weather(city: str) -> str: 查询天气工具  wttr.in
def get_attraction(city: str, weather: str) -> str: 
"""
根据城市和天气，使用Tavily Search API搜索并返回优化后的景点推荐。
"""

langchainchatmodel

for 循环
LLM思考
多余的Thought-Action需要截断

加入历史，并输出

校验是否有Action，

*  noAction 不合法，Observation： ....  加入历史，输出，continue.

*  Finish  输出，break

* Functionname   正则匹配工具名称，参数 Action Observation  

* Function 格式异常，没有对应工具，调用工具出错， Observation, 加入历史，输出，continue.

 ## 总结

Thought -- Action -- Observation 循环