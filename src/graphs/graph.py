"""
多智能体协作G代码生成系统 - 主流程图
使用LangGraph实现状态机编排
"""
import os
import json
import logging
from typing import TypedDict, Optional, Dict, Any, Literal
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from graphs.state import MachiningState, DEFAULT_STATE
from tools.process_planning_tools import recognize_features, generate_process_plan, validate_process_feasibility
from tools.tool_selection_tools import select_tools_for_features, optimize_cutting_parameters, check_tool_interference
from tools.path_planning_tools import generate_drilling_path, generate_milling_path, optimize_path_sequence
from tools.gcode_generation_tools import generate_gcode_program, optimize_gcode, convert_to_fanuc_gcode
from tools.validation_tools import validate_gcode_safety, check_tool_collision, analyze_machining_time, validate_program_structure

logger = logging.getLogger(__name__)


# ============================================================================
# 智能体节点定义
# ============================================================================

def orchestrator_node(state: MachiningState) -> Dict[str, Any]:
    """
    编排器节点
    负责初始化和协调各个智能体的执行
    """
    logger.info("=== Orchestrator Node ===")
    
    updates = {
        "current_agent": "orchestrator",
        "current_stage": "init",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    
    if state.get("iteration", 0) == 0:
        updates["iteration"] = 1
        updates["messages"] = [HumanMessage(content=f"开始处理零件加工任务: {state.get('part_description', '')}")]
    
    return updates


def process_planner_node(state: MachiningState) -> Dict[str, Any]:
    """
    工艺规划专家节点
    分析零件特征，制定加工工艺路线
    """
    logger.info("=== Process Planner Node ===")
    
    part_description = state.get("part_description", "")
    material = state.get("material", "未知材料")
    precision_requirements = state.get("precision_requirements", {})
    
    # 识别特征
    features_json = recognize_features.invoke({
        "part_description": part_description,
        "material": material
    })
    
    features_data = json.loads(features_json)
    
    # 生成工艺规划
    process_plan_json = generate_process_plan.invoke({
        "features": features_json,
        "material": material,
        "precision_requirements": json.dumps(precision_requirements)
    })
    
    process_plan_data = json.loads(process_plan_json)
    
    # 验证可行性
    machine_type = state.get("machine_type", "三轴铣床")
    feasibility_json = validate_process_feasibility.invoke({
        "process_plan": process_plan_json,
        "machine_type": machine_type
    })
    
    feasibility_data = json.loads(feasibility_json)
    
    updates = {
        "current_agent": "process_planner",
        "current_stage": "planning",
        "features": features_data.get("features", []),
        "process_plan": process_plan_data,
        "updated_at": datetime.now().isoformat(),
    }
    
    # 如果需要修订，添加反馈
    if feasibility_data.get("review_required", False):
        updates["needs_revision"] = True
        updates["feedback"] = feasibility_data.get("warnings", [])
    
    logger.info(f"识别到 {len(features_data.get('features', []))} 个特征")
    
    return updates


def tool_expert_node(state: MachiningState) -> Dict[str, Any]:
    """
    刀具专家节点
    选择合适的刀具和切削参数
    """
    logger.info("=== Tool Expert Node ===")
    
    features_json = json.dumps({"features": state.get("features", [])})
    material = state.get("material", "钢")
    
    # 选择刀具
    tools_json = select_tools_for_features.invoke({
        "features": features_json,
        "material": material
    })
    
    tools_data = json.loads(tools_json)
    
    # 优化切削参数
    optimized_json = optimize_cutting_parameters.invoke({
        "tool_list": tools_json,
        "material": material
    })
    
    optimized_data = json.loads(optimized_json)
    
    # 检查刀具干涉
    workpiece_dims = state.get("workpiece_dimensions", {})
    interference_json = check_tool_interference.invoke({
        "tool_list": optimized_json,
        "workpiece_dimensions": json.dumps(workpiece_dims)
    })
    
    interference_data = json.loads(interference_json)
    
    updates = {
        "current_agent": "tool_expert",
        "current_stage": "tool_selection",
        "tool_list": optimized_data.get("optimized_tool_list", []),
        "cutting_parameters": optimized_data,
        "updated_at": datetime.now().isoformat(),
    }
    
    # 如果有干涉问题，添加反馈
    if interference_data.get("has_interference", False):
        updates["needs_revision"] = True
        updates["feedback"] = interference_data.get("interference_issues", [])
    elif interference_data.get("warnings"):
        if not updates.get("feedback"):
            updates["feedback"] = []
        updates["feedback"].extend(interference_data.get("warnings", []))
    
    logger.info(f"选择了 {len(optimized_data.get('optimized_tool_list', []))} 把刀具")
    
    return updates


def path_planner_node(state: MachiningState) -> Dict[str, Any]:
    """
    路径规划师节点
    生成优化的刀具路径
    """
    logger.info("=== Path Planner Node ===")
    
    features = state.get("features", [])
    tool_list = state.get("tool_list", [])
    
    all_paths = []
    
    # 为每个特征生成路径
    for feature in features:
        feature_type = feature.get("feature_type")
        feature_json = json.dumps(feature)
        
        # 找到对应的刀具
        matching_tools = [t for t in tool_list if t.get("feature_id") == feature.get("feature_id")]
        
        if not matching_tools:
            logger.warning(f"未找到特征 {feature.get('feature_id')} 的刀具")
            continue
        
        if feature_type == "hole":
            # 钻孔路径
            for tool in matching_tools:
                if tool.get("operation") == "drilling":
                    path_json = generate_drilling_path.invoke({
                        "hole_features": json.dumps({"features": [feature]}),
                        "tool_params": json.dumps(tool)
                    })
                    path_data = json.loads(path_json)
                    all_paths.extend(path_data.get("drilling_paths", []))
        
        elif feature_type in ["slot", "pocket", "contour"]:
            # 铣削路径
            for tool in matching_tools:
                operation_type = "rough" if "rough" in tool.get("operation", "") else "finish"
                path_json = generate_milling_path.invoke({
                    "feature": feature_json,
                    "tool_params": json.dumps(tool),
                    "operation_type": operation_type
                })
                path_data = json.loads(path_json)
                all_paths.append(path_data)
    
    # 优化路径顺序
    optimized_paths_json = optimize_path_sequence.invoke({
        "paths": json.dumps({"tool_paths": all_paths})
    })
    
    optimized_paths_data = json.loads(optimized_paths_json)
    
    updates = {
        "current_agent": "path_planner",
        "current_stage": "path_planning",
        "tool_paths": optimized_paths_data.get("optimized_paths", []),
        "updated_at": datetime.now().isoformat(),
    }
    
    logger.info(f"生成了 {len(optimized_paths_data.get('optimized_paths', []))} 条优化路径")
    logger.info(f"路径优化率: {optimized_paths_data.get('optimization_rate', 0):.1f}%")
    
    return updates


def gcode_generator_node(state: MachiningState) -> Dict[str, Any]:
    """
    G代码生成器节点
    将路径数据转换为标准G代码
    """
    logger.info("=== G-Code Generator Node ===")
    
    tool_paths = state.get("tool_paths", [])
    process_plan = state.get("process_plan", {})
    
    # 准备程序信息
    program_info = {
        "program_number": "0001",
        "program_name": "CNC_MACHINING",
        "material": state.get("material", "Unknown"),
        "workpiece_size": str(state.get("workpiece_dimensions", {})),
        "tool_count": len(state.get("tool_list", [])),
        "estimated_time": process_plan.get("estimated_time", 0)
    }
    
    # 生成G代码
    gcode_json = generate_gcode_program.invoke({
        "tool_paths": json.dumps({"tool_paths": tool_paths}),
        "program_info": json.dumps(program_info)
    })
    
    gcode_data = json.loads(gcode_json)
    
    # 优化G代码
    optimized_json = optimize_gcode.invoke({
        "gcode_program": gcode_data.get("gcode_program", "")
    })
    
    optimized_data = json.loads(optimized_json)
    
    # 转换为FANUC格式
    fanuc_json = convert_to_fanuc_gcode.invoke({
        "gcode_program": optimized_data.get("optimized_gcode", "")
    })
    
    fanuc_data = json.loads(fanuc_json)
    
    updates = {
        "current_agent": "gcode_generator",
        "current_stage": "gcode_generation",
        "gcode_program": fanuc_data.get("fanuc_gcode", ""),
        "gcode_metadata": {
            "original_lines": optimized_data.get("original_lines", 0),
            "optimized_lines": optimized_data.get("optimized_lines", 0),
            "reduction_percentage": optimized_data.get("reduction_percentage", 0),
            "compatible_models": fanuc_data.get("compatible_models", [])
        },
        "updated_at": datetime.now().isoformat(),
    }
    
    logger.info(f"生成G代码 {len(fanuc_data.get('fanuc_gcode', ''))} 字节")
    logger.info(f"代码优化率: {optimized_data.get('reduction_percentage', 0):.1f}%")
    
    return updates


def safety_validator_node(state: MachiningState) -> Dict[str, Any]:
    """
    安全验证器节点
    验证G代码的安全性和合理性
    """
    logger.info("=== Safety Validator Node ===")
    
    gcode_program = state.get("gcode_program", "")
    workpiece_dimensions = state.get("workpiece_dimensions", {})
    tool_list = state.get("tool_list", [])
    
    # 安全验证
    safety_json = validate_gcode_safety.invoke({
        "gcode_program": gcode_program,
        "workpiece_dimensions": json.dumps(workpiece_dimensions)
    })
    
    safety_data = json.loads(safety_json)
    
    # 碰撞检查
    collision_json = check_tool_collision.invoke({
        "gcode_program": gcode_program,
        "tool_list": json.dumps({"tool_list": tool_list})
    })
    
    collision_data = json.loads(collision_json)
    
    # 加工时间分析
    time_json = analyze_machining_time.invoke({
        "gcode_program": gcode_program
    })
    
    time_data = json.loads(time_json)
    
    # 程序结构验证
    structure_json = validate_program_structure.invoke({
        "gcode_program": gcode_program
    })
    
    structure_data = json.loads(structure_json)
    
    # 汇总验证结果
    is_valid = (
        safety_data.get("is_valid", False) and 
        not collision_data.get("has_collision_risk", False) and
        structure_data.get("structure_complete", False)
    )
    
    all_errors = []
    all_errors.extend(safety_data.get("errors", []))
    all_errors.extend([f"碰撞风险: {r}" for r in collision_data.get("collision_risks", [])])
    
    all_warnings = []
    all_warnings.extend(safety_data.get("warnings", []))
    all_warnings.extend(collision_data.get("warnings", []))
    
    all_safety_issues = safety_data.get("safety_issues", [])
    
    all_optimizations = []
    all_optimizations.extend(safety_data.get("optimization_suggestions", []))
    all_optimizations.extend(time_data.get("optimization_suggestions", []))
    
    validation_result = {
        "is_valid": is_valid,
        "errors": all_errors,
        "warnings": all_warnings,
        "safety_issues": all_safety_issues,
        "optimization_suggestions": all_optimizations,
        "machining_time": time_data.get("total_time_minutes", 0),
        "completeness_score": structure_data.get("completeness_score", 0)
    }
    
    updates = {
        "current_agent": "safety_validator",
        "current_stage": "validation",
        "validation_result": validation_result,
        "updated_at": datetime.now().isoformat(),
    }
    
    # 如果验证失败，需要修订
    if not is_valid:
        updates["needs_revision"] = True
        updates["feedback"] = all_errors + all_warnings
    
    logger.info(f"验证结果: {'通过' if is_valid else '失败'}")
    logger.info(f"错误: {len(all_errors)}, 警告: {len(all_warnings)}")
    
    return updates


def decision_node(state: MachiningState) -> Literal["process_planner", "end"]:
    """
    决策节点
    判断是否需要重新规划
    """
    logger.info("=== Decision Node ===")
    
    needs_revision = state.get("needs_revision", False)
    iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", 3)
    
    if needs_revision and iteration < max_iterations:
        logger.info(f"需要修订 (迭代 {iteration}/{max_iterations})")
        return "process_planner"
    
    logger.info("流程完成")
    return "end"


# ============================================================================
# 构建流程图
# ============================================================================

def build_graph():
    """构建多智能体协作流程图"""
    
    # 创建状态图
    workflow = StateGraph(MachiningState)
    
    # 添加节点
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("process_planner", process_planner_node)
    workflow.add_node("tool_expert", tool_expert_node)
    workflow.add_node("path_planner", path_planner_node)
    workflow.add_node("gcode_generator", gcode_generator_node)
    workflow.add_node("safety_validator", safety_validator_node)
    
    # 设置入口点
    workflow.set_entry_point("orchestrator")
    
    # 添加边（定义流程）
    workflow.add_edge("orchestrator", "process_planner")
    workflow.add_edge("process_planner", "tool_expert")
    workflow.add_edge("tool_expert", "path_planner")
    workflow.add_edge("path_planner", "gcode_generator")
    workflow.add_edge("gcode_generator", "safety_validator")
    
    # 添加条件边（决策节点）
    workflow.add_conditional_edges(
        "safety_validator",
        decision_node,
        {
            "process_planner": "process_planner",
            "end": END
        }
    )
    
    # 编译图
    graph = workflow.compile()
    
    return graph


# 创建图实例
graph = build_graph()
