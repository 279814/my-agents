# -*- coding: utf-8 -*-
"""
MsgHub 专项演示 - 深入理解消息驱动机制
专门解答：Agent 之间如何通信？记忆是否同步？
"""
import asyncio
import os
import sys
from typing import List

# 修复模块导入路径
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from agentscope.agent import ReActAgent
from agentscope.message import Msg
from agentscope.pipeline import MsgHub, fanout_pipeline
from agentscope.model import DashScopeChatModel
from agentscope.formatter import DashScopeMultiAgentFormatter
from pydantic import BaseModel, Field


# =============================================================================
# 配置
# =============================================================================
# ⚠️ 请先设置你的 API Key
# os.environ["DASHSCOPE_API_KEY"] = "your-actual-api-key"


# =============================================================================
# 创建测试 Agent
# =============================================================================
def create_test_agent(name: str, personality: str) -> ReActAgent:
    """创建一个测试用的 Agent"""
    prompt = f"""你是 {name}。

性格特点：{personality}

请用符合你性格的方式回答问题。"""

    return ReActAgent(
        name=name,
        sys_prompt=prompt,
        model=DashScopeChatModel(
            model_name="qwen3-max",
            api_key=os.environ["DASHSCOPE_API_KEY"],
            enable_thinking=True,
        ),
        formatter=DashScopeMultiAgentFormatter(),
    )


# =============================================================================
# 问题解答
# =============================================================================
"""
╔══════════════════════════════════════════════════════════════════════╗
║                    MsgHub 核心问题解答                                 ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  Q1: MsgHub 内 Agent 是如何通信的？                                    ║
║  ───────────────────────────────────                                  ║
║                                                                      ║
║  【消息驱动架构】                                                       ║
║                                                                      ║
║      ┌─────────┐      ┌──────────┐      ┌─────────┐                   ║
║      │ Agent A │ ←──→ │  MsgHub  │ ←──→ │ Agent B │                   ║
║      └─────────┘      └──────────┘      └─────────┘                   ║
║           ↑                                    ↑                       ║
║           │          ┌──────────┐            │                        ║
║           ←─────────→│  消息    │←───────────                         ║
║                      │  队列    │                                    ║
║                      └──────────┘                                    ║
║                                                                      ║
║  1. Agent A 发送消息 → MsgHub 收到                                   ║
║  2. MsgHub 广播消息 → 放入 Agent B 的消息队列                         ║
║  3. Agent B 观察消息 → 更新自己的状态/记忆                             ║
║                                                                      ║
║  Q2: Agent 的记忆是否同步？                                            ║
║  ──────────────────────────────                                       ║
║                                                                      ║
║  ❌ 【错误理解】：Agent 之间自动共享记忆                                ║
║  ✅ 【正确理解】：每个 Agent 有独立记忆，MsgHub 只是消息通道            ║
║                                                                      ║
║      ┌─────────────────────────────────────────────┐                 ║
║      │              MsgHub (消息中心)               │                 ║
║      │                                             │                 ║
║      │   消息: "今晚杀刘备"                         │                 ║
║      │   来自: 曹操                                 │                 ║
║      └──────────────────┬──────────────────────────┘                 ║
║                          │ 广播                                        ║
║              ┌───────────┴───────────┐                                ║
║              ↓                       ↓                                 ║
║      ┌──────────────┐         ┌──────────────┐                         ║
║      │ 曹操 的记忆   │         │ 司马懿 的记忆  │                         ║
║      │              │         │              │                         ║
║      │ 记得:        │         │ 记得:        │                         ║
║      │ "今晚杀刘备" │         │ "今晚杀刘备"  │                         ║
║      │ 来自: 曹操   │         │ 来自: 曹操    │                         ║
║      │              │         │              │                         ║
║      │ 不记得:      │         │ 不记得:      │                         ║
║      │ 预言家说了啥 │         │ 村民说了啥   │                         ║
║      └──────────────┘         └──────────────┘                         ║
║                                                                      ║
║  【关键点】                                                            ║
║  1. MsgHub 是"消息通道"，不是"共享大脑"                                 ║
║  2. 每个 Agent 收到消息后，是否"记住"取决于 Agent 实现                    ║
║  3. 狼人能看到狼队友的话，但看不到预言家的话                            ║
║  4. ReActAgent 的 memory 是独立的                                      ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
"""


