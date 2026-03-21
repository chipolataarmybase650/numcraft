"""
G代码生成工具集
用于生成标准G代码程序
"""
from typing import Dict, List, Any
from langchain.tools import tool
from tools.tool_helpers import parse_json_param
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


# G代码模板
GCODE_TEMPLATES = {
    "header": """%
O{program_number}
(程序名称: {program_name})
(创建时间: {timestamp})
(材料: {material})
(工件尺寸: {workpiece_size})
(刀具总数: {tool_count})
(预计时间: {estimated_time}分钟)
{comment}
G90 G54 G17 G40 G49 G80
G28 G91 Z0
T{tool_number} M6
G43 H{tool_number} Z50.
S{spindle_speed} M3
G0 X{x} Y{y}
Z5.
""",
    "drilling": """G0 X{x} Y{y}
G0 Z{clearance}
G83 X{x} Y{y} Z{depth} R{retract} Q{peck} F{feed_rate}
G0 Z{clearance}
""",
    "milling_rapid": "G0 X{x:.3f} Y{y:.3f} Z{z:.3f}\n",
    "milling_feed": "G1 X{x:.3f} Y{y:.3f} Z{z:.3f} F{feed_rate}\n",
    "arc_cw": "G2 X{x:.3f} Y{y:.3f} I{i:.3f} J{j:.3f} F{feed_rate}\n",
    "arc_ccw": "G3 X{x:.3f} Y{y:.3f} I{i:.3f} J{j:.3f} F{feed_rate}\n",
    "footer": """G0 Z50.
M5
G28 G91 Z0
M30
%
"""
}


@tool
def generate_gcode_program(tool_paths, program_info) -> str:
    """
    根据刀具路径生成完整的G代码程序
    
    Args:
        tool_paths: JSON格式的刀具路径数据
        program_info: JSON格式的程序信息
    
    Returns:
        完整的G代码程序字符串
    """
    paths_data = parse_json_param(tool_paths, {"tool_paths": []})
    info = parse_json_param(program_info, {})
    
    # 获取路径列表
    if isinstance(paths_data, list):
        path_list = paths_data
    else:
        path_list = paths_data.get("optimized_paths", paths_data.get("tool_paths", paths_data.get("drilling_paths", [])))
    
    if not path_list:
        return json.dumps({"error": "No tool paths provided"}, ensure_ascii=False)
    
    gcode_lines = []
    
    # 程序头
    gcode_lines.append(generate_program_header(info))
    
    # 按刀具分组
    tool_groups = group_paths_by_tool(path_list)
    
    # 生成每个刀具的G代码
    for tool_id, paths in tool_groups.items():
        gcode_lines.append(f"\n(--- 刀具 {tool_id} ---)")
        
        for path in paths:
            gcode_lines.append(generate_path_gcode(path))
    
    # 程序尾
    gcode_lines.append(GCODE_TEMPLATES["footer"])
    
    gcode_program = "".join(gcode_lines)
    
    result = {
        "gcode_program": gcode_program,
        "program_number": info.get("program_number", "0001"),
        "total_lines": len(gcode_lines),
        "total_tools": len(tool_groups),
        "file_size": len(gcode_program),
        "generation_time": datetime.now().isoformat(),
        "compatible_systems": ["FANUC", "SIEMENS", "MAZAK", "HAAS"]
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)


def generate_program_header(info: Dict) -> str:
    """生成程序头"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    header = f"""%
O{info.get('program_number', '0001')}
(程序名称: {info.get('program_name', 'CNC_MACHINING')})
(创建时间: {timestamp})
(材料: {info.get('material', 'Unknown')})
(工件尺寸: {info.get('workpiece_size', 'N/A')})
(刀具总数: {info.get('tool_count', 0)})
(预计时间: {info.get('estimated_time', 0)}分钟)
(生成系统: Multi-Agent G-Code Generator)
(G代码标准: FANUC / ISO)

