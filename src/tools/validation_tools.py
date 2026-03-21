"""
验证工具集
用于G代码的安全检查和验证
"""
from typing import Dict, List, Any
from langchain.tools import tool
import json
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@tool
def validate_gcode_safety(gcode_program: str, workpiece_dimensions: str) -> str:
    """
    验证G代码的安全性
    
    Args:
        gcode_program: G代码程序
        workpiece_dimensions: JSON格式的工作尺寸
    
    Returns:
        JSON格式的验证结果
    """
    if not gcode_program:
        return json.dumps({"error": "Empty G-code program"}, ensure_ascii=False)
    
    try:
        workpiece = json.loads(workpiece_dimensions) if workpiece_dimensions else {}
    except json.JSONDecodeError:
        workpiece = {}
    
    errors = []
    warnings = []
    safety_issues = []
    optimization_suggestions = []
    
    lines = gcode_program.strip().split('\n')
    
    # 工作区域边界
    x_min, x_max = -500, 500
    y_min, y_max = -500, 500
    z_min, z_max = -300, 100
    
    if workpiece:
        x_min = workpiece.get("x_min", x_min)
        x_max = workpiece.get("x_max", x_max)
        y_min = workpiece.get("y_min", y_min)
        y_max = workpiece.get("y_max", y_max)
        z_min = workpiece.get("z_min", z_min)
        z_max = workpiece.get("z_max", z_max)
    
    # 检查坐标超限
    for i, line in enumerate(lines, 1):
        # 提取坐标值
        x_match = re.search(r'X(-?\d+\.?\d*)', line)
        y_match = re.search(r'Y(-?\d+\.?\d*)', line)
        z_match = re.search(r'Z(-?\d+\.?\d*)', line)
        
        if x_match:
            x_val = float(x_match.group(1))
            if x_val < x_min or x_val > x_max:
                warnings.append(f"行{i}: X坐标{x_val}超出工作范围[{x_min}, {x_max}]")
        
        if y_match:
            y_val = float(y_match.group(1))
            if y_val < y_min or y_val > y_max:
                warnings.append(f"行{i}: Y坐标{y_val}超出工作范围[{y_min}, {y_max}]")
        
        if z_match:
            z_val = float(z_match.group(1))
            if z_val < z_min:
                errors.append(f"行{i}: Z坐标{z_val}可能造成碰撞")
            elif z_val > z_max:
                warnings.append(f"行{i}: Z坐标{z_val}超出安全范围")
    
    # 检查主轴和进给设置
    has_spindle_start = False
    has_spindle_stop = False
    has_coolant = False
    
    for line in lines:
        if 'M3' in line or 'M03' in line or 'M4' in line or 'M04' in line:
            has_spindle_start = True
        if 'M5' in line or 'M05' in line:
            has_spindle_stop = True
        if 'M8' in line or 'M08' in line:
            has_coolant = True
    
    if not has_spindle_start:
        errors.append("未检测到主轴启动指令(M3/M4)")
    
    # 检查刀具补偿
    has_tool_compensation = any('G43' in line for line in lines)
    if not has_tool_compensation:
        warnings.append("未检测到刀具长度补偿(G43)，可能导致Z轴位置错误")
    
    # 检查程序结束
    has_program_end = any('M30' in line or 'M2' in line for line in lines)
    if not has_program_end:
        warnings.append("程序缺少结束指令(M30/M2)")
    
    # 安全建议
    safety_issues.append("建议首次运行时使用单段执行模式")
    safety_issues.append("注意观察刀具切入切出的位置")
    
    if has_coolant:
        optimization_suggestions.append("冷却液已启用，适合加工难加工材料")
    else:
        optimization_suggestions.append("未检测到冷却液指令，建议对钢件加工开启冷却液")
    
    # 检查进给速度合理性
    feed_rates = []
    for line in lines:
        feed_match = re.search(r'F(\d+)', line)
        if feed_match:
            feed_rates.append(int(feed_match.group(1)))
    
    if feed_rates:
        max_feed = max(feed_rates)
        if max_feed > 5000:
            warnings.append(f"检测到高进给速度{max_feed} mm/min，请确认刀具和材料适用")
        elif max_feed < 50:
            warnings.append(f"检测到低进给速度{max_feed} mm/min，可能影响加工效率")
    
    result = {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "safety_issues": safety_issues,
        "optimization_suggestions": optimization_suggestions,
        "validation_summary": {
            "total_lines": len(lines),
            "error_count": len(errors),
            "warning_count": len(warnings),
            "work_envelope": {
                "x_range": [x_min, x_max],
                "y_range": [y_min, y_max],
                "z_range": [z_min, z_max]
            },
            "spindle_control": has_spindle_start,
            "coolant_enabled": has_coolant,
            "tool_compensation": has_tool_compensation
        },
        "validated_at": datetime.now().isoformat()
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def check_tool_collision(gcode_program: str, tool_list: str) -> str:
    """
    检查刀具碰撞风险
    
    Args:
        gcode_program: G代码程序
        tool_list: JSON格式的刀具清单
    
    Returns:
        JSON格式的碰撞检查结果
    """
    if not gcode_program:
        return json.dumps({"error": "Empty G-code program"}, ensure_ascii=False)
    
    try:
        tools = json.loads(tool_list).get("tool_list", []) if tool_list else []
    except json.JSONDecodeError:
        tools = []
    
    collision_risks = []
    warnings = []
    
    # 提取刀具信息
    tool_diameters = {}
    for tool in tools:
        tool_id = tool.get("tool_id")
        diameter = tool.get("diameter", 10)
        tool_diameters[tool_id] = diameter
    
    # 分析路径
    lines = gcode_program.strip().split('\n')
    current_tool = None
    current_position = {"x": 0, "y": 0, "z": 0}
    rapid_moves = []
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # 检测刀具更换
        if stripped.startswith('T') and 'M6' in stripped:
            tool_match = re.match(r'T(\d+)', stripped)
            if tool_match:
                current_tool = f"T{int(tool_match.group(1)):02d}"
        
        # 提取坐标
        x_match = re.search(r'X(-?\d+\.?\d*)', stripped)
        y_match = re.search(r'Y(-?\d+\.?\d*)', stripped)
        z_match = re.search(r'Z(-?\d+\.?\d*)', stripped)
        
        if x_match:
            current_position["x"] = float(x_match.group(1))
        if y_match:
            current_position["y"] = float(y_match.group(1))
        if z_match:
            current_position["z"] = float(z_match.group(1))
        
        # 记录快速移动
        if stripped.startswith('G0') or stripped.startswith('G00'):
            if current_position["z"] < 0:  # 快速移动时Z在工件下方
                collision_risks.append(f"行{i}: Z={current_position['z']}时快速移动，有碰撞风险")
            
            rapid_moves.append({
                "line": i,
                "position": current_position.copy(),
                "tool": current_tool
            })
    
    # 检查快速移动之间的距离
    for i in range(1, len(rapid_moves)):
        prev = rapid_moves[i-1]
        curr = rapid_moves[i]
        
        # 计算XY平面距离
        distance = ((curr["position"]["x"] - prev["position"]["x"])**2 + 
                   (curr["position"]["y"] - prev["position"]["y"])**2)**0.5
        
        # 如果距离很大且Z很低，可能有问题
        if distance > 100 and curr["position"]["z"] < 5:
            warnings.append(f"行{curr['line']}: 长距离快速移动({distance:.1f}mm)且Z高度较低")
    
    result = {
        "has_collision_risk": len(collision_risks) > 0,
        "collision_risks": collision_risks,
        "warnings": warnings,
        "rapid_move_count": len(rapid_moves),
        "tool_diameters": tool_diameters,
        "recommendations": [
            "建议在快速移动前确保Z轴提升到安全高度",
            "注意刀具切入角度，避免垂直下刀",
            "使用刀具直径较小的刀具时注意进给速度"
        ]
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def analyze_machining_time(gcode_program: str) -> str:
    """
    分析G代码预估加工时间
    
    Args:
        gcode_program: G代码程序
    
    Returns:
        JSON格式的加工时间分析
    """
    if not gcode_program:
        return json.dumps({"error": "Empty G-code program"}, ensure_ascii=False)
    
    lines = gcode_program.strip().split('\n')
    
    total_time = 0.0
    rapid_time = 0.0
    cutting_time = 0.0
    rapid_distance = 0.0
    cutting_distance = 0.0
    
    current_feed = 1000  # 默认进给速度 mm/min
    current_position = {"x": 0, "y": 0, "z": 0}
    is_rapid = False
    
    for line in lines:
        stripped = line.strip()
        
        # 更新进给速度
        feed_match = re.search(r'F(\d+)', stripped)
        if feed_match:
            current_feed = int(feed_match.group(1))
        
        # 检测快速移动
        if stripped.startswith('G0') or stripped.startswith('G00'):
            is_rapid = True
            current_feed = 10000  # 假设快速移动速度
        elif stripped.startswith('G1') or stripped.startswith('G01'):
            is_rapid = False
        
        # 提取坐标
        new_position = current_position.copy()
        
        x_match = re.search(r'X(-?\d+\.?\d*)', stripped)
        y_match = re.search(r'Y(-?\d+\.?\d*)', stripped)
        z_match = re.search(r'Z(-?\d+\.?\d*)', stripped)
        
        if x_match:
            new_position["x"] = float(x_match.group(1))
        if y_match:
            new_position["y"] = float(y_match.group(1))
        if z_match:
            new_position["z"] = float(z_match.group(1))
        
        # 计算移动距离
        dx = new_position["x"] - current_position["x"]
        dy = new_position["y"] - current_position["y"]
        dz = new_position["z"] - current_position["z"]
        distance = (dx**2 + dy**2 + dz**2)**0.5
        
        if distance > 0:
            # 计算时间（分钟）
            move_time = distance / current_feed
            
            if is_rapid:
                rapid_time += move_time
                rapid_distance += distance
            else:
                cutting_time += move_time
                cutting_distance += distance
        
        current_position = new_position
    
    total_time = rapid_time + cutting_time
    
    result = {
        "total_time_minutes": round(total_time, 2),
        "total_time_formatted": format_time(total_time),
        "rapid_time_minutes": round(rapid_time, 2),
        "cutting_time_minutes": round(cutting_time, 2),
        "rapid_distance_mm": round(rapid_distance, 2),
        "cutting_distance_mm": round(cutting_distance, 2),
        "efficiency_metrics": {
            "cutting_ratio": round(cutting_time / total_time * 100, 1) if total_time > 0 else 0,
            "average_cutting_feed": round(cutting_distance / cutting_time) if cutting_time > 0 else 0
        },
        "optimization_suggestions": generate_time_optimization_suggestions(
            rapid_time, cutting_time, rapid_distance, cutting_distance
        )
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)


def format_time(minutes: float) -> str:
    """格式化时间显示"""
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    secs = int((minutes % 1) * 60)
    
    if hours > 0:
        return f"{hours}小时{mins}分{secs}秒"
    elif mins > 0:
        return f"{mins}分{secs}秒"
    else:
        return f"{secs}秒"


def generate_time_optimization_suggestions(rapid_time: float, cutting_time: float,
                                          rapid_distance: float, cutting_distance: float) -> List[str]:
    """生成时间优化建议"""
    suggestions = []
    
    total_time = rapid_time + cutting_time
    
    if total_time == 0:
        return ["无法分析时间"]
    
    rapid_ratio = rapid_time / total_time
    
    if rapid_ratio > 0.4:
        suggestions.append(f"空行程时间占比{rapid_ratio*100:.1f}%，建议优化刀具路径减少空行程")
    
    if cutting_time > 30:
        suggestions.append("加工时间较长，建议考虑使用更大直径刀具提高效率")
    
    if rapid_distance > cutting_distance:
        suggestions.append("空行程距离大于切削距离，建议重新规划加工顺序")
    
    if not suggestions:
        suggestions.append("加工参数合理，时间利用率良好")
    
    return suggestions


@tool
def validate_program_structure(gcode_program: str) -> str:
    """
    验证G代码程序结构的完整性
    
    Args:
        gcode_program: G代码程序
    
    Returns:
        JSON格式的结构验证结果
    """
    if not gcode_program:
        return json.dumps({"error": "Empty G-code program"}, ensure_ascii=False)
    
    lines = gcode_program.strip().split('\n')
    
    structure_checks = {
        "has_program_number": False,
        "has_coordinate_system": False,
        "has_tool_change": False,
        "has_spindle_control": False,
        "has_coolant_control": False,
        "has_tool_compensation": False,
        "has_program_end": False,
        "has_safety_height": False
    }
    
    program_info = {
        "program_number": None,
        "coordinate_system": None,
        "tools_used": [],
        "spindle_speeds": [],
        "feed_rates": []
    }
    
    for line in lines:
        stripped = line.strip()
        
        # 程序号
        if stripped.startswith('O'):
            program_match = re.match(r'O(\d+)', stripped)
            if program_match:
                structure_checks["has_program_number"] = True
                program_info["program_number"] = program_match.group(1)
        
        # 坐标系统
        if re.search(r'G5[4-9]', stripped):
            structure_checks["has_coordinate_system"] = True
            coord_match = re.search(r'(G5[4-9])', stripped)
            if coord_match:
                program_info["coordinate_system"] = coord_match.group(1)
        
        # 换刀
        if 'M6' in stripped or 'M06' in stripped:
            structure_checks["has_tool_change"] = True
            tool_match = re.search(r'T(\d+)', stripped)
            if tool_match:
                program_info["tools_used"].append(f"T{int(tool_match.group(1)):02d}")
        
        # 主轴控制
        if re.search(r'M[034]', stripped):
            structure_checks["has_spindle_control"] = True
        
        # 冷却液
        if re.search(r'M[89]', stripped):
            structure_checks["has_coolant_control"] = True
        
        # 刀具补偿
        if 'G43' in stripped:
            structure_checks["has_tool_compensation"] = True
        
        # 程序结束
        if re.search(r'M[230]', stripped):
            structure_checks["has_program_end"] = True
        
        # 安全高度
        z_match = re.search(r'Z(\d+\.?\d*)', stripped)
        if z_match:
            z_val = float(z_match.group(1))
            if z_val >= 20:
                structure_checks["has_safety_height"] = True
        
        # 提取转速和进给
        speed_match = re.search(r'S(\d+)', stripped)
        if speed_match:
            program_info["spindle_speeds"].append(int(speed_match.group(1)))
        
        feed_match = re.search(r'F(\d+)', stripped)
        if feed_match:
            program_info["feed_rates"].append(int(feed_match.group(1)))
    
    # 评估结构完整性
    missing_elements = [k for k, v in structure_checks.items() if not v]
    
    completeness_score = sum(structure_checks.values()) / len(structure_checks) * 100
    
    result = {
        "structure_complete": len(missing_elements) == 0,
        "completeness_score": round(completeness_score, 1),
        "structure_checks": structure_checks,
        "missing_elements": missing_elements,
        "program_info": {
            "program_number": program_info["program_number"],
            "coordinate_system": program_info["coordinate_system"],
            "tools_used": list(set(program_info["tools_used"])),
            "spindle_speeds": list(set(program_info["spindle_speeds"])),
            "feed_rates": list(set(program_info["feed_rates"]))
        },
        "recommendations": generate_structure_recommendations(missing_elements)
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)


def generate_structure_recommendations(missing: List[str]) -> List[str]:
    """生成结构完善建议"""
    recommendations = []
    
    element_names = {
        "has_program_number": "程序号",
        "has_coordinate_system": "坐标系统",
        "has_tool_change": "刀具更换",
        "has_spindle_control": "主轴控制",
        "has_coolant_control": "冷却液控制",
        "has_tool_compensation": "刀具补偿",
        "has_program_end": "程序结束指令",
        "has_safety_height": "安全高度"
    }
    
    for element in missing:
        name = element_names.get(element, element)
        recommendations.append(f"建议添加: {name}")
    
    if not recommendations:
        recommendations.append("程序结构完整，符合标准")
    
    return recommendations