# =============================================================================
# 代码演示
# =============================================================================
class DemoModel(BaseModel):
    """演示用输出格式"""
    message: str = Field(description="你要说的内容")


async def demo_message_flow():
    """
    演示消息流动
    """
    print("\n" + "=" * 70)
    print("【演示1】消息流动 - Agent 如何通过 MsgHub 通信")
    print("=" * 70)

    # 创建两个 Agent
    agent_a = create_test_agent("曹操", "雄才大略，善于权谋")
    agent_b = create_test_agent("司马懿", "深谋远虑，城府极深")

    print(f"\n📍 创建两个 Agent：{agent_a.name} 和 {agent_b.name}")
    print("-" * 50)

    # 场景：曹操想在群里发消息
    async with MsgHub(
        participants=[agent_a, agent_b],
        enable_auto_broadcast=True,
        announcement="曹魏群聊已创建",
    ) as hub:

        print("\n📝 曹操在群里说：'司马懿，你觉得今晚该杀谁？'\n")

        # 曹操发言
        await agent_a()

        print(f"\n💬 消息流动过程：")
        print("""
           ┌─────────────────────────────────────────────┐
           │                   MsgHub                     │
           │                                              │
           │  1. agent_a() 被调用                        │
           │  2. Agent A 生成消息                        │
           │  3. MsgHub 收到消息                         │
           │  4. MsgHub 广播消息给 agent_b               │
           │  5. agent_b 的消息隊列收到消息               │
           │  6. agent_b 调用 observe() 时能看到这条消息  │
           └─────────────────────────────────────────────┘
        """)

        # 司马懿回应
        print(f"\n📝 司马懿在群里回应...\n")
        await agent_b()


async def demo_isolated_memory():
    """
    演示 Agent 记忆是隔离的
    """
    print("\n" + "=" * 70)
    print("【演示2】记忆隔离 - 狼人能看到狼队友，看不到村民")
    print("=" * 70)

    # 创建不同阵营的 Agent
    werewolf_cao = create_test_agent("曹操", "狼人 - 魏国首领")
    werewolf_simayi = create_test_agent("司马懿", "狼人 - 深谋远虑")
    seer_zhangfei = create_test_agent("张飞", "预言家 - 勇猛直接")
    villager_zhaoyun = create_test_agent("赵云", "村民 - 忠勇双全")

    print(f"""
📍 创建 4 个 Agent：
   - 狼人阵营：曹操、司马懿
   - 好人阵营：张飞（预言家）、赵云（村民）

🔴 狼人阵营有独立的 MsgHub
☀️ 好人阵营有另一个 MsgHub
""")

    # 狼人在私密群聊天
    print("-" * 50)
    print("🐺 狼人私密群 - 曹操和司马懿讨论...\n")

    async with MsgHub(
        participants=[werewolf_cao, werewolf_simayi],
        enable_auto_broadcast=True,
        announcement="🐺 狼人群：今晚杀谁？",
    ) as werewolf_hub:

        print("曹操说：'我觉得杀张飞，他是预言家太危险'")
        await werewolf_cao()

        print("\n司马懿说：'同意，杀张飞'")
        await werewolf_simayi()

    print("\n❌ 赵云和張飞【听不到】狼人的对话！")

    # 好人在公开群聊天
    print("\n" + "-" * 50)
    print("☀️ 好人公开群 - 张飞和赵云讨论...\n")

    async with MsgHub(
        participants=[seer_zhangfei, villager_zhaoyun],
        enable_auto_broadcast=True,
        announcement="☀️ 全员讨论：找出狼人",
    ) as good_hub:

        print("张飞说：'我觉得曹操是狼人，他说话太油滑'")
        await seer_zhangfei()

        print("\n赵云说：'我也觉得曹操可疑'")
        await villager_zhaoyun()

    print("\n❌ 狼人【听不到】好人的对话！")

    print("\n" + "-" * 50)
    print("📊 记忆隔离总结：")
    print("""
    ┌─────────────────────────────────────────────────────┐
    │                                                     │
    │   狼人 (曹操, 司马懿)                                │
    │   ├── 记得狼队友说的话 ✅                            │
    │   └── 不记得好人群里说的话 ❌                        │
    │                                                     │
    │   好人 (张飞, 赵云)                                 │
    │   ├── 记得好人群里说的话 ✅                         │
    │   └── 不记得狼人私密群说的话 ❌                     │
    │                                                     │
    │   每个 Agent 的 memory 是完全独立的！                │
    │                                                     │
    └─────────────────────────────────────────────────────┘
    """)