(初始化)
G90 G54 G17          (绝对坐标, 工件坐标系G54, XY平面)
G40 G49 G80          (取消刀补, 取消长度补偿, 取消固定循环)
G28 G91 Z0           (Z轴回零)
"""
    
    return header


def group_paths_by_tool(paths: List[Dict]) -> Dict[str, List[Dict]]:
    """按刀具分组路径"""
    tool_groups = {}
    
    for path in paths:
        tool_id = path.get("tool_id", "T01")
        
        if tool_id not in tool_groups:
            tool_groups[tool_id] = []
        
        tool_groups[tool_id].append(path)
    
    return tool_groups


def generate_path_gcode(path: Dict) -> str:
    """为单个路径生成G代码"""
    gcode_lines = []
    
    tool_id = path.get("tool_id", "T01")
    operation_type = path.get("operation_type", "milling")
    path_points = path.get("path_points", [])
    feed_rate = path.get("feed_rate", 500)
    spindle_speed = path.get("spindle_speed", 3000)
    
    # 刀具换刀
    tool_number = int(tool_id.replace("T", ""))
    gcode_lines.append(f"""
(操作: {operation_type})
(刀具: {tool_id})
T{tool_number:02d} M6               (换刀)
G43 H{tool_number:02d} Z50.         (刀具长度补偿)
S{spindle_speed} M3                 (主轴正转)
M8                                 (冷却液开)
""")
    
    # 生成路径点
    for i, point in enumerate(path_points):
        x = point.get("x", 0)
        y = point.get("y", 0)
        z = point.get("z", 0)
        motion = point.get("motion", "feed")
        description = point.get("description", "")
        
        # 添加注释
        if description and i % 5 == 0:  # 每5个点添加一次注释
            gcode_lines.append(f"({description})\n")
        
        # 生成移动指令
        if motion == "rapid":
            gcode_lines.append(GCODE_TEMPLATES["milling_rapid"].format(x=x, y=y, z=z))
        else:
            gcode_lines.append(GCODE_TEMPLATES["milling_feed"].format(
                x=x, y=y, z=z, feed_rate=feed_rate
            ))
    
    # 安全高度
    gcode_lines.append(f"""
G0 Z50.               (安全高度)
M5                    (主轴停止)
M9                    (冷却液关)
""")
    
    return "".join(gcode_lines)


@tool
def optimize_gcode(gcode_program: str) -> str:
    """
    优化G代码以提高执行效率
    
    Args:
        gcode_program: G代码程序字符串
    
    Returns:
        JSON格式的优化结果
    """
    if not gcode_program:
        return json.dumps({"error": "Empty G-code program"}, ensure_ascii=False)
    
    original_lines = gcode_program.strip().split('\n')
    optimized_lines = []
    
    # 优化策略
    optimizations = {
        "removed_redundant_moves": 0,
        "merged_rapid_moves": 0,
        "optimized_feed_rates": 0,
        "removed_empty_lines": 0
    }
    
    prev_line = None
    prev_motion = None
    
    for line in original_lines:
        stripped = line.strip()
        
        # 移除空行
        if not stripped:
            optimizations["removed_empty_lines"] += 1
            continue
        
        # 移除冗余的G0移动
        if stripped.startswith('G0 ') or stripped.startswith('G00 '):
            if prev_motion == 'G0':
                # 检查是否连续的快速移动到相同位置
                optimizations["removed_redundant_moves"] += 1
            prev_motion = 'G0'
        
        # 检测连续的G1移动，可以合并
        elif stripped.startswith('G1 ') or stripped.startswith('G01 '):
            prev_motion = 'G1'
        
        optimized_lines.append(line)
        prev_line = stripped
    
    optimized_program = '\n'.join(optimized_lines)
    
    result = {
        "optimized_gcode": optimized_program,
        "original_lines": len(original_lines),
        "optimized_lines": len(optimized_lines),
        "reduction_percentage": round((len(original_lines) - len(optimized_lines)) / len(original_lines) * 100, 2) if original_lines else 0,
        "optimizations_applied": optimizations,
        "notes": "G代码优化完成"
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def convert_to_fanuc_gcode(gcode_program: str) -> str:
    """
    将G代码转换为FANUC格式
    
    Args:
        gcode_program: 通用G代码程序
    
    Returns:
        JSON格式的FANUC G代码
    """
    if not gcode_program:
        return json.dumps({"error": "Empty G-code program"}, ensure_ascii=False)
    
    # FANUC特定的转换规则
    fanuc_gcode = gcode_program
    
    # 确保使用FANUC标准的G代码
    conversions = {
        "G0 ": "G00 ",  # 快速定位
        "G1 ": "G01 ",  # 直线插补
        "G2 ": "G02 ",  # 顺圆插补
        "G3 ": "G03 ",  # 逆圆插补
    }
    
    for old, new in conversions.items():
        fanuc_gcode = fanuc_gcode.replace(old, new)
    
    # 添加FANUC特定的预处理
    fanuc_header = """%
