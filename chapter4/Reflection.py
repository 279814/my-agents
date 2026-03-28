from typing import List, Dict, Any
from llm_client import HelloAgentsLLM


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


# class Memory:
# 	一个简单的短期记忆模块，用于存储智能体的行动与反思轨迹
# 	def __init__():
# 		records: List[Dict[str, Any]]
#
# 	def add_record(record_type: str, content: str):
# 		向记忆中添加一条新记录。
#         参数:
#         - record_type (str): 记录的类型 ('execution' 或 'reflection')。
#         - content (str): 记录的具体内容 (例如，生成的代码或反思的反馈)。
#         append print
#
#     def get_trajectory() -> str:
#     	将所有记忆记录格式化为一个连贯的字符串文本，用于构建提示词。
#     	trajectory = ""
#     	return
#
#     def get_last_execution() -> str:
#     	获取最近一次的执行结果
#     	reversed() None

class Memory:
    """
    一个简单的短期记忆模块，用于存储智能体的行动与反思轨迹
    """
    def __init__(self):
        self.records: List[Dict[str, Any]] = []

    def add_record(self, record_type: str, content: str):
        """
        向记忆中添加一条新记录。
        参数:
         - record_type (str): 记录的类型 ('execution' 或 'reflection')。
         - content (str): 记录的具体内容 (例如，生成的代码或反思的反馈)。
        """
        self.records.append({"type": record_type, "content": content})
        print(f"\n---已添加一条{record_type}记录----")

    def get_trajectory(self) -> str:
        """
        将所有记忆记录格式化为一个连贯的字符串文本，用于构建提示词。
        """
        trajectory = ""
        for record in self.records:
            if record["type"] == "execution":
                trajectory += f"---上一轮尝试(代码):\n---结果:{record['content']}\n\n"
            elif record["type"] == "reflection":
                trajectory += f"---评审员反馈:\n---结果:{record['content']}\n\n"
        return trajectory

    def get_last_execution(self) -> str:
        """
        获取最近一次的执行结果
        """
        reversed_records = reversed(self.records)
        for record in reversed_records:
            if record["type"] == "execution":
                return record["content"]
        return ''


class ReflectionAgent:
    def __init__(self, llm_client: HelloAgentsLLM, max_iterations: int = 3):
        self.llm_client = llm_client
        self.max_iterations = max_iterations
        self.memory = Memory()

# 	def run(task: str):
# 		begin --- task
# 		初始执行
# 		initial_prompt
# 		initial_code = _get_llm_response()
# 		add_record
    def run(self, task: str):
        print(f"\n任务开始======{task}")
        print("开始进行初始执行...")
        initial_prompt = INITIAL_PROMPT_TEMPLATE.format(task=task)
        initial_code = self._get_llm_response(initial_prompt)
        self.memory.add_record("execution", initial_code)
# 		for
# 		print
# 		反思
# 		last_code
# 		reflect_prompt
# 		feedback
# 		add_record
        for i in range(self.max_iterations):
            print(f"\n进行第{i + 1}/{self.max_iterations}轮反思...")
            print("正在进行反思...")
            last_code = self.memory.get_last_execution()
            reflect_prompt = REFLECT_PROMPT_TEMPLATE.format(task=task, code=last_code)
            feedback = self._get_llm_response(reflect_prompt)
            self.memory.add_record("reflection", feedback)
# 		校验是否停止
            if "无需改进" in feedback or "no need for improvement" in feedback.lower():
                print("无需改进，停止反思。")
                break

# 		优化
# 		print
# 		refine_prompt
# 		refined_code =
# 		add_record
            print("正在进行优化...")
            refine_prompt = REFINE_PROMPT_TEMPLATE.format(task=task, last_code_attempt=last_code, feedback=feedback)
            refined_code = self._get_llm_response(refine_prompt)
            self.memory.add_record("execution", refined_code)
# 	final_code
        final_code = self.memory.get_last_execution()
        print(f"\n最终代码：\n{final_code}")
        print(f"任务结束======")
        print('*' * 50)
        print(self.memory.get_trajectory())
        return final_code


    def _get_llm_response(self, prompt: str):
        messages = [{"role": "user", "content": prompt}]
        response_text = self.llm_client.think(messages)
        return response_text

if __name__ == '__main__':
    llm_client = HelloAgentsLLM()
    reflection_agent = ReflectionAgent(llm_client)
    task = "编写一个Python函数，找出1到n之间所有的素数 (prime numbers)。"
    reflection_agent.run(task)
