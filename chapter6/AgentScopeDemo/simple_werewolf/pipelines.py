# -*- coding: utf-8 -*-
"""
简化版狼人杀 - Pipeline 演示模块
重点演示三种执行模式的区别
"""
import asyncio
from typing import List
from agentscope.agent import ReActAgent
from agentscope.message import Msg
from agentscope.pipeline import MsgHub, sequential_pipeline, fanout_pipeline
from pydantic import BaseModel, Field
from typing import Literal


# =============================================================================
# 场景1：sequential_pipeline - 顺序执行
# =============================================================================
"""
【生活比喻】餐厅排队点餐
- 顾客A点餐 → 等待完成 → 顾客B点餐 → 等待完成 → ...
- 一个人处理完，下一个人才能开始

【代码场景】白天轮流发言
- 玩家1发言 → 玩家2发言 → 玩家3发言
- 一个人说完，下一个人再说
"""


async def sequential_demo(agents: List[ReActAgent]):
    """
    演示顺序执行：每个人必须等前面的人说完才能说

    执行顺序：Agent1 → Agent2 → Agent3（严格按顺序）
    """
    print("\n" + "=" * 60)
    print("【演示1】sequential_pipeline - 顺序执行")
    print("=" * 60)
    print("场景：白天轮流发言")
    print("规则：玩家1说完 → 玩家2说 → 玩家3说（依次进行）\n")

    # sequential_pipeline 会自动让每个 Agent 发言
    # 内部会创建一个临时的 MsgHub 来管理消息
    results = await sequential_pipeline(agents)

    print("\n--- 执行结果 ---")
    for i, result in enumerate(results):
        print(f"  {agents[i].name} 发言完成")

    return results


# =============================================================================
# 场景2：fanout_pipeline - 并发执行
# =============================================================================
"""
【生活比喻】群发短信
- 发一条短信给100人
- 100人同时收到，不需要等待彼此

【代码场景】投票
- 向所有玩家发送投票请求
- 玩家同时投票，不需要等其他人
"""


class VoteModel(BaseModel):
    """投票格式"""
    vote: str = Field(description="投票给谁")
    reason: str = Field(description="投票理由")


async def fanout_demo(agents: List[ReActAgent]):
    """
    演示并发执行：所有人同时收到消息，同时处理

    执行顺序：Agent1 + Agent2 + Agent3（同时进行）
    """
    print("\n" + "=" * 60)
    print("【演示2】fanout_pipeline - 并发执行")
    print("=" * 60)
    print("场景：投票选择要淘汰的玩家")
    print("规则：所有人同时收到投票请求，同时投票\n")

    # fanout_pipeline：同时向所有 Agent 发送消息
    vote_results = await fanout_pipeline(
        agents,
        msg="请投票选择要淘汰的玩家（只能投给其他人）",
        structured_model=VoteModel,
        enable_gather=False,  # 不等待所有人，只需要多数
    )

    print("\n--- 投票结果 ---")
    votes = {}
    for i, result in enumerate(vote_results):
        if result and hasattr(result, 'metadata') and result.metadata:
            voted_for = result.metadata.get("vote", "无效票")
            reason = result.metadata.get("reason", "")
            votes[agents[i].name] = voted_for
            print(f"  {agents[i].name} 投票给: {voted_for}")
            print(f"    理由: {reason[:30]}...")

    return votes


# =============================================================================
# 场景3：fanout_pipeline + enable_gather=True
# =============================================================================
"""
【fanout_pipeline 的两个模式】

enable_gather=False（默认）：
- 只发消息，不等待所有人回复
- 只要收到足够多的回复就继续
- 适合：投票（不需要等所有人）

enable_gather=True：
- 发消息，等待所有人回复
- 收集所有回复后继续
- 适合：需要所有人意见的场景
"""


async def fanout_gather_demo(agents: List[ReActAgent]):
    """
    演示并发执行 + 等待所有人回复
    """
    print("\n" + "=" * 60)
    print("【演示3】fanout_pipeline + enable_gather=True")
    print("=" * 60)
    print("场景：收集所有玩家的意见")
    print("规则：所有人都必须回复，收集完整后继续\n")

    # enable_gather=True：必须等待所有人回复
    all_results = await fanout_pipeline(
        agents,
        msg="请发表你对当前局势的看法",
        structured_model=VoteModel,
        enable_gather=True,  # 必须等所有人
    )

    print("\n--- 收集到的所有意见 ---")
    for i, result in enumerate(all_results):
        print(f"  {agents[i].name}: {result.metadata.get('vote', '无效')}")

    return all_results


