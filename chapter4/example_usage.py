#!/usr/bin/env python
"""
HelloAgentsLLM使用示例
"""

import sys
sys.path.append('.')

from llm_client import HelloAgentsLLM


def example_default_config():
    """示例1: 使用默认配置（从.env文件读取）"""
    print("=" * 60)
    print("示例1: 使用默认配置（从.env文件读取）")
    print("=" * 60)

    try:
        # 不传任何参数，自动从.env文件读取配置
        llm = HelloAgentsLLM()
        config = llm.get_config()
        print(f"配置信息: {config}")

        # 简单的流式调用
        messages = [
            {"role": "user", "content": "请用一句话介绍你自己"}
        ]

        response = llm.think(messages, temperature=0.7, max_tokens=200)
        print(f"\n响应: {response}")

    except Exception as e:
        print(f"错误: {e}")


def example_custom_config():
    """示例2: 使用自定义参数覆盖.env配置"""
    print("\n" + "=" * 60)
    print("示例2: 使用自定义参数覆盖.env配置")
    print("=" * 60)

    try:
        # 使用自定义参数（这里使用假参数，实际使用时替换为真实值）
        llm = HelloAgentsLLM(
            base_url="https://api.example.com/v1",  # 自定义base_url
            api_key="sk-custom-key-12345",          # 自定义api_key
            model="custom-model",                   # 自定义模型
            timeout=30                              # 自定义超时时间
        )
        config = llm.get_config()
        print(f"配置信息: {config}")
        print("注意: 这里使用了假参数，实际调用会失败")

    except Exception as e:
        print(f"预期中的错误（因为使用了假参数）: {e}")


def example_non_streaming():
    """示例3: 使用非流式调用"""
    print("\n" + "=" * 60)
    print("示例3: 使用非流式调用")
    print("=" * 60)

    try:
        # 从.env初始化
        llm = HelloAgentsLLM()

        # 使用非流式调用
        messages = [
            {"role": "system", "content": "你是一个有用的助手"},
            {"role": "user", "content": "什么是机器学习？请简要回答"}
        ]

        response = llm.think(
            messages,
            temperature=0.5,
            max_tokens=300,
            stream=False  # 关闭流式调用
        )

        print(f"非流式响应（{len(response)}字符）:\n")
        print(response)

    except Exception as e:
        print(f"错误: {e}")


def example_multiple_messages():
    """示例4: 使用多轮对话"""
    print("\n" + "=" * 60)
    print("示例4: 使用多轮对话")
    print("=" * 60)

    try:
        llm = HelloAgentsLLM()

        # 第一轮
        messages = [
            {"role": "user", "content": "Python是什么？"}
        ]
        response1 = llm.think(messages, max_tokens=150)
        print(f"第一轮回答: {response1[:100]}...")

        # 第二轮（基于第一轮的回答）
        messages.append({"role": "assistant", "content": response1})
        messages.append({"role": "user", "content": "它有哪些主要应用领域？"})

        response2 = llm.think(messages, max_tokens=200)
        print(f"\n第二轮回答: {response2[:100]}...")

    except Exception as e:
        print(f"错误: {e}")


def main():
    """运行所有示例"""
    print("HelloAgentsLLM 使用示例")
    print("=" * 60)

    example_default_config()
    example_custom_config()
    example_non_streaming()
    example_multiple_messages()

    print("\n" + "=" * 60)
    print("所有示例完成")
    print("=" * 60)


if __name__ == "__main__":
    main()