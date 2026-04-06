# -*- coding: utf-8 -*-
"""
简化版狼人杀 - 主程序
重点演示 AgentScope 组件的使用和消息驱动机制
"""
import asyncio
import os
import sys
from typing import List, Dict

# 修复模块导入路径：确保当前目录在 sys.path 中
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from agentscope.agent import ReActAgent
from agentscope.message import Msg
from agentscope.pipeline import MsgHub, sequential_pipeline, fanout_pipeline
from pydantic import BaseModel, Field
from collections import Counter

from agents import create_agents_for_game, get_simple_prompt

# pipelines 中的函数在 simple_game.py 中直接实现，不需要导入
# from pipelines import (
#     sequential_demo,
#     fanout_demo,
#     msg_hub_demo,
#     msg_hub_broadcast_control_demo,
# )


# =============================================================================
# 配置
# =============================================================================
# ⚠️ 请先设置你的 API Key！
# 方式1：在命令行设置环境变量
#   set DASHSCOPE_API_KEY=your-actual-api-key
#
# 方式2：直接在这里修改（仅用于测试，生产环境不要这样做！）
# os.environ["DASHSCOPE_API_KEY"] = "sk-xxxxxxxxxxxx"

# 6人游戏配置：2狼人 + 1预言家 + 3村民
PLAYER_NAMES = ["刘备", "曹操", "孙权", "周瑜", "张飞", "赵云"]
ROLES = {
    "刘备": "狼人",
    "曹操": "狼人",
    "孙权": "预言家",
    "周瑜": "村民",
    "张飞": "村民",
    "赵云": "村民",
}


# =============================================================================
# 投票模型
# =============================================================================
class VoteModel(BaseModel):
    """投票格式"""
    vote: str = Field(description="投票给谁")
    reason: str = Field(description="投票理由（简短）")


class DiscussionModel(BaseModel):
    """讨论格式"""
    opinion: str = Field(description="你的观点")
    target: str = Field(description="你怀疑的对象")


