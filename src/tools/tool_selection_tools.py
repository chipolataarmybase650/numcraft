"""
刀具选择工具集
用于刀具推荐和切削参数计算
"""
from typing import Dict, List, Any
from langchain.tools import tool
import json
import logging

logger = logging.getLogger(__name__)


# 刀具数据库
TOOL_DATABASE = {
    "end_mill": {
        "standard": [
            {"diameter": 6, "flute_count": 3, "material": "硬质合金", "coating": "TiAlN", "max_depth": 24},
            {"diameter": 8, "flute_count": 4, "material": "硬质合金", "coating": "TiAlN", "max_depth": 32},
            {"diameter": 10, "flute_count": 4, "material": "硬质合金", "coating": "TiAlN", "max_depth": 40},
            {"diameter": 12, "flute_count": 4, "material": "硬质合金", "coating": "TiAlN", "max_depth": 48},
            {"diameter": 16, "flute_count": 4, "material": "硬质合金", "coating": "TiAlN", "max_depth": 64},
            {"diameter": 20, "flute_count": 4, "material": "硬质合金", "coating": "TiAlN", "max_depth": 80},
        ],
        "ball_nose": [
            {"diameter": 6, "flute_count": 2, "material": "硬质合金", "coating": "TiAlN"},
            {"diameter": 8, "flute_count": 2, "material": "硬质合金", "coating": "TiAlN"},
            {"diameter": 10, "flute_count": 2, "material": "硬质合金", "coating": "TiAlN"},
        ]
    },
    "drill": {
        "standard": [
            {"diameter": 3, "material": "高速钢", "coating": "TiN", "max_depth": 30},
            {"diameter": 5, "material": "硬质合金", "coating": "TiAlN", "max_depth": 50},
            {"diameter": 8, "material": "硬质合金", "coating": "TiAlN", "max_depth": 80},
            {"diameter": 10, "material": "硬质合金", "coating": "TiAlN", "max_depth": 100},
            {"diameter": 12, "material": "硬质合金", "coating": "TiAlN", "max_depth": 120},
            {"diameter": 15, "material": "硬质合金", "coating": "TiAlN", "max_depth": 150},
            {"diameter": 20, "material": "硬质合金", "coating": "TiAlN", "max_depth": 200},
        ],
        "center_drill": [
            {"diameter": 3, "material": "高速钢", "coating": "TiN"},
            {"diameter": 5, "material": "高速钢", "coating": "TiN"},
        ]
    },
    "reamer": {
        "standard": [
            {"diameter": 6, "material": "硬质合金", "coating": "TiAlN"},
            {"diameter": 8, "material": "硬质合金", "coating": "TiAlN"},
            {"diameter": 10, "material": "硬质合金", "coating": "TiAlN"},
            {"diameter": 12, "material": "硬质合金", "coating": "TiAlN"},
            {"diameter": 15, "material": "硬质合金", "coating": "TiAlN"},
            {"diameter": 20, "material": "硬质合金", "coating": "TiAlN"},
        ]
    },
    "tap": {
        "metric": [
            {"size": "M6", "pitch": 1.0, "material": "高速钢", "coating": "TiN"},
            {"size": "M8", "pitch": 1.25, "material": "高速钢", "coating": "TiN"},
            {"size": "M10", "pitch": 1.5, "material": "高速钢", "coating": "TiN"},
            {"size": "M12", "pitch": 1.75, "material": "高速钢", "coating": "TiN"},
        ]
    }
}

