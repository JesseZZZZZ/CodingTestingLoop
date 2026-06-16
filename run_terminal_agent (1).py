import os
import subprocess
import json
import re
from openai import OpenAI
# --- 1. 配置千帆 API ---
# API_URL = "https://openrouter.ai/api/v1/"
# API_KEY = ""
API_URL = "https://qianfan.baidubce.com/v2/"
API_KEY = ""

client = OpenAI(
    base_url=API_URL,
    api_key=API_KEY
)

def _normalize_message_content(content):
    """规范化消息 content，兼容千帆可接受的格式。"""
    if content is None:
        return None
    return str(content)



def _build_qianfan_messages(messages):
    """严格按千帆兼容格式清洗消息体。"""
    clean_messages = []
    for msg in messages:
        clean_msg = {"role": msg["role"]}

        if msg.get("content") is not None:
            clean_msg["content"] = _normalize_message_content(msg.get("content"))
        if msg.get("name"):
            clean_msg["name"] = msg["name"]
        if msg.get("tool_calls"):
            clean_msg["tool_calls"] = msg["tool_calls"]

        clean_messages.append(clean_msg)

    return clean_messages



def call_qianfan_api(messages, functions=None, MODEL = "deepseek-v3.1-250821"):
    """直接调用千帆 API"""
    params = {
        "model": MODEL,
        "messages": _build_qianfan_messages(messages)
    }

    if functions:
        params["functions"] = functions

    try:
        response = client.chat.completions.create(**params)
        return response.model_dump()
    except Exception as e:
        print(f"API 调用失败: {e}")
        return None

import os

def execute_shell(command):
    """在 Linux 终端执行命令，允许引用本地文件，禁止引用外部包"""
    print(f"\n⚡️ [执行终端命令]: {command}")

    # --- 增强版拦截规则 ---
    # 逻辑：匹配 require('pkg') 但排除 require('./pkg') 或 require('/path/pkg')
    # 1. 匹配 require: 查找引号内【不以 . 或 / 开头】的内容
    # 2. 匹配 import: 查找 from 后引号内【不以 . 或 / 开头】的内容
    forbidden_patterns = [
        # 匹配 require("..."), 如果引号内第一个字符不是 . 或 /，则视为外部包
        r"require\s*\(\s*['\"](?![./]).*?['\"]\s*\)",
        
        # 匹配 import ... from "...", 如果引号内第一个字符不是 . 或 /
        r"import\s+.*?from\s+['\"](?![./]).*?['\"]",
        
        # 匹配动态 import("..."), 同样排除 . 或 /
        r"import\s*\(\s*['\"](?![./]).*?['\"]\s*\)",
        
        # 匹配直接导入 import "...", 排除 . 或 /
        r"import\s+['\"](?![./]).*?['\"]"
    ]
    
    for pattern in forbidden_patterns:
        if re.search(pattern, command):
            error_msg = "❌ 安全限制：禁止加载外部 NPM 包。仅允许通过相对路径 (./) 或绝对路径 (/) 引用本地文件。"
            print(f"\n{error_msg}")
            return error_msg
    # --- 拦截结束 ---

    # 环境变量注入逻辑保持不变
    env = os.environ.copy()

    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=60,
            env=env
        )
        return f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    except Exception as e:
        return f"Error: {str(e)}"
# 定义工具函数
functions = [
    {
        "name": "execute_shell",
        "description": "执行 Linux shell 命令并返回结果",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "完整的 shell 命令"}
            },
            "required": ["command"],
        },
    }
]

def run_reasoning_agent(user_query, model_name=None):
    # 初始消息队列
    messages = [
        {"role": "system", "content": "你是一个拥有 Linux 终端权限的 AI 专家。你可以执行命令来完成任务。在调用工具前，请先利用你的推理能力分析任务。"},
        {"role": "user", "content": user_query}
    ]
    
    # 统计 token 使用量
    total_input_tokens = 0
    total_output_tokens = 0

    while True:
        # 调用千帆 API
        response = call_qianfan_api(messages, functions=functions, MODEL=model_name)

        if not response or "choices" not in response:
            print("API 调用失败或返回格式错误")
            break

        # 累计 token 使用量
        if "usage" in response:
            usage = response["usage"]
            total_input_tokens += usage.get("prompt_tokens", 0)
            total_output_tokens += usage.get("completion_tokens", 0)

        choice = response["choices"][0]
        msg = choice["message"]

        # 打印推理过程（如果 API 返回了 reasoning_details）
        if "reasoning_details" in msg and msg["reasoning_details"]:
            print("\n🧠 [模型推理中...]:")
            print(f"--- Reasoning ---\n{msg['reasoning_details']}\n-----------------")

        # 构造需要存回上下文的消息对象（包含推理详情）
        msg_to_append = {
            "role": "assistant",
            "content": msg.get("content") if not msg.get("tool_calls") else None
        }
        if "reasoning_details" in msg:
            msg_to_append["reasoning_details"] = msg["reasoning_details"]
        if "tool_calls" in msg and msg["tool_calls"]:
            msg_to_append["tool_calls"] = msg["tool_calls"]

        messages.append(msg_to_append)

        # 检查是否需要调用工具
        if "tool_calls" not in msg or not msg["tool_calls"]:
            print(f"\n✅ [最终结果]:\n{msg.get('content', '')}")
            break

        # 执行工具调用
        for tool_call in msg["tool_calls"]:
            try:
                args = json.loads(tool_call["function"]["arguments"])
            except json.JSONDecodeError as e:
                print(f"\n❌ 工具调用格式错误: {e}")
                print(f"原始参数: {tool_call['function']['arguments']}")
                return {
                    "error": f"工具调用参数格式无效: {e}",
                    "input_tokens": total_input_tokens,
                    "output_tokens": total_output_tokens,
                    "total_tokens": total_input_tokens + total_output_tokens
                }

            observation = execute_shell(args['command'])
            print("👀[工具运行结果]:\n", observation[:1000])
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "name": "execute_shell",
                "content": observation
            })

    # 返回 token 统计信息
    return {
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "total_tokens": total_input_tokens + total_output_tokens
    }

if __name__ == "__main__":
    task = input("请输入你想要 Agent 执行的任务: ")
    run_reasoning_agent(task, model_name="buhphep1_qwen3_27b")
