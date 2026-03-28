from llm_client import HelloAgentsLLM
from typing import List, Dict, Any


# --- 模块 2: Reflection 智能体 ---
# 1. 初始执行提示词
INITIAL_PROMPT_TEMPLATE = """
你是一位资深的Python程序员。请根据以下要求，编写一个Python函数。
你的代码必须包含完整的函数签名、文档字符串，并遵循PEP 8编码规范。

要求: {task}

请直接输出代码，不要包含任何额外的解释。
"""

# 2. 反思提示词
REFLECT_PROMPT_TEMPLATE = """
你是一位极其严格的代码评审专家和资深算法工程师，对代码的性能有极致的要求。
你的任务是审查以下Python代码，并专注于找出其在**算法效率**上的主要瓶颈。

# 原始任务:
{task}

# 待审查的代码:
```python
{code}
```

请分析该代码的时间复杂度，并思考是否存在一种**算法上更优**的解决方案来显著提升性能。
如果存在，请清晰地指出当前算法的不足，并提出具体的、可行的改进算法建议（例如，使用筛法替代试除法）。
如果代码在算法层面已经达到最优，才能回答“无需改进”。

请直接输出你的反馈，不要包含任何额外的解释。
"""

# 3. 优化提示词
REFINE_PROMPT_TEMPLATE = """
你是一位资深的Python程序员。你正在根据一位代码评审专家的反馈来优化你的代码。

# 原始任务:
{task}

# 你上一轮尝试的代码:
{last_code_attempt}

# 评审员的反馈:
{feedback}

请根据评审员的反馈，生成一个优化后的新版本代码。
你的代码必须包含完整的函数签名、文档字符串，并遵循PEP 8编码规范。
请直接输出优化后的代码，不要包含任何额外的解释。
"""


class Memory:
    def __init__(self):
        self.records: List[Dict[str, Any]] = []

    def addRecord(self, record_type: str, content: str):
        self.records.append({"record_type": record_type, "content": content})
        print(f"已记录一条记录：{record_type}")

    def getLastExecution(self) -> str:
        for record in reversed(self.records):
            if record["record_type"] == "execution":
                return record["content"]
        return ""

class ReflectionAgent:
    def __init__(self, llm_client: HelloAgentsLLM, max_iteration: int = 3):
        self.llm_client = llm_client
        self.max_iteration = max_iteration
        self.memory = Memory()

    def run(self, task: str):
        print("进行初始执行...")
        initial_code = self._get_llm_response(INITIAL_PROMPT_TEMPLATE.format(task=task))
        self.memory.addRecord("execution", initial_code)
# 		for i in range(max..):
        for i in range(self.max_iteration):
            print(f"进行第 {i+1} 轮...")
            print("进行反思...")
# 			last_code
            last_code = self.memory.getLastExecution()
            feedback = self._get_llm_response(REFLECT_PROMPT_TEMPLATE.format(task=task, code=last_code))
            self.memory.addRecord("reflection", feedback)

            if "无需改进" in feedback or "no need for improvement" in feedback.lower():
                print("无需改进，任务完成")
                break
            print("进行优化...")
            new_code = self._get_llm_response(REFINE_PROMPT_TEMPLATE.format(task=task, last_code_attempt=last_code, feedback=feedback))
            self.memory.addRecord("execution", new_code)
        final_code = self.memory.getLastExecution()
        return f"{final_code}"


    def _get_llm_response(self, prompt: str):
        messages = [{"role": "user", "content": prompt}]
        return self.llm_client.think(messages)


if __name__ == '__main__':
    llm_client = HelloAgentsLLM()
    agent = ReflectionAgent(llm_client)
    task = "编写一个Python函数，找出1到n之间所有的素数 (prime numbers)。"
    result = agent.run(task)
    print(f"\n\n优化后的代码为：\n{result}")