# 切削参数数据库（基于材料和刀具）
CUTTING_PARAMETERS = {
    "铝合金": {
        "end_mill": {
            "vc_range": (200, 400),  # 切削速度范围 m/min
            "fz_range": (0.05, 0.15),  # 每齿进给量 mm/tooth
            "ae_max": 0.7,  # 最大径向切深（刀具直径的倍数）
            "ap_max": 2.0,  # 最大轴向切深（刀具直径的倍数）
        },
        "drill": {
            "vc_range": (80, 150),
            "f_range": (0.1, 0.3),  # 每转进给量 mm/rev
        }
    },
    "钢": {
        "end_mill": {
            "vc_range": (80, 150),
            "fz_range": (0.03, 0.1),
            "ae_max": 0.5,
            "ap_max": 1.5,
        },
        "drill": {
            "vc_range": (40, 80),
            "f_range": (0.05, 0.15),
        }
    },
    "不锈钢": {
        "end_mill": {
            "vc_range": (60, 120),
            "fz_range": (0.02, 0.08),
            "ae_max": 0.4,
            "ap_max": 1.0,
        },
        "drill": {
            "vc_range": (30, 60),
            "f_range": (0.03, 0.1),
        }
    }
}


@tool
def select_tools_for_features(features, material: str) -> str:
    """
    根据特征和材料选择合适的刀具
    
    Args:
        features: JSON格式的特征列表或特征列表对象
        material: 材料信息
    
    Returns:
        JSON格式的刀具清单
    """
    # 处理不同类型的输入
    if isinstance(features, str):
        try:
            features_data = json.loads(features)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON input"}, ensure_ascii=False)
    elif isinstance(features, list):
        features_data = features
    elif isinstance(features, dict):
        features_data = features.get("features", [])
    else:
        return json.dumps({"error": f"Invalid features type: {type(features)}"}, ensure_ascii=False)
    
    # 如果features_data是字典，提取features列表
    if isinstance(features_data, dict):
        feature_list = features_data.get("features", [])
    else:
        feature_list = features_data
    
    tool_list = []
    tool_id = 1
    
    # 材料关键词匹配
    material_key = None
    for key in CUTTING_PARAMETERS.keys():
        if key in material:
            material_key = key
            break
    
    if not material_key:
        material_key = "钢"  # 默认
    
    for feature in feature_list:
        feature_type = feature.get("feature_type")
        dimensions = feature.get("dimensions", {})
        operations = feature.get("operations", [])
        
        # 根据特征类型选择刀具
        if feature_type == "hole":
            diameter = dimensions.get("diameter", 10)
            
            # 选择钻头
            drill_diameters = [t["diameter"] for t in TOOL_DATABASE["drill"]["standard"]]
            closest_diameter = min(drill_diameters, key=lambda x: abs(x - diameter))
            
            drill_tool = next(t for t in TOOL_DATABASE["drill"]["standard"] if t["diameter"] == closest_diameter)
            
            tool_list.append({
                "tool_id": f"T{tool_id:02d}",
                "tool_type": "drill",
                "diameter": drill_tool["diameter"],
                "length": drill_tool.get("max_depth", 100),
                "material": drill_tool["material"],
                "flute_count": 2,
                "coating": drill_tool.get("coating", ""),
                "feature_id": feature.get("feature_id"),
                "operation": "drilling",
                "cutting_parameters": calculate_cutting_params("drill", drill_tool["diameter"], material_key)
            })
            tool_id += 1
            
            # 如果需要铰孔
            if "reaming" in operations:
                reamer_diameters = [t["diameter"] for t in TOOL_DATABASE["reamer"]["standard"]]
                if diameter in reamer_diameters:
                    tool_list.append({
                        "tool_id": f"T{tool_id:02d}",
                        "tool_type": "reamer",
                        "diameter": diameter,
                        "length": 100,
                        "material": "硬质合金",
                        "flute_count": 6,
                        "coating": "TiAlN",
                        "feature_id": feature.get("feature_id"),
                        "operation": "reaming",
                        "cutting_parameters": calculate_cutting_params("reamer", diameter, material_key)
                    })
                    tool_id += 1
        
        elif feature_type in ["slot", "pocket", "contour"]:
            # 槽加工选择立铣刀
            width = dimensions.get("width", 10)
            length = dimensions.get("length", 50)
            
            # 选择刀具直径（通常小于槽宽）
            tool_diameter = min(width * 0.75, 20)
            
            # 选择最接近的标准直径
            end_mill_diameters = [t["diameter"] for t in TOOL_DATABASE["end_mill"]["standard"]]
            closest_diameter = min(end_mill_diameters, key=lambda x: abs(x - tool_diameter))
            
            mill_tool = next(t for t in TOOL_DATABASE["end_mill"]["standard"] if t["diameter"] == closest_diameter)
            
            # 粗加工刀具
            tool_list.append({
                "tool_id": f"T{tool_id:02d}",
                "tool_type": "end_mill",
                "diameter": mill_tool["diameter"],
                "length": mill_tool.get("max_depth", 40),
                "material": mill_tool["material"],
                "flute_count": mill_tool["flute_count"],
                "coating": mill_tool["coating"],
                "feature_id": feature.get("feature_id"),
                "operation": "rough_milling",
                "cutting_parameters": calculate_cutting_params("end_mill", mill_tool["diameter"], material_key, is_rough=True)
            })
            tool_id += 1
            
            # 精加工刀具（更小的刀具或更高质量）
            tool_list.append({
                "tool_id": f"T{tool_id:02d}",
                "tool_type": "end_mill",
                "diameter": closest_diameter,
                "length": mill_tool.get("max_depth", 40),
                "material": mill_tool["material"],
                "flute_count": mill_tool["flute_count"],
                "coating": mill_tool["coating"],
                "feature_id": feature.get("feature_id"),
                "operation": "finish_milling",
                "cutting_parameters": calculate_cutting_params("end_mill", closest_diameter, material_key, is_rough=False)
            })
            tool_id += 1
    
    result = {
        "tool_list": tool_list,
        "total_tools": len(tool_list),
        "material": material,
        "selection_notes": "刀具选择基于特征尺寸、材料特性和加工要求"
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)


