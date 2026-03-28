# ReAct.py
from llm_client import HelloAgentsLLM
from tools import search, ToolExecutor
import re

REACT_PROMPT_TEMPLATE = """
请注意，你是一个有能力调用外部工具的智能助手。

可用工具如下：
{tools}

请严格按照以下格式进行回应：

Thought: 你的思考过程，用于分析问题、拆解任务和规划下一步行动。
Action: 你决定采取的行动，必须是以下格式之一：
- `{{tool_name}}[{{tool_input}}]`：调用一个可用工具。
- `Finish[最终答案]`：当你认为已经获得最终答案时。
- 当你收集到足够的信息，能够回答用户的最终问题时，你必须在`Action:`字段后使用 `Finish[最终答案]` 来输出最终答案。


现在，请开始解决以下问题：
Question: {question}
History: {history}
"""


# class ReActAgent:
#     def __init__(llm_client:, tool_executor:, max_steps:):
#
#     def run(question: str):
#         循环
class ReActAgent:
    def __init__(self, llm_client: HelloAgentsLLM, tool_executor: ToolExecutor, max_steps: int = 6):
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.max_steps = max_steps
        self.history = []

    def run(self, question: str):
        print(f"问题: {question}")
        current_step = 0
        while current_step < self.max_steps:
            current_step += 1
            print(f"轮次 ----第{current_step}次----")
#     prompt
            tools_text = self.tool_executor.getAvailableTools()
            history_text = "\n".join(self.history)
            prompt = REACT_PROMPT_TEMPLATE.format(
                tools=tools_text,
                question=question,
                history=history_text
            )
#     messages
            messages = [{"role": "user", "content": prompt}]
#     llm_client.think
            response_text = self.llm_client.think(messages)
#     解析response_text
            thought, action = self._parse_output(response_text)
            self.history.append(f"\nThought: {thought}\n")
            self.history.append(f"\nAction: {action}\n")
#     判空
#     Observation
            if thought:
                print(f"Thought: {thought}")
            else:
                print("没有找到有效的Thought")
                self.history.append("\nObservation: 无法找到有效的Thought\n")
                continue
            if not action:
                print("没有找到有效的Action")
                self.history.append("\nObservation: 无法找到有效的Action\n")
                continue
            print(f"Action: {action}")
#     Finish
            # 判断是否含有Finish
            if action.startswith("Finish"):
                finish_text = self._parse_action_input(action)
                print(f"Finish: {finish_text}")
                return

#     Action: tool_name, tool_input _parse_action
            tool_name, tool_input = self._parse_action(action)
#     判空
            if not tool_name:
                print("Action无效,请严格按照提示词输出")
                self.history.append("\nObservation: Action无效,请严格按照提示词输出\n")
                continue

#     Observation
#     not in tools
            if tool_name not in self.tool_executor.tools:
                print(f"没有工具 {tool_name}")
                self.history.append(f"\nObservation: 没有工具 {tool_name}\n")
                continue
#     Observation
#     执行
            tool = self.tool_executor.getTool(tool_name)
            try:
                tool_output = tool(tool_input)
                print(f"工具 {tool_name} 输出: {tool_output}")
                self.history.append(f"\nObservation: 工具 {tool_name} 输出: {tool_output}\n")
            except Exception as e:
                print(f"工具 {tool_name} 执行错误: {e}")
                self.history.append(f"\nObservation: 工具 {tool_name} 执行错误: {e}\n")
        print("超出最大次数,终止")



    def _parse_output(self, text: str):
        """
        解析大模型返回的结果，提取Thought和Action部分。
        返回 (thought, action)，如果没有找到则返回 (None, None)
        """
        import re

        # 匹配 Thought: 或 Thought：（中文冒号）后面的内容，忽略大小写
        # 使用非贪婪匹配，直到 Action: 或字符串结束
        thought_match = re.search(r'Thought[:：]\s*(.*?)(?=\s*Action[:：]|$)', text, re.DOTALL | re.IGNORECASE)
        # 匹配 Action: 或 Action：（中文冒号）后面的内容，忽略大小写
        action_match = re.search(r'Action[:：]\s*(.*)', text, re.DOTALL | re.IGNORECASE)

        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None

        return thought, action

#     def _parse_action_input(action_text: str):
    def _parse_action_input(self, action_text: str):
        # 解析Action,返回Finish 的内容
        match = re.match(r"\w+\[(.*)\]", action_text, re.DOTALL)
        return match.group(1) if match else ""

    def _parse_action(self, action_text: str):
        """
        解析Action内容，返回(tool_name, tool_input)
        如果没有找到则返回(None, None)
        格式示例: search[查询词] 或 Finish[最终答案]
        """
        import re

        # 匹配 tool_name[tool_input] 格式
        match = re.match(r"(\w+)\[(.*)\]", action_text, re.DOTALL)
        if match:
            tool_name = match.group(1).strip()
            tool_input = match.group(2).strip()
            return tool_name, tool_input
        else:
            return None, None


if __name__ == '__main__':
    llm_client = HelloAgentsLLM()
    tool_executor = ToolExecutor()
    tool_executor.registerTool("search", "网页搜索引擎，当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。", search)
    # print(tool_executor.getAvailableTools())
    agent = ReActAgent(llm_client, tool_executor)
    agent.run("英伟达最新的GPU型号是什么")