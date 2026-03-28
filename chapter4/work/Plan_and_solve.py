from llm_client import HelloAgentsLLM
from typing import List, Dict, Any
import ast


# --- 2. 规划器 (Planner) 定义 ---
PLANNER_PROMPT_TEMPLATE = """
你是一个顶级的AI规划专家。你的任务是将用户提出的复杂问题分解成一个由多个简单步骤组成的行动计划。
请确保计划中的每个步骤都是一个独立的、可执行的子任务，并且严格按照逻辑顺序排列。
你的输出必须是一个Python列表，其中每个元素都是一个描述子任务的字符串。

问题: {question}

请严格按照以下格式输出你的计划，```python与```作为前后缀是必要的:
```python
["步骤1", "步骤2", "步骤3", ...]
```
"""


# --- 3. 执行器 (Executor) 定义 ---
EXECUTOR_PROMPT_TEMPLATE = """
你是一位顶级的AI执行专家。你的任务是严格按照给定的计划，一步步地解决问题。
你将收到原始问题、完整的计划、以及到目前为止已经完成的步骤和结果。
请你专注于解决“当前步骤”，并仅输出该步骤的最终答案，不要输出任何额外的解释或对话。

# 原始问题:
{question}

# 完整计划:
{plan}

# 历史步骤与结果:
{history}

# 当前步骤:
{current_step}

请仅输出针对“当前步骤”的回答:
"""


class Planner:
    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client

    def plan(self, task: str) -> List[str]:
        prompt = PLANNER_PROMPT_TEMPLATE.format(question=task)
        messages = [{"role": "user", "content": prompt}]
        result = self.llm_client.think(messages)
        result = result.split('```python')[1].split('```')[0].strip()
        plan = ast.literal_eval(result)
        return plan if isinstance(plan, list) else []


class Executor:
    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client

    def execute(self, question: str, plan: List[str]):
        history = ""
        for i, step in enumerate(plan, 1):
            print(f"正在执行步骤{i}: {step}")
            prompt = EXECUTOR_PROMPT_TEMPLATE.format(
                question=question,
                plan=plan,
                history=history if history else "无",
                current_step=step
            )
            messages = [{"role": "user", "content": prompt}]
            result = self.llm_client.think(messages)
            history += f"步骤{i}: {step}\n结果为: {result}\n\n"
            print(f"步骤{i}的答案为: {result}")


class PlanAndSolveAgent:
    def __init__(self, llm_client: HelloAgentsLLM):
        self.planner = Planner(llm_client)
        self.executor = Executor(llm_client)
        self.llm_client = llm_client

    def run(self, question: str):
        plan = self.planner.plan(question)
        if not plan:
            print("无法生成有效的计划，请重新提问。")
            return
        self.executor.execute(question, plan)

if __name__ == '__main__':
    llm_client = HelloAgentsLLM()
    agent = PlanAndSolveAgent(llm_client)
    agent.run("一个水果店周一卖出了15个苹果。周二卖出的苹果数量是周一的两倍。周三卖出的数量比周二少了5个。请问这三天总共卖出了多少个苹果？")