def calculate_cutting_params(tool_type: str, diameter: float, material: str, is_rough: bool = True) -> Dict[str, float]:
    """
    计算切削参数
    
    Args:
        tool_type: 刀具类型
        diameter: 刀具直径
        material: 材料类型
        is_rough: 是否为粗加工
    
    Returns:
        切削参数字典
    """
    if material not in CUTTING_PARAMETERS:
        material = "钢"  # 默认
    
    params = CUTTING_PARAMETERS[material].get(tool_type, CUTTING_PARAMETERS[material]["end_mill"])
    
    if tool_type == "drill":
        vc_min, vc_max = params["vc_range"]
        f_min, f_max = params["f_range"]
        
        # 选择中间值
        vc = (vc_min + vc_max) / 2
        f = (f_min + f_max) / 2
        
        # 计算转速和进给
        n = (vc * 1000) / (3.14159 * diameter)  # RPM
        feed_rate = f * n  # mm/min
        
        return {
            "spindle_speed": round(n),
            "feed_rate": round(feed_rate),
            "plunge_rate": round(feed_rate * 0.5),
            "cutting_speed": vc,
            "notes": "钻孔参数"
        }
    
    else:  # end_mill
        vc_min, vc_max = params["vc_range"]
        fz_min, fz_max = params["fz_range"]
        ae_max = params["ae_max"]
        ap_max = params["ap_max"]
        
        # 粗加工使用较低参数，精加工使用较高参数
        if is_rough:
            vc = (vc_min + vc_max) / 2 * 0.8
            fz = (fz_min + fz_max) / 2 * 1.2
            ae = diameter * ae_max * 0.8
            ap = diameter * ap_max * 0.8
        else:
            vc = (vc_min + vc_max) / 2 * 1.2
            fz = (fz_min + fz_max) / 2 * 0.6
            ae = diameter * ae_max * 0.3
            ap = diameter * ap_max * 0.3
        
        # 计算转速和进给
        n = (vc * 1000) / (3.14159 * diameter)
        
        # 假设4齿铣刀
        flute_count = 4
        feed_rate = fz * n * flute_count
        
        return {
            "spindle_speed": round(n),
            "feed_rate": round(feed_rate),
            "plunge_rate": round(feed_rate * 0.3),
            "cutting_speed": vc,
            "radial_depth": round(ae, 2),
            "axial_depth": round(ap, 2),
            "feed_per_tooth": fz,
            "notes": "粗加工参数" if is_rough else "精加工参数"
        }


