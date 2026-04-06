# -*- coding: utf-8 -*-
"""
简化版狼人杀 - AgentScope 学习项目
"""
from .agents import create_basic_agent, create_agents_for_game, get_simple_prompt
from .pipelines import (
    sequential_demo,
    fanout_demo,
    msg_hub_demo,
    msg_hub_broadcast_control_demo,
)
from .simple_game import SimpleWerewolfGame

__all__ = [
    "create_basic_agent",
    "create_agents_for_game",
    "get_simple_prompt",
    "sequential_demo",
    "fanout_demo",
    "msg_hub_demo",
    "msg_hub_broadcast_control_demo",
    "SimpleWerewolfGame",
]