async def demo_broadcast_control():
    """
    演示广播开关
    """
    print("\n" + "=" * 70)
    print("【演示3】广播开关 - set_auto_broadcast()")
    print("=" * 70)

    agent1 = create_test_agent("玩家A", "性格1")
    agent2 = create_test_agent("玩家B", "性格2")
    agent3 = create_test_agent("玩家C", "性格3")

    print("""
📍 广播机制说明：

enable_auto_broadcast=True（默认）：
  - Agent 说的任何话都会自动推送给群里所有人
  - 适合：自由讨论、辩论

enable_auto_broadcast=False（关闭）：
  - Agent 说的话不会自动广播
  - 适合：投票（不希望提前知道别人投谁）
  - 需要手动调用 hub.broadcast(msg) 才能发送
""")

    async with MsgHub(
        participants=[agent1, agent2, agent3],
        enable_auto_broadcast=True,
        announcement="讨论阶段",
    ) as hub:

        print("\n📝 阶段1：自由讨论（广播开启）\n")

        print("  玩家A 发言 → 大家都能看到")
        await agent1()
        print("  玩家B 发言 → 大家都能看到")
        await agent2()
        print("  玩家C 发言 → 大家都能看到")
        await agent3()

        print("\n" + "-" * 30)
        print("\n📝 阶段2：投票（广播关闭）\n")

        # 关闭广播
        hub.set_auto_broadcast(False)
        print("  广播已关闭！")
        print("  投票时，Agent 说的话不会推送给其他人")

        print("\n  玩家A 投票 → 只有系统知道")
        await agent1()
        print("  玩家B 投票 → 只有系统知道")
        await agent2()
        print("  玩家C 投票 → 只有系统知道")

        print("\n  【关键应用】投票场景下，关闭广播可以：")
        print("  1. 防止玩家互相看到投票内容")
        print("  2. 模拟真实投票的保密性")
        print("  3. 程序可以先收集所有投票，再统一公布结果")


async def demo_message_types():
    """
    演示不同类型的消息
    """
    print("\n" + "=" * 70)
    print("【演示4】消息类型 - Msg 的结构")
    print("=" * 70)

    print("""
📍 Msg 是 AgentScope 中的消息格式，就像一封信：

    ┌─────────────────────────────────────────────┐
    │               Msg 结构                       │
    │                                             │
    │   name: "曹操"     ← 谁发的信               │
    │   content: "..."   ← 信的内容               │
    │   role: "assistant" ← 发送者角色             │
    │                                             │
    └─────────────────────────────────────────────┘

📍 role 的取值：
  - "user"      ：用户发送的消息
  - "assistant" ：Agent 生成的消息
  - "system"    ：系统消息（如游戏主持人公告）
""")

    # 创建不同类型的消息
    user_msg = Msg(name="玩家", content="你好", role="user")
    assistant_msg = Msg(name="曹操", content="我是曹操", role="assistant")
    system_msg = Msg(name="系统", content="天亮了", role="system")

    print("\n📝 消息示例：")
    print(f"  用户消息: {user_msg}")
    print(f"  Agent消息: {assistant_msg}")
    print(f"  系统消息: {system_msg}")


# =============================================================================
# 主函数
# =============================================================================
async def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║              🔍 MsgHub 专项演示 - 消息驱动机制                        ║
║                                                                      ║
║   学习目标：                                                          ║
║   1. MsgHub 内 Agent 如何通信                                        ║
║   2. Agent 的记忆是否同步                                             ║
║   3. 广播开关的作用                                                   ║
║   4. Msg 消息结构                                                    ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """)

    # 打印问题解答
    print(__doc__)

    # 检查 API Key
    if "DASHSCOPE_API_KEY" not in os.environ or os.environ["DASHSCOPE_API_KEY"] == "your-api-key-here":
        print("\n⚠️ 请先设置 DASHSCOPE_API_KEY 环境变量")
        print("   在代码中修改第 15 行：os.environ['DASHSCOPE_API_KEY'] = 'your-key'")
        return

    # 执行演示
    await demo_message_flow()
    await demo_isolated_memory()
    await demo_broadcast_control()
    await demo_message_types()

    print("\n" + "=" * 70)
    print("🎉 MsgHub 演示结束！")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())