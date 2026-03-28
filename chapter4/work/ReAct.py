from llm_client import HelloAgentsLLM
from tools import search, ToolsExecutor
from dotenv import load_dotenv
import os
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


class ReActAgent:
    def __init__(self, llm_client: HelloAgentsLLM, tool_executor: ToolsExecutor, max_step: int = 6):
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.max_step = max_step

# 	def run(question: str) -> str:
    def run(self, question: str) -> str:
        history = []
        current_step = 0
        print(f"问题: {question}")
        while current_step < self.max_step:
            current_step += 1
            print(f"\n>>>第{current_step}/{self.max_step}轮...")
            tools = self.tool_executor.getAvailableTools()
            prompt = REACT_PROMPT_TEMPLATE.format(
                tools=tools,
                question=question,
                history="\n".join(history)
            )
            messages = [{"role": "user", "content": prompt}]
            response_text = self.llm_client.think(messages)
# 			提取thought action
            thought, action = self._parse_output(response_text)
            history.append(f"Thought: {thought}")
            history.append(f"Action: {action}")
# 			校验是否合法，判空
# 			thought Observation append continue
            if not thought:
                print("Thought无效，请检查模型输出")
                history.append("Observation: 无效的Thought")
                continue
            if not action:
                print("Action无效，请检查模型输出")
                history.append("Observation: 无效的Action")
                continue
# 			判断是否含有Finish print return  def _parse_input(action_str) -> str:
            if action.startswith("Finish"):
                finish_text = self._parse_input(action)
                print(f"\n Finish: {finish_text}")
                return finish_text
# 			提取tool_name, tool_input   def _parse_action(action_str):   返回tool_name,tool_input || None,None
            tool_name, tool_input = self._parse_action(action)
            if not tool_name:
                print("Action工具调用无效，请检查模型输出")
                history.append("Observation: Action工具调用无效，请检查模型输出")
                continue

            if tool_name not in self.tool_executor.tools:
                print(f"未找到工具：{tool_name}")
                history.append(f"Observation: 未找到工具：{tool_name}")
                continue

# 			判断是否有tool_name
            tool = self.tool_executor.getTool(tool_name)
            try:
                tool_output = tool(tool_input)
            except Exception as e:
                print(f"工具调用异常：{e}")
                history.append(f"Observation: 工具调用异常：{e}")
                continue
            history.append(f"Observation: 工具 {tool_name} 输出: {tool_output}")
            print(f"工具 {tool_name} 输出: {tool_output}")
        print("超出最大步骤，模型输出终止!")


    def _parse_output(self, response_text: str):
        """
        解析大模型的输出，提取Thought和Action部分。
        Thought从"Thought:"到"Action:"或末尾，Action从"Action:"到末尾。
        返回(thought, action)内容部分，如果没有找到则返回(None, None)
        """
        # 匹配 Thought: 或 Thought：（中文冒号）后面的内容，忽略大小写
        # 使用非贪婪匹配，直到 Action: 或字符串结束
        thought_match = re.search(r'Thought[:：]\s*(.*?)(?=\s*Action[:：]|$)', response_text, re.DOTALL | re.IGNORECASE)
        # 匹配 Action: 或 Action：（中文冒号）后面的内容，忽略大小写
        action_match = re.search(r'Action[:：]\s*(.*)', response_text, re.DOTALL | re.IGNORECASE)

        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None

        return thought, action

    def _parse_input(self, action_str: str) -> str:
        """
        提取Finish的内容
        :param action_str:
        :return: str
        """
        return re.search(r'Finish\[(.*)\]', action_str).group(1)

    def _parse_action(self, action_str: str):
        """
                解析Action内容，返回(tool_name, tool_input)
                如果没有找到则返回(None, None)
                格式示例: search[查询词] 或 Finish[最终答案]
                """
        import re

        # 匹配 tool_name[tool_input] 格式
        match = re.match(r"(\w+)\[(.*)\]", action_str, re.DOTALL)
        if match:
            tool_name = match.group(1).strip()
            tool_input = match.group(2).strip()
            return tool_name, tool_input
        else:
            return None, None


if __name__ == '__main__':
    llm_client = HelloAgentsLLM()
    tool_executor = ToolsExecutor()
    tool_executor.registerTool("search", "一个网页搜索工具，当你回答事实，时事，热点或搜索相关的内容时，调用此工具。", search)
    agent = ReActAgent(llm_client, tool_executor)
    agent.run("小米最新大模型咨询")