(FANUC格式G代码)
(兼容系统: FANUC 0i/18i/21i/30i)
"""
    
    fanuc_gcode = fanuc_header + fanuc_gcode
    
    result = {
        "fanuc_gcode": fanuc_gcode,
        "compatible_models": [
            "FANUC 0i-TF",
            "FANUC 0i-MF",
            "FANUC 18i-TB",
            "FANUC 18i-MB",
            "FANUC 21i-TB",
            "FANUC 21i-MB",
            "FANUC 30i-TB",
            "FANUC 30i-MB"
        ],
        "conversion_notes": "已添加FANUC特定的G代码和格式"
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def generate_gcode_documentation(gcode_program: str) -> str:
    """
    为G代码生成详细的文档说明
    
    Args:
        gcode_program: G代码程序
    
    Returns:
        JSON格式的文档
    """
    if not gcode_program:
        return json.dumps({"error": "Empty G-code program"}, ensure_ascii=False)
    
    lines = gcode_program.strip().split('\n')
    
    # 分析G代码
    analysis = {
        "total_lines": len(lines),
        "coordinate_systems": [],
        "tools_used": [],
        "operations": [],
        "feed_rates": [],
        "spindle_speeds": [],
        "warnings": []
    }
    
    for line in lines:
        stripped = line.strip()
        
        # 提取坐标系统
        if 'G54' in stripped:
            analysis["coordinate_systems"].append("G54")
        elif 'G55' in stripped:
            analysis["coordinate_systems"].append("G55")
        
        # 提取刀具信息
        if stripped.startswith('T') and 'M6' in stripped:
            tool_num = stripped.split()[0]
            analysis["tools_used"].append(tool_num)
        
        # 提取进给速度
        if 'F' in stripped:
            import re
            feed_match = re.search(r'F(\d+)', stripped)
            if feed_match:
                feed_rate = int(feed_match.group(1))
                if feed_rate not in analysis["feed_rates"]:
                    analysis["feed_rates"].append(feed_rate)
        
        # 提取主轴转速
        if 'S' in stripped:
            import re
            speed_match = re.search(r'S(\d+)', stripped)
            if speed_match:
                speed = int(speed_match.group(1))
                if speed not in analysis["spindle_speeds"]:
                    analysis["spindle_speeds"].append(speed)
        
        # 检测操作类型
        if 'G83' in stripped or 'drilling' in stripped.lower():
            analysis["operations"].append("钻孔")
        elif 'G01' in stripped or 'G1 ' in stripped:
            if "铣削" not in analysis["operations"]:
                analysis["operations"].append("铣削")
        
        # 警告检测
        if stripped.startswith('G0') and 'F' in stripped:
            analysis["warnings"].append("快速移动中设置了进给速度（将被忽略）")
    
    # 生成文档
    documentation = f"""
# G代码程序文档

## 程序概览
- 总行数: {analysis['total_lines']}
- 使用刀具: {', '.join(analysis['tools_used']) if analysis['tools_used'] else '未指定'}
- 加工操作: {', '.join(analysis['operations']) if analysis['operations'] else '未识别'}

## 参数设置
- 坐标系统: {', '.join(set(analysis['coordinate_systems'])) if analysis['coordinate_systems'] else 'G54'}
- 进给速度范围: {min(analysis['feed_rates']) if analysis['feed_rates'] else 0} - {max(analysis['feed_rates']) if analysis['feed_rates'] else 0} mm/min
- 主轴转速范围: {min(analysis['spindle_speeds']) if analysis['spindle_speeds'] else 0} - {max(analysis['spindle_speeds']) if analysis['spindle_speeds'] else 0} RPM

## 安全提示
{chr(10).join('- ' + w for w in analysis['warnings']) if analysis['warnings'] else '- 未检测到明显问题'}

## 使用说明
1. 检查刀具是否安装正确
2. 确认工件夹紧牢固
3. 设置正确的工件坐标系
4. 首次运行建议单段执行
5. 注意观察切削状态
"""
    
    result = {
        "documentation": documentation,
        "analysis": analysis,
        "generated_at": datetime.now().isoformat()
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)