# =============================================================================
# 游戏类
# =============================================================================
class SimpleWerewolfGame:
    """
    简化版狼人杀游戏

    核心学习点：
    1. Agent 的创建和调用
    2. MsgHub 消息中心的工作机制
    3. 消息如何在 Agent 之间传递
    4. Agent 的记忆是否同步
    """

    def __init__(self):
        self.agents: Dict[str, ReActAgent] = {}
        self.roles: Dict[str, str] = {}
        self.alive_players: List[ReActAgent] = []
        self.werewolves: List[ReActAgent] = []

    async def setup_game(self):
        """初始化游戏"""
        print("\n" + "=" * 60)
        print("🎮 游戏初始化")
        print("=" * 60)

        # 创建所有 Agent
        self.agents = create_agents_for_game(PLAYER_NAMES, ROLES)

        # 设置存活玩家
        self.alive_players = [self.agents[name] for name in PLAYER_NAMES]

        # 设置狼人列表
        self.werewolves = [self.agents[name] for name in PLAYER_NAMES if ROLES[name] == "狼人"]

        # 打印游戏配置
        print(f"\n📋 游戏配置：{len(self.alive_players)} 名玩家")
        for name in PLAYER_NAMES:
            role = ROLES[name]
            is_werewolf = "🐺" if role == "狼人" else "😊"
            print(f"  {is_werewolf} {name} - {role}")

    # ==========================================================================
    # 夜晚阶段：MsgHub 内部通信演示
    # ==========================================================================
    async def night_phase(self):
        """
        夜晚阶段 - 重点演示 MsgHub 内 Agent 通信
        """
        print("\n" + "=" * 60)
        print("🌙 夜晚阶段")
        print("=" * 60)

        # -------------------------------------------------------------------------
        # 狼人讨论（MsgHub 群聊）
        # -------------------------------------------------------------------------
        print("\n🐺 狼人队伍进入私密群聊...")
        print(f"   成员: {[w.name for w in self.werewolves]}")
        print("\n【核心问题1】MsgHub 内 Agent 是如何通信的？")
        print("-" * 40)

        async with MsgHub(
            participants=self.werewolves,
            enable_auto_broadcast=True,
            announcement="🐺 狼人群已创建，请讨论今晚击杀目标",
        ) as werewolves_hub:

            print("\n  📝 MsgHub 工作机制：")
            print("""
  1. 创建群聊时，每个狼人 Agent 都被"拉进"群里
  2. 当曹操发言时，消息会通过 MsgHub 广播给其他狼人
  3. 其他狼人（司马懿、张飞）会在自己的"消息队列"中收到这条消息
  4. Agent 内部会更新自己的【记忆/状态】
  """)

            # 让狼人轮流发言
            for wolf in self.werewolves:
                print(f"\n  >>> {wolf.name} 发言：")
                result = await wolf(structured_model=DiscussionModel)
                if result:
                    print(f"      [思考完成]")
                    print(f"      观点: {result.metadata.get('opinion', '')[:50]}...")
                    print(f"      目标: {result.metadata.get('target', '无')}")

        # 退出群聊后，狼人讨论结束
        print("\n🐺 狼人群聊结束")

        # -------------------------------------------------------------------------
        # 狼人投票
        # -------------------------------------------------------------------------
        print("\n🗳️ 狼人投票阶段...")
        print("\n【核心问题2】fanout_pipeline 的 enable_gather=False 是什么？")
        print("-" * 40)
        print("""
  enable_gather=False:
  - 发消息给所有狼人后，不等待"所有人"回复
  - 只要收到回复就继续
  - 适合投票场景（不需要等挂机的）

  enable_gather=True:
  - 发消息后，必须等所有人回复
  - 适合需要收集完整意见的场景
""")

        werewolf_names = [w.name for w in self.werewolves]

        vote_results = await fanout_pipeline(
            self.werewolves,
            msg="请投票选择今晚击杀的目标（不能投给自己人）",
            structured_model=VoteModel,
            enable_gather=False,
        )

        votes = {}
        for i, result in enumerate(vote_results):
            if result and hasattr(result, 'metadata') and result.metadata:
                voted = result.metadata.get('vote', '无效')
                votes[self.werewolves[i].name] = voted
                print(f"  {self.werewolves[i].name} 投票给: {voted}")

        # 统计票数
        vote_count = Counter(votes.values())
        most_voted = vote_count.most_common(1)[0] if vote_count else ("无人", 0)
        print(f"\n📊 投票结果: {most_voted[0]} 以 {most_voted[1]} 票被击杀")

    # ==========================================================================
    # 白天阶段：全员讨论
    # ==========================================================================
    async def day_phase(self):
        """
        白天阶段 - 演示 MsgHub 全员群聊
        """
        print("\n" + "=" * 60)
        print("☀️ 白天阶段")
        print("=" * 60)

        print("\n【核心问题3】MsgHub 内外，Agent 的记忆是否同步？")
        print("-" * 40)
        print("""
  ❌ 重要误解：Agent 的记忆是【独立的】！

  狼人在 MsgHub 里说的话：
  - 狼人 A 看到了 ✅
  - 狼人 B 看到了 ✅
  - 预言家/村民【看不到】❌

  每个 Agent 都有自己的"记忆"，MsgHub 只是消息通道。
  消息会进入 Agent 的【观察队列】，但 Agent 是否"记住"
  取决于 Agent 的内部实现。
""")

        # 全员讨论
        async with MsgHub(
            participants=self.alive_players,
            enable_auto_broadcast=True,
            announcement="☀️ 天亮了！请讨论找出狼人",
        ) as all_hub:

            print("\n📝 全员讨论开始...\n")

            # 顺序发言
            for agent in self.alive_players:
                role = ROLES[agent.name]
                is_wolf = "🐺" if role == "狼人" else "😊"
                print(f"  {is_wolf} {agent.name} 发言：")

                result = await agent(structured_model=DiscussionModel)
                if result:
                    opinion = result.metadata.get('opinion', '')[:40]
                    target = result.metadata.get('target', '无')
                    print(f"      观点: {opinion}...")
                    print(f"      怀疑: {target}")

        # 投票
        print("\n🗳️ 全员投票...")
        vote_results = await fanout_pipeline(
            self.alive_players,
            msg="请投票淘汰一名玩家",
            structured_model=VoteModel,
            enable_gather=False,
        )

        votes = {}
        for i, result in enumerate(vote_results):
            if result and hasattr(result, 'metadata') and result.metadata:
                voted = result.metadata.get('vote', '无效')
                votes[self.alive_players[i].name] = voted
                print(f"  {self.alive_players[i].name} 投票给: {voted}")

        # 统计
        vote_count = Counter(votes.values())
        most_voted = vote_count.most_common(1)[0] if vote_count else ("无人", 0)
        print(f"\n📊 投票结果: {most_voted[0]} 以 {most_voted[1]} 票被淘汰")

    # ==========================================================================
    # 演示 Agent.observe() - 手动推送消息
    # ==========================================================================
    async def demo_observe(self):
        """
        演示如何手动向 Agent 推送消息
        """
        print("\n" + "=" * 60)
        print("📨 Agent.observe() - 手动推送消息")
        print("=" * 60)
        print("""
  observe() 方法用于手动向 Agent 推送消息。
  这就像给某人发私信，而不是在群里说话。
""")

        # 给某个 Agent 发消息
        target = self.agents["刘备"]
        msg = Msg(
            name="系统",
            content="刘备，狼人杀游戏即将开始，请做好准备！",
            role="system"
        )

        print(f"\n  >>> 向 {target.name} 推送消息：'{msg.content}'")
        await target.observe(msg)
        print(f"  >>> 消息已推送给 {target.name}，他已观察到这条消息")


# =============================================================================
# 主函数
# =============================================================================
async def main(self):
    """主函数"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║           🎭 简化版狼人杀 - AgentScope 学习演示                ║
║                                                                ║
║   学习重点：                                                   ║
║   1. ReActAgent 的创建和使用                                   ║
║   2. MsgHub 消息中心的工作机制                                   ║
║   3. sequential_pipeline / fanout_pipeline 区别                 ║
║   4. Agent 之间的消息传递                                       ║
║   5. Agent 记忆是否同步                                         ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
    """)

    # 检查 API Key
    if "DASHSCOPE_API_KEY" not in os.environ or os.environ["DASHSCOPE_API_KEY"] == "your-api-key-here":
        print("\n⚠️ 请先设置 DASHSCOPE_API_KEY 环境变量")
        print("   在代码中修改：os.environ['DASHSCOPE_API_KEY'] = 'your-key'")
        return

    # 创建游戏
    game = SimpleWerewolfGame()
    await game.setup_game()

    # 演示 observe
    await game.demo_observe()

    # 夜晚阶段
    await game.night_phase()

    # 白天阶段
    await game.day_phase()

    print("\n" + "=" * 60)
    print("🎮 游戏结束！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main)