@tool
def optimize_cutting_parameters(tool_list: str, material: str) -> str:
    """
    优化切削参数以提高加工效率和质量
    
    Args:
        tool_list: JSON格式的刀具清单
        material: 材料信息
    
    Returns:
        JSON格式的优化后的切削参数
    """
    try:
        tools_data = json.loads(tool_list)
        tools = tools_data.get("tool_list", [])
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON input"}, ensure_ascii=False)
    
    optimized_tools = []
    total_mrr = 0.0  # 材料去除率
    
    for tool in tools:
        optimized_tool = tool.copy()
        params = tool.get("cutting_parameters", {})
        
        # 计算材料去除率（MRR）
        if tool["tool_type"] == "end_mill":
            ae = params.get("radial_depth", tool["diameter"] * 0.5)
            ap = params.get("axial_depth", tool["diameter"] * 1.0)
            vf = params.get("feed_rate", 500)
            mrr = ae * ap * vf  # mm³/min
            
            optimized_tool["material_removal_rate"] = round(mrr, 2)
            total_mrr += mrr
            
            # 优化建议
            suggestions = []
            if mrr < 5000:
                suggestions.append("可适当增加切深以提高效率")
            if params.get("feed_rate", 0) < 300:
                suggestions.append("进给速度偏低，可适当提高")
            
            optimized_tool["optimization_suggestions"] = suggestions
        
        elif tool["tool_type"] == "drill":
            # 钻孔效率评估
            diameter = tool["diameter"]
            feed = params.get("feed_rate", 100)
            efficiency = (diameter ** 2 * 3.14159 / 4) * feed / 1000
            
            optimized_tool["drilling_efficiency"] = round(efficiency, 2)
        
        optimized_tools.append(optimized_tool)
    
    result = {
        "optimized_tool_list": optimized_tools,
        "total_material_removal_rate": round(total_mrr, 2),
        "efficiency_grade": "高" if total_mrr > 20000 else "中" if total_mrr > 10000 else "低",
        "optimization_notes": "参数优化基于材料去除率和加工稳定性"
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def check_tool_interference(tool_list: str, workpiece_dimensions: str) -> str:
    """
    检查刀具干涉情况
    
    Args:
        tool_list: JSON格式的刀具清单
        workpiece_dimensions: JSON格式的工作尺寸
    
    Returns:
        JSON格式的干涉检查结果
    """
    try:
        tools = json.loads(tool_list).get("tool_list", [])
        workpiece = json.loads(workpiece_dimensions) if workpiece_dimensions else {}
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON input"}, ensure_ascii=False)
    
    issues = []
    warnings = []
    
    for tool in tools:
        tool_diameter = tool.get("diameter", 10)
        tool_length = tool.get("length", 50)
        
        # 检查刀具是否够长
        if workpiece:
            max_depth = max(workpiece.get("depth", 0), workpiece.get("height", 0))
            if tool_length < max_depth * 1.2:
                warnings.append(f"刀具 {tool['tool_id']} 长度可能不足，建议使用加长刀具")
        
        # 检查刀具直径是否过大
        if tool["tool_type"] == "end_mill":
            feature_dimensions = tool.get("feature_id", "")
            # 简化检查
            if tool_diameter > 20:
                warnings.append(f"刀具 {tool['tool_id']} 直径较大，注意进给速度控制")
    
    result = {
        "has_interference": len(issues) > 0,
        "interference_issues": issues,
        "warnings": warnings,
        "recommendations": [
            "建议使用刀具长度比加工深度大20%以上",
            "粗加工使用较大直径刀具，精加工使用较小直径刀具"
        ]
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)
