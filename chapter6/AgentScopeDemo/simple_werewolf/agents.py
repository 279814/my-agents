# -*- coding: utf-8 -*-
"""
简化版狼人杀 - Agent 创建模块
专注于 AgentScope 的 ReActAgent 使用
"""
import os
from agentscope.agent import ReActAgent
from agentscope.model import DashScopeChatModel
from agentscope.formatter import DashScopeMultiAgentFormatter


def create_basic_agent(name: str, role: str, role_prompt: str) -> ReActAgent:
    """
    创建一个基础的 ReActAgent

    参数:
        name: Agent 名字
        role: 角色身份（狼人/预言家/村民）
        role_prompt: 角色提示词

    返回:
        ReActAgent 实例
    """
    agent = ReActAgent(
        name=name,
        sys_prompt=role_prompt,
        model=DashScopeChatModel(
            model_name="qwen3-max",
            api_key=os.environ["DASHSCOPE_API_KEY"],
            enable_thinking=True,
        ),
        formatter=DashScopeMultiAgentFormatter(),
    )
    return agent


def create_agents_for_game(player_names: list, roles: dict) -> dict:
    """
    为游戏创建多个 Agent

    参数:
        player_names: 玩家名字列表
        roles: 名字->角色 的字典

    返回:
        名字->Agent 的字典
    """
    agents = {}

    for name in player_names:
        role = roles[name]
        prompt = get_simple_prompt(name, role)
        agents[name] = create_basic_agent(name, role, prompt)

    return agents


def get_simple_prompt(name: str, role: str) -> str:
    """
    生成简单的角色提示词
    """
    prompts = {
        "狼人": f"""你是 {name}，在这场狼人杀游戏中扮演【狼人】。

你的目标：消灭所有好人
你的技能：夜晚可以击杀一名玩家

游戏规则：
1. 狼人夜晚可以讨论并投票选择击杀目标
2. 白天要隐藏身份，装作好人
3. 你的发言应该试图误导好人

请以 {name} 的身份和风格发言。""",

        "预言家": f"""你是 {name}，在这场狼人杀游戏中扮演【预言家】。

你的目标：找出所有狼人
你的技能：每晚可以查验一名玩家的身份

游戏规则：
1. 夜晚可以选择一名玩家进行查验
2. 查验结果会告诉你该玩家是狼人还是好人
3. 你可以选择性地公开或隐藏你的查验结果

请以 {name} 的身份和风格发言。""",

        "村民": f"""你是 {name}，在这场狼人杀游戏中扮演【村民】。

你的目标：找出所有狼人并投票淘汰他们
你的技能：无特殊技能，只能通过发言和投票

游戏规则：
1. 白天通过讨论找出狼人
2. 通过分析发言来判断谁可能是狼人
3. 投票淘汰你认为是狼人的玩家

请以 {name} 的身份和风格发言。""",
    }

    return prompts.get(role, prompts["村民"])