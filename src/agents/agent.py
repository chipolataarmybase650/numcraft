"""
多智能体协作G代码生成系统 - Agent入口
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

# 导入所有工具
from tools.process_planning_tools import (
    recognize_features, 
    generate_process_plan, 
    validate_process_feasibility
)
from tools.tool_selection_tools import (
    select_tools_for_features, 
    optimize_cutting_parameters, 
    check_tool_interference
)
from tools.path_planning_tools import (
    generate_drilling_path, 
    generate_milling_path, 
    optimize_path_sequence
)
from tools.gcode_generation_tools import (
    generate_gcode_program, 
    optimize_gcode, 
    convert_to_fanuc_gcode,
    generate_gcode_documentation
)
from tools.validation_tools import (
    validate_gcode_safety, 
    check_tool_collision, 
    analyze_machining_time,
    validate_program_structure
)
from storage.memory.memory_saver import get_memory_saver


LLM_CONFIG = "config/agent_llm_config.json"

# 保留最近20轮对话
MAX_MESSAGES = 40


def _windowed_messages(old, new):
    """滑动窗口: 只保留最近 MAX_MESSAGES 条消息"""
    return add_messages(old, new)[-MAX_MESSAGES:]


class AgentState(MessagesState):
    """Agent状态"""
    messages: Annotated[List[AnyMessage], _windowed_messages]


def build_agent(ctx=None):
    """构建Agent实例"""
    
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    config_path = os.path.join(workspace_path, LLM_CONFIG)
    
    # 读取配置
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    
    # 获取API配置
    api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
    base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")
    
    # 创建LLM
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
    
    # 定义工具列表
    tools = [
        # 工艺规划工具
        recognize_features,
        generate_process_plan,
        validate_process_feasibility,
        
        # 刀具选择工具
        select_tools_for_features,
        optimize_cutting_parameters,
        check_tool_interference,
        
        # 路径规划工具
        generate_drilling_path,
        generate_milling_path,
        optimize_path_sequence,
        
        # G代码生成工具
        generate_gcode_program,
        optimize_gcode,
        convert_to_fanuc_gcode,
        generate_gcode_documentation,
        
        # 验证工具
        validate_gcode_safety,
        check_tool_collision,
        analyze_machining_time,
        validate_program_structure,
    ]
    
    # 创建Agent
    agent = create_agent(
        model=llm,
        system_prompt=cfg.get("sp"),
        tools=tools,
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
    
    return agent
