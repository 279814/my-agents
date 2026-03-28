import os
from llm_client import HelloAgentsLLM
from dotenv import load_dotenv
import ast
from typing import List


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


# load_dotenv()
load_dotenv()
#
# class Planner:
# 	def __init__(llm_client):
#
# 	def plan(question) -> :
# 		prompt
# 		llm_client.think
# 		除去```python ``` /n
# 		plan = ast.literal_eval(plan_str)
# 		判断是否已经转成list, else []
# 		except e, []
class Planner:
    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client

    def plan(self, question: str) -> List[str]:
        prompt = PLANNER_PROMPT_TEMPLATE.format(question=question)
        messages = [{"role": "user", "content": prompt}]
        plan_str = self.llm_client.think(messages)
        try:
            plan_str = plan_str.split('```python')[1].split('```')[0].strip()
            plan = ast.literal_eval(plan_str)
            # 判断是否已经转成list, else []
            return plan if isinstance(plan, list) else []
        except Exception as e:
            print(f"无法解析计划: {e}")
            return []


# class Executor:
# 	def __init__(llm_client):
#
# 	def execute(question: str, plan: list[str]) -> str:
# 		history
# 		enumerate(plan)
# 		print
# 		prompt  history else '无'
# 		messages
# 		think
# 		history += f"步骤{}: {}\n结果： {}\n\n"
# 		print
class Executor:
    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client

    def execute(self, question: str, plan: List[str]) -> str:
        history = ""
        final_answer = ""
        for i, step in enumerate(plan, 1):
            print(f"\n >>--步骤{i}/{len(plan)}: {step}")
            prompt = EXECUTOR_PROMPT_TEMPLATE.format(
                question=question,
                plan=plan,
                history=history if history else "无",
                current_step=step
            )
            messages = [{"role": "user", "content": prompt}]
            result = self.llm_client.think(messages)
            history += f"步骤{i}: {step}\n结果： {result}\n\n"
            final_answer = result
            print(f"步骤{i}的答案： {final_answer}")
        return final_answer

# class PlanAndSolveAgent:
# 	def __init__(llm_client):
#
# 	def run(question: str):
# 		begin
# 		plan
# 		判空 return
# 		solve
# 		end
class PlanAndSolveAgent:
    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client
        self.planner = Planner(llm_client)
        self.executor = Executor(llm_client)

    def run(self, question: str):
        print("开始进行任务规划...")
        plan = self.planner.plan(question)
        print(f"生成的计划为：{plan}")
        if not plan:
            print("无法生成有效的计划，请重新提问。")
            return
        result = self.executor.execute(question, plan)
        print(f"任务完成，结果为：{result}")


if __name__ == '__main__':
    try:
        llm_client = HelloAgentsLLM()
        agent = PlanAndSolveAgent(llm_client)
        question = "一个水果店周一卖出了15个苹果。周二卖出的苹果数量是周一的两倍。周三卖出的数量比周二少了5个。请问这三天总共卖出了多少个苹果？"
        agent.run(question)
    except ValueError as e:
        print(e)