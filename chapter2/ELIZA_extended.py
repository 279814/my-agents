import re
import random
from datetime import datetime

# 扩展规则库
rules = {
    r'I need (.*)': [
        "Why do you need {0}?",
        "Would it really help you to get {0}?",
        "Are you sure you need {0}?"
    ],
    r'Why don\'t you (.*)\?': [
        "Do you really think I don't {0}?",
        "Perhaps eventually I will {0}.",
        "Do you really want me to {0}?"
    ],
    r'Why can\'t I (.*)\?': [
        "Do you think you should be able to {0}?",
        "If you could {0}, what would you do?",
        "I don't know -- why can't you {0}?"
    ],
    r'I am (.*)': [
        "Did you come to me because you are {0}?",
        "How long have you been {0}?",
        "How do you feel about being {0}?"
    ],
    # 新规则1：谈论工作
    r'I work as (.*)|My job is (.*)|I am a (.*)': [
        "How do you feel about being a {0}?",
        "What do you enjoy most about your work as a {0}?",
        "How long have you been working as a {0}?"
    ],
    # 新规则2：谈论学习
    r'I study (.*)|I am studying (.*)|I am learning (.*)': [
        "Why did you choose to study {0}?",
        "What do you find most challenging about learning {0}?",
        "How do you plan to use your knowledge of {0} in the future?"
    ],
    # 新规则3：谈论爱好
    r'I like (.*)|I enjoy (.*)|My hobby is (.*)': [
        "What do you enjoy about {0}?",
        "How did you become interested in {0}?",
        "How often do you get to do {0}?"
    ],
    # 新规则4：谈论家庭
    r'my (.*) (wife|husband|child|son|daughter|parent)': [
        "Tell me more about your {1}.",
        "How does your {1} make you feel?",
        "What is your relationship like with your {1}?"
    ],
    # 新规则5：询问ELIZA
    r'Are you (.*)\?|Can you (.*)\?|Do you (.*)\?': [
        "Why do you ask if I {0}?",
        "Does it matter whether I {0}?",
        "What do you think about whether I {0}?"
    ],
    r'.* mother .*': [
        "Tell me more about your mother.",
        "What was your relationship with your mother like?",
        "How do you feel about your mother?"
    ],
    r'.* father .*': [
        "Tell me more about your father.",
        "How did your father make you feel?",
        "What has your father taught you?"
    ],
    r'.*': [
        "Please tell me more.",
        "Let's change focus a bit... Tell me about your family.",
        "Can you elaborate on that?"
    ]
}

# 代词转换规则（保持不变）
pronoun_swap = {
    "i": "you", "you": "i", "me": "you", "my": "your",
    "am": "are", "are": "am", "was": "were", "i'd": "you would",
    "i've": "you have", "i'll": "you will", "yours": "mine",
    "mine": "yours"
}

# 上下文记忆系统
class ElizaMemory:
    def __init__(self):
        self.memory = {
            'name': None,
            'age': None,
            'job': None,
            'hobbies': [],
            'family': {},
            'mentioned_topics': []
        }
        self.conversation_history = []

    def extract_info(self, user_input):
        """从用户输入中提取关键信息"""
        # 提取姓名
        name_patterns = [
            r'my name is (\w+)',
            r'I am called (\w+)',
            r'call me (\w+)'
        ]
        for pattern in name_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match and not self.memory['name']:
                self.memory['name'] = match.group(1)
                self.memory['mentioned_topics'].append('name')

        # 提取年龄
        age_patterns = [
            r'I am (\d+) years old',
            r'I\'m (\d+)',
            r'age (\d+)'
        ]
        for pattern in age_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match and not self.memory['age']:
                self.memory['age'] = match.group(1)
                self.memory['mentioned_topics'].append('age')

        # 提取工作信息（已通过规则处理）
        # 记录提到的话题
        topics = ['work', 'job', 'study', 'learn', 'hobby', 'family', 'mother', 'father']
        for topic in topics:
            if topic in user_input.lower() and topic not in self.memory['mentioned_topics']:
                self.memory['mentioned_topics'].append(topic)

    def get_personalized_response(self, base_response):
        """基于记忆个性化响应"""
        personalized = base_response

        # 如果知道姓名，在响应中提及
        if self.memory['name']:
            if random.random() < 0.3:  # 30%概率提及姓名
                personalized = f"{self.memory['name']}, {personalized.lower()}"

        # 如果知道年龄，在适当时候提及
        if self.memory['age'] and 'age' in self.memory['mentioned_topics']:
            if random.random() < 0.2:
                age_comment = f" By the way, at {self.memory['age']} years old, "
                personalized = personalized.replace(". ", age_comment)

        # 如果知道工作，在适当时候提及
        if self.memory['job'] and 'work' in self.memory['mentioned_topics']:
            if random.random() < 0.2:
                job_comment = f" As a {self.memory['job']}, "
                personalized = personalized.replace(". ", job_comment)

        return personalized

    def add_to_history(self, user_input, response):
        """添加对话到历史"""
        self.conversation_history.append({
            'time': datetime.now().strftime("%H:%M:%S"),
            'user': user_input,
            'eliza': response
        })

        # 保持历史长度
        if len(self.conversation_history) > 10:
            self.conversation_history.pop(0)

# 初始化记忆系统
memory = ElizaMemory()

def swap_pronouns(phrase):
    """对输入短语中的代词进行第一/第二人称转换"""
    words = phrase.lower().split()
    swapped_words = [pronoun_swap.get(word, word) for word in words]
    return " ".join(swapped_words)

def respond(user_input):
    """根据规则库生成响应，结合上下文记忆"""
    # 更新记忆
    memory.extract_info(user_input)

    for pattern, responses in rules.items():
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            # 捕获匹配到的部分
            captured_group = match.group(1) if match.groups() else ''
            # 进行代词转换
            swapped_group = swap_pronouns(captured_group)
            # 从模板中随机选择一个并格式化
            base_response = random.choice(responses).format(swapped_group)
            # 个性化响应
            final_response = memory.get_personalized_response(base_response)

            # 特殊处理：如果用户提到工作，更新记忆
            if 'work' in user_input.lower() or 'job' in user_input.lower():
                job_match = re.search(r'work as (.*?)(\.|$)|job is (.*?)(\.|$)|am a (.*?)(\.|$)',
                                     user_input, re.IGNORECASE)
                if job_match:
                    # 提取工作信息（从不同的捕获组）
                    for i in [1, 3, 5]:
                        if job_match.group(i) and not memory.memory['job']:
                            memory.memory['job'] = job_match.group(i)
                            break

            return final_response

    # 如果没有匹配任何特定规则，使用最后的通配符规则
    base_response = random.choice(rules[r'.*'])
    final_response = memory.get_personalized_response(base_response)
    return final_response

# 主聊天循环
if __name__ == '__main__':
    print("Therapist: Hello! My name is ELIZA. How can I help you today?")
    print("Therapist: You can tell me about yourself - your name, age, work, or anything on your mind.")

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["quit", "exit", "bye"]:
            print(f"Therapist: Goodbye. It was nice talking to you.")
            if memory.memory['name']:
                print(f"Therapist: Take care, {memory.memory['name']}!")
            break

        response = respond(user_input)
        memory.add_to_history(user_input, response)
        print(f"Therapist: {response}")

        # 偶尔展示记忆内容（调试模式）
        if random.random() < 0.1:  # 10%概率
            if memory.memory['name']:
                print(f"(Note: I remember your name is {memory.memory['name']})")