"""
最小化Agent测试
"""
import os
import json
from typing import Annotated, List
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from coze_coding_utils.runtime_ctx.context import default_headers
from storage.memory.memory_saver import get_memory_saver


LLM_CONFIG = "config/agent_llm_config.json"
MAX_MESSAGES = 40


def _windowed_messages(old, new):
    """滑动窗口"""
    return add_messages(old, new)[-MAX_MESSAGES]


class AgentState(MessagesState):
    messages: Annotated[List[AnyMessage], _windowed_messages]


def build_agent(ctx=None):
    """构建最小化Agent"""
    
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    config_path = os.path.join(workspace_path, LLM_CONFIG)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    
    api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
    base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")
    
    llm = ChatOpenAI(
        model=cfg['config'].get("model"),
        api_key=api_key,
        base_url=base_url,
        temperature=cfg['config'].get('temperature', 0.7),
        streaming=True,
        timeout=cfg['config'].get('timeout', 600),
        extra_body={
            "thinking": {
                "type": cfg['config'].get('thinking', 'disabled')
            }
        },
        default_headers=default_headers(ctx) if ctx else {}
    )
    
    # 不加载任何工具，只使用基本对话功能
    agent = create_agent(
        model=llm,
        system_prompt="你是一个机加工G代码生成助手。请根据用户描述的零件，简单回答你理解的需求。",
        tools=[],  # 空工具列表
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
    
    return agent