# =============================================================================
# 场景4：MsgHub - 群聊模式
# =============================================================================
"""
【生活比喻】微信群聊
- 创建一个群，拉多人进来
- 群里的消息所有人都能看到
- 可以设置"群公告"告知讨论主题

【代码场景】狼人夜晚讨论
- 狼人进入私密群
- 狼人们可以看到彼此的发言
- 讨论击杀目标
"""


async def msg_hub_demo(werewolf_agents: List[ReActAgent], all_agents: List[ReActAgent]):
    """
    演示 MsgHub 群聊模式

    关键点：
    1. MsgHub 创建一个"消息中心"
    2. 里面的 Agent 可以互相看到消息
    3. 可以开启/关闭广播模式
    """
    print("\n" + "=" * 60)
    print("【演示4】MsgHub - 群聊模式")
    print("=" * 60)
    print("场景：狼人夜晚在私密群中讨论")
    print("规则：只有狼人能进入这个群，看到彼此发言\n")

    # 创建群聊
    async with MsgHub(
        participants=werewolf_agents,  # 只有狼人参与
        enable_auto_broadcast=True,     # 开启广播：说的消息自动推送给群里所有人
        announcement="🐺 狼人群：请讨论今晚击杀谁",  # 群公告
    ) as werewolves_hub:

        print(f"--- 狼人群创建成功，共 {len(werewolf_agents)} 名成员 ---")
        print("--- 开始讨论 ---\n")

        # 群里的 Agent 可以"看到"彼此的发言
        for agent in werewolf_agents:
            # Agent 在群里发言
            result = await agent()
            print(f"  {agent.name}: [在群里发言]")

        print("\n--- 讨论结束 ---")

    # 退出 with 块后，群聊自动结束
    print("--- 群聊已关闭 ---")

    # 现在演示在"全员群"中的讨论
    print("\n" + "-" * 40)
    print("场景切换：白天全员讨论\n")

    async with MsgHub(
        participants=all_agents,  # 所有人参与
        enable_auto_broadcast=True,
        announcement="☀️ 全体讨论：找出狼人",
    ) as all_hub:

        print(f"--- 全员群创建成功，共 {len(all_agents)} 名成员 ---")

        # 轮流发言（顺序执行）
        for agent in all_agents:
            result = await agent()
            speaker = agent.name
            role = "狼人" if agent in werewolf_agents else "好人"
            print(f"  {speaker} ({role}): [在群里发言]")


# =============================================================================
# 场景5：MsgHub 广播控制
# =============================================================================
"""
【广播开关】

enable_auto_broadcast=True：
- Agent 说的任何话都会自动推送给群里所有人
- 适合：自由讨论

enable_auto_broadcast=False：
- Agent 说的话不会自动广播
- 需要手动调用 werewolves_hub.broadcast(msg) 来发送
- 适合：投票阶段，不需要看到别人的投票

set_auto_broadcast(False)：
- 在 with 块内动态关闭广播
- 常用于：讨论结束后，投票时不希望看到别人的选择
"""


async def msg_hub_broadcast_control_demo(werewolf_agents: List[ReActAgent]):
    """
    演示 MsgHub 的广播开关控制
    """
    print("\n" + "=" * 60)
    print("【演示5】MsgHub - 广播开关控制")
    print("=" * 60)

    async with MsgHub(
        participants=werewolf_agents,
        enable_auto_broadcast=True,
        announcement="🐺 狼人讨论：先讨论，后投票",
    ) as werewolves_hub:

        # 阶段1：自由讨论（开启广播）
        print("\n--- 阶段1：自由讨论（广播开启）---")
        for agent in werewolf_agents:
            await agent()
            print(f"  {agent.name} 发言，大家都能看到")

        # 阶段2：投票（关闭广播）
        print("\n--- 阶段2：投票（广播关闭）---")
        werewolves_hub.set_auto_broadcast(False)  # 关闭广播！
        print("  广播已关闭，投票时看不到别人的选择")

        # 投票
        vote_results = await fanout_pipeline(
            werewolf_agents,
            msg="请投票：今晚杀谁？",
            structured_model=VoteModel,
            enable_gather=False,
        )

        print("\n--- 投票结果 ---")
        for i, result in enumerate(vote_results):
            if result and hasattr(result, 'metadata') and result.metadata:
                print(f"  {werewolf_agents[i].name} 投票给: {result.metadata.get('vote')}")

    print("\n--- 群聊结束 ---")