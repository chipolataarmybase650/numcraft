"""
路径规划工具集
用于生成刀具路径
"""
from typing import Dict, List, Any
from langchain.tools import tool
from tools.tool_helpers import parse_json_param
import json
import math
import logging

logger = logging.getLogger(__name__)


@tool
def generate_drilling_path(hole_features, tool_params) -> str:
    """
    生成钻孔路径
    
    Args:
        hole_features: JSON格式的孔特征信息
        tool_params: JSON格式的刀具参数
    
    Returns:
        JSON格式的钻孔路径
    """
    features = parse_json_param(hole_features, {"features": []})
    params = parse_json_param(tool_params, {})
    
    if isinstance(features, list):
        features = {"features": features}
    
    paths = []
    
    for feature in features.get("features", []):
        if feature.get("feature_type") != "hole":
            continue
        
        dimensions = feature.get("dimensions", {})
        position = feature.get("position", {})
        
        diameter = dimensions.get("diameter", 10)
        depth = dimensions.get("depth", 30)
        x = position.get("x", 0)
        y = position.get("y", 0)
        z_start = 5.0  # 安全高度
        
        # 钻孔路径点
        path_points = []
        
        # 快速定位到孔上方
        path_points.append({
            "x": x,
            "y": y,
            "z": z_start,
            "motion": "rapid",
            "description": "快速定位到孔上方"
        })
        
        # 钻孔进给
        path_points.append({
            "x": x,
            "y": y,
            "z": -depth,
            "motion": "feed",
            "description": f"钻孔深度 {depth}mm"
        })
        
        # 退刀
        path_points.append({
            "x": x,
            "y": y,
            "z": z_start,
            "motion": "rapid",
            "description": "退刀"
        })
        
        # 获取刀具参数
        tool_info = params.get("cutting_parameters", {})
        spindle_speed = tool_info.get("spindle_speed", 1000)
        feed_rate = tool_info.get("feed_rate", 100)
        
        path = {
            "feature_id": feature.get("feature_id"),
            "tool_id": params.get("tool_id"),
            "operation_type": "drilling",
            "path_points": path_points,
            "feed_rate": feed_rate,
            "spindle_speed": spindle_speed,
            "coolant": "flood",
            "dwell_time": 0.5,  # 底部停留时间
            "peck_depth": min(depth, 20),  # 啄钻深度
            "notes": f"直径{diameter}mm，深{depth}mm的孔"
        }
        
        paths.append(path)
    
    result = {
        "drilling_paths": paths,
        "total_holes": len(paths),
        "estimated_time": sum(len(p["path_points"]) * 0.5 for p in paths)
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def generate_milling_path(feature: str, tool_params: str, operation_type: str) -> str:
    """
    生成铣削路径（粗加工或精加工）
    
    Args:
        feature: JSON格式的特征信息
        tool_params: JSON格式的刀具参数
        operation_type: 操作类型 (rough/finish)
    
    Returns:
        JSON格式的铣削路径
    """
    try:
        feature_data = json.loads(feature)
        params = json.loads(tool_params)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON input"}, ensure_ascii=False)
    
    feature_type = feature_data.get("feature_type")
    dimensions = feature_data.get("dimensions", {})
    position = feature_data.get("position", {})
    
    tool_diameter = params.get("diameter", 10)
    cutting_params = params.get("cutting_parameters", {})
    
    path_points = []
    
    if feature_type == "slot":
        # 槽加工路径
        length = dimensions.get("length", 50)
        width = dimensions.get("width", 20)
        depth = dimensions.get("depth", 10)
        
        x_start = position.get("x", 0)
        y_start = position.get("y", 0)
        
        if operation_type == "rough":
            # 粗加工：Zig-Zag路径
            stepover = tool_diameter * 0.7  # 步距
            current_z = 0
            z_step = cutting_params.get("axial_depth", 3)
            
            while current_z > -depth:
                current_z = max(current_z - z_step, -depth)
                
                # 计算每层的路径
                y_current = y_start
                direction = 1
                pass_count = 0
                
                while y_current < y_start + width:
                    if direction == 1:
                        path_points.append({
                            "x": x_start,
                            "y": y_current,
                            "z": current_z,
                            "motion": "feed",
                            "description": f"层高{abs(current_z):.1f}mm，第{pass_count+1}刀"
                        })
                        path_points.append({
                            "x": x_start + length,
                            "y": y_current,
                            "z": current_z,
                            "motion": "feed",
                            "description": "铣削"
                        })
                    else:
                        path_points.append({
                            "x": x_start + length,
                            "y": y_current,
                            "z": current_z,
                            "motion": "feed",
                            "description": f"层高{abs(current_z):.1f}mm，第{pass_count+1}刀"
                        })
                        path_points.append({
                            "x": x_start,
                            "y": y_current,
                            "z": current_z,
                            "motion": "feed",
                            "description": "铣削"
                        })
                    
                    y_current += stepover
                    direction *= -1
                    pass_count += 1
        
        else:  # finish
            # 精加工：轮廓路径
            # 四个角落
            corners = [
                (x_start, y_start),
                (x_start + length, y_start),
                (x_start + length, y_start + width),
                (x_start, y_start + width),
            ]
            
            # 从安全高度开始
            path_points.append({
                "x": corners[0][0],
                "y": corners[0][1],
                "z": 5,
                "motion": "rapid",
                "description": "快速定位"
            })
            
            # 下刀
            path_points.append({
                "x": corners[0][0],
                "y": corners[0][1],
                "z": -depth,
                "motion": "feed",
                "description": "下刀到加工深度"
            })
            
            # 沿轮廓铣削
            for i, (x, y) in enumerate(corners):
                path_points.append({
                    "x": x,
                    "y": y,
                    "z": -depth,
                    "motion": "feed",
                    "description": f"轮廓第{i+1}边"
                })
            
            # 回到起点
            path_points.append({
                "x": corners[0][0],
                "y": corners[0][1],
                "z": -depth,
                "motion": "feed",
                "description": "闭合轮廓"
            })
    
    elif feature_type == "pocket":
        # 型腔加工路径
        length = dimensions.get("length", 50)
        width = dimensions.get("width", 40)
        depth = dimensions.get("depth", 15)
        
        x_center = position.get("x", 0) + length / 2
        y_center = position.get("y", 0) + width / 2
        
        if operation_type == "rough":
            # 螺旋铣削路径
            current_z = 0
            z_step = cutting_params.get("axial_depth", 3)
            
            while current_z > -depth:
                current_z = max(current_z - z_step, -depth)
                
                # 从中心向外螺旋
                spiral_points = generate_spiral_path(
                    x_center, y_center, current_z,
                    min(length, width) / 2 - tool_diameter,
                    tool_diameter * 0.7
                )
                path_points.extend(spiral_points)
        
        else:  # finish
            # 轮廓精加工
            path_points.append({
                "x": x_center - length/2,
                "y": y_center - width/2,
                "z": 5,
                "motion": "rapid",
                "description": "快速定位"
            })
            
            path_points.append({
                "x": x_center - length/2,
                "y": y_center - width/2,
                "z": -depth,
                "motion": "feed",
                "description": "下刀"
            })
            
            # 轮廓路径
            contour = [
                (x_center - length/2, y_center - width/2),
                (x_center + length/2, y_center - width/2),
                (x_center + length/2, y_center + width/2),
                (x_center - length/2, y_center + width/2),
            ]
            
            for x, y in contour:
                path_points.append({
                    "x": x,
                    "y": y,
                    "z": -depth,
                    "motion": "feed",
                    "description": "轮廓精加工"
                })
    
    elif feature_type == "contour":
        # 外轮廓加工
        # 简化为矩形轮廓
        length = dimensions.get("length", 100)
        width = dimensions.get("width", 60)
        
        # 从安全高度开始
        path_points.append({
            "x": 0,
            "y": 0,
            "z": 5,
            "motion": "rapid",
            "description": "安全高度"
        })
        
        # 下刀
        path_points.append({
            "x": 0,
            "y": 0,
            "z": -1,
            "motion": "feed",
            "description": "下刀"
        })
        
        # 轮廓路径
        contour_points = [
            (0, 0), (length, 0), (length, width), (0, width), (0, 0)
        ]
        
        for x, y in contour_points:
            path_points.append({
                "x": x,
                "y": y,
                "z": -1,
                "motion": "feed",
                "description": "外轮廓"
            })
    
    result = {
        "feature_id": feature_data.get("feature_id"),
        "tool_id": params.get("tool_id"),
        "operation_type": operation_type,
        "path_points": path_points,
        "feed_rate": cutting_params.get("feed_rate", 500),
        "spindle_speed": cutting_params.get("spindle_speed", 3000),
        "coolant": "flood",
        "total_points": len(path_points),
        "estimated_length": calculate_path_length(path_points)
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)


def generate_spiral_path(x_center: float, y_center: float, z: float, 
                         max_radius: float, stepover: float) -> List[Dict]:
    """生成螺旋路径"""
    points = []
    angle = 0
    radius = 0
    angle_increment = math.pi / 18  # 10度
    
    while radius < max_radius:
        x = x_center + radius * math.cos(angle)
        y = y_center + radius * math.sin(angle)
        
        points.append({
            "x": round(x, 3),
            "y": round(y, 3),
            "z": z,
            "motion": "feed",
            "description": "螺旋路径"
        })
        
        angle += angle_increment
        radius += stepover * angle_increment / (2 * math.pi)
    
    return points


def calculate_path_length(points: List[Dict]) -> float:
    """计算路径总长度"""
    total_length = 0.0
    
    for i in range(1, len(points)):
        dx = points[i]["x"] - points[i-1]["x"]
        dy = points[i]["y"] - points[i-1]["y"]
        dz = points[i]["z"] - points[i-1]["z"]
        total_length += math.sqrt(dx**2 + dy**2 + dz**2)
    
    return round(total_length, 2)


@tool
def optimize_path_sequence(paths: str) -> str:
    """
    优化刀具路径顺序以减少空行程
    
    Args:
        paths: JSON格式的路径列表
    
    Returns:
        JSON格式的优化后的路径
    """
    try:
        paths_data = json.loads(paths)
        path_list = paths_data.get("tool_paths", paths_data.get("drilling_paths", []))
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON input"}, ensure_ascii=False)
    
    if len(path_list) <= 1:
        return json.dumps({
            "optimized_paths": path_list,
            "optimization_rate": 0,
            "notes": "无需优化"
        }, ensure_ascii=False)
    
    # 最近邻算法优化路径顺序
    optimized_paths = [path_list[0]]
    remaining_paths = path_list[1:]
    
    while remaining_paths:
        current_end = get_path_end(optimized_paths[-1])
        
        # 找最近的下一个路径起点
        min_distance = float('inf')
        nearest_idx = 0
        
        for i, path in enumerate(remaining_paths):
            next_start = get_path_start(path)
            distance = calculate_distance(current_end, next_start)
            
            if distance < min_distance:
                min_distance = distance
                nearest_idx = i
        
        optimized_paths.append(remaining_paths.pop(nearest_idx))
    
    # 计算优化效果
    original_distance = calculate_total_distance(path_list)
    optimized_distance = calculate_total_distance(optimized_paths)
    optimization_rate = (original_distance - optimized_distance) / original_distance * 100 if original_distance > 0 else 0
    
    result = {
        "optimized_paths": optimized_paths,
        "original_distance": round(original_distance, 2),
        "optimized_distance": round(optimized_distance, 2),
        "optimization_rate": round(optimization_rate, 2),
        "notes": f"路径优化减少了 {round(optimization_rate, 1)}% 的空行程"
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)


def get_path_start(path: Dict) -> tuple:
    """获取路径起点"""
    points = path.get("path_points", [])
    if points:
        return (points[0]["x"], points[0]["y"])
    return (0, 0)


def get_path_end(path: Dict) -> tuple:
    """获取路径终点"""
    points = path.get("path_points", [])
    if points:
        return (points[-1]["x"], points[-1]["y"])
    return (0, 0)


def calculate_distance(point1: tuple, point2: tuple) -> float:
    """计算两点间距离"""
    return math.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)


def calculate_total_distance(paths: List[Dict]) -> float:
    """计算路径总距离（包括空行程）"""
    total_distance = 0.0
    
    for i, path in enumerate(paths):
        points = path.get("path_points", [])
        
        # 加工距离
        for j in range(1, len(points)):
            total_distance += calculate_distance(
                (points[j-1]["x"], points[j-1]["y"]),
                (points[j]["x"], points[j]["y"])
            )
        
        # 到下一个路径的空行程
        if i < len(paths) - 1:
            next_start = get_path_start(paths[i+1])
            current_end = get_path_end(path)
            total_distance += calculate_distance(current_end, next_start)
    
    return total_distance
