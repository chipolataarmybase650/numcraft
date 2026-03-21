"""
工艺规划工具集
用于特征识别和工艺规划
"""
from typing import Dict, List, Any, Optional
from langchain.tools import tool
import re
import json
import logging

logger = logging.getLogger(__name__)


@tool
def recognize_features(part_description: str, material: str) -> str:
    """
    从零件描述中识别加工特征
    
    Args:
        part_description: 零件的自然语言描述
        material: 材料信息
    
    Returns:
        JSON格式的特征列表
    """
    features = []
    feature_id = 1
    
    # 孔特征识别 - 更灵活的匹配模式
    hole_patterns = [
        r'直径\s*(\d+(?:\.\d+)?)\s*mm',  # 直接匹配直径
        r'(\d+(?:\.\d+)?)\s*mm.*?孔',     # 数字mm + 孔
        r'孔.*?(\d+(?:\.\d+)?)\s*mm',     # 孔 + 数字mm
        r'钻孔.*?(\d+(?:\.\d+)?)',        # 钻孔 + 数字
    ]
    
    for pattern in hole_patterns:
        matches = re.finditer(pattern, part_description, re.IGNORECASE)
        for match in matches:
            diameter = float(match.group(1))
            
            # 尝试提取深度
            depth = None
            depth_match = re.search(r'深\s*(\d+(?:\.\d+)?)\s*mm', part_description)
            if depth_match:
                depth = float(depth_match.group(1))
            
            feature = {
                "feature_id": f"F{feature_id:03d}",
                "feature_type": "hole",
                "dimensions": {
                    "diameter": diameter,
                    "depth": depth if depth else diameter * 3  # 默认深径比3:1
                },
                "position": {
                    "x": 0.0,
                    "y": 0.0,
                    "z": 0.0
                },
                "operations": ["drilling", "reaming"] if diameter <= 20 else ["drilling", "boring"],
                "priority": feature_id,
                "notes": f"直径{diameter}mm的孔"
            }
            features.append(feature)
            feature_id += 1
    
    # 槽特征识别
    slot_patterns = [
        r'(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*mm.*?槽',
        r'槽.*?(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*mm',
        r'长\s*(\d+(?:\.\d+)?)\s*宽\s*(\d+(?:\.\d+)?)\s*mm.*?槽',
    ]
    
    for pattern in slot_patterns:
        matches = re.finditer(pattern, part_description, re.IGNORECASE)
        for match in matches:
            length = float(match.group(1))
            width = float(match.group(2))
            
            # 尝试提取深度
            depth = 5.0  # 默认深度
            depth_match = re.search(r'深\s*(\d+(?:\.\d+)?)\s*mm', part_description)
            if depth_match:
                depth = float(depth_match.group(1))
            
            feature = {
                "feature_id": f"F{feature_id:03d}",
                "feature_type": "slot",
                "dimensions": {
                    "length": length,
                    "width": width,
                    "depth": depth
                },
                "position": {
                    "x": 0.0,
                    "y": 0.0,
                    "z": 0.0
                },
                "operations": ["rough_milling", "finish_milling"],
                "priority": feature_id,
                "notes": f"{length}x{width}mm的槽"
            }
            features.append(feature)
            feature_id += 1
    
    # 轮廓特征识别
    if any(keyword in part_description for keyword in ['轮廓', '外形', '边缘', '外形加工']):
        feature = {
            "feature_id": f"F{feature_id:03d}",
            "feature_type": "contour",
            "dimensions": {
                "type": "external"
            },
            "position": {
                "x": 0.0,
                "y": 0.0,
                "z": 0.0
            },
            "operations": ["rough_milling", "finish_milling"],
            "priority": feature_id,
            "notes": "外轮廓加工"
        }
        features.append(feature)
        feature_id += 1
    
    # 型腔特征识别
    pocket_patterns = [
        r'(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*mm.*?(型腔|腔体|凹槽)',
        r'(型腔|腔体|凹槽).*?(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*mm',
    ]
    
    for pattern in pocket_patterns:
        matches = re.finditer(pattern, part_description, re.IGNORECASE)
        for match in matches:
            length = float(match.group(1))
            width = float(match.group(2))
            
            feature = {
                "feature_id": f"F{feature_id:03d}",
                "feature_type": "pocket",
                "dimensions": {
                    "length": length,
                    "width": width,
                    "depth": 10.0  # 默认深度
                },
                "position": {
                    "x": 0.0,
                    "y": 0.0,
                    "z": 0.0
                },
                "operations": ["rough_milling", "finish_milling"],
                "priority": feature_id,
                "notes": f"{length}x{width}mm的型腔"
            }
            features.append(feature)
            feature_id += 1
    
    result = {
        "features": features,
        "total_count": len(features),
        "material": material,
        "recognition_confidence": 0.85 if features else 0.0
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def generate_process_plan(features, material: str, precision_requirements) -> str:
    """
    根据特征列表生成工艺规划方案
    
    Args:
        features: JSON格式的特征列表或特征列表对象
        material: 材料信息
        precision_requirements: JSON格式的精度要求
    
    Returns:
        JSON格式的工艺规划方案
    """
    # 处理features参数
    if isinstance(features, str):
        try:
            features_list = json.loads(features)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON input"}, ensure_ascii=False)
    elif isinstance(features, list):
        features_list = {"features": features}
    elif isinstance(features, dict):
        features_list = features
    else:
        return json.dumps({"error": f"Invalid features type: {type(features)}"}, ensure_ascii=False)
    
    # 处理precision_requirements参数
    if isinstance(precision_requirements, str):
        try:
            precision_dict = json.loads(precision_requirements) if precision_requirements else {}
        except json.JSONDecodeError:
            precision_dict = {}
    elif isinstance(precision_requirements, dict):
        precision_dict = precision_requirements
    else:
        precision_dict = {}
    
    # 材料硬度映射
    material_hardness = {
        "铝合金": "HB 80-120",
        "钢": "HRC 20-40",
        "不锈钢": "HB 180-250",
        "铸铁": "HB 180-250",
        "铜合金": "HB 60-100",
        "钛合金": "HRC 30-40",
    }
    
    # 估算加工时间（基于特征）
    total_time = 0.0
    machining_sequence = []
    setup_sequence = []
    
    # 分析特征，制定加工顺序
    sorted_features = sorted(features_list.get("features", []), key=lambda x: x.get("priority", 0))
    
    # 基础装夹设置
    setup_sequence.append({
        "setup_id": "S1",
        "setup_type": "定位夹紧",
        "description": "工件定位，三爪卡盘夹紧",
        "estimated_time": 5.0
    })
    total_time += 5.0
    
    operation_id = 1
    for feature in sorted_features:
        feature_type = feature.get("feature_type")
        operations = feature.get("operations", [])
        dimensions = feature.get("dimensions", {})
        
        for op in operations:
            # 基于特征类型和尺寸估算时间
            if op == "drilling":
                diameter = dimensions.get("diameter", 10)
                depth = dimensions.get("depth", 30)
                time_estimate = (diameter * depth) / 500.0  # 经验公式
            elif op == "rough_milling":
                time_estimate = 15.0  # 粗加工估算
            elif op == "finish_milling":
                time_estimate = 10.0  # 精加工估算
            elif op == "reaming":
                time_estimate = 3.0
            else:
                time_estimate = 5.0
            
            machining_sequence.append({
                "operation_id": f"OP{operation_id:03d}",
                "feature_id": feature.get("feature_id"),
                "operation_type": op,
                "estimated_time": time_estimate,
                "notes": f"{feature.get('notes', '')} - {op}"
            })
            
            total_time += time_estimate
            operation_id += 1
    
    process_plan = {
        "plan_id": "PP001",
        "total_operations": len(machining_sequence),
        "setup_sequence": setup_sequence,
        "machining_sequence": machining_sequence,
        "estimated_time": total_time,
        "material_info": {
            "material": material,
            "hardness": material_hardness.get(material, "未知"),
            "machinability": "良好" if "铝" in material else "一般"
        },
        "precision_analysis": precision_dict,
        "notes": "工艺规划基于特征识别和材料特性生成"
    }
    
    return json.dumps(process_plan, ensure_ascii=False, indent=2)


@tool
def validate_process_feasibility(process_plan, machine_type: str) -> str:
    """
    验证工艺方案的可行性
    
    Args:
        process_plan: JSON格式的工艺规划
        machine_type: 机床类型
    
    Returns:
        JSON格式的可行性分析结果
    """
    # 处理process_plan参数
    if isinstance(process_plan, str):
        try:
            plan = json.loads(process_plan)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON input"}, ensure_ascii=False)
    elif isinstance(process_plan, dict):
        plan = process_plan
    else:
        return json.dumps({"error": f"Invalid process_plan type: {type(process_plan)}"}, ensure_ascii=False)
    
    issues = []
    warnings = []
    suggestions = []
    
    # 检查加工顺序合理性
    operations = plan.get("machining_sequence", [])
    operation_types = [op.get("operation_type") for op in operations]
    
    # 检查粗精加工顺序
    if "finish_milling" in operation_types and "rough_milling" in operation_types:
        rough_idx = operation_types.index("rough_milling")
        finish_idx = operation_types.index("finish_milling")
        if finish_idx < rough_idx:
            issues.append("精加工应在粗加工之后进行")
    
    # 检查时间估算合理性
    total_time = plan.get("estimated_time", 0)
    if total_time < 5:
        warnings.append("预估时间过短，请检查工艺完整性")
    elif total_time > 300:
        warnings.append("预估时间较长，建议优化工艺方案")
    
    # 机床能力检查
    if machine_type and "五轴" not in machine_type:
        complex_features = sum(1 for op in operations if "复杂" in op.get("notes", ""))
        if complex_features > 0:
            suggestions.append("检测到复杂特征，建议使用五轴机床以提高效率")
    
    result = {
        "is_feasible": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "optimization_suggestions": suggestions,
        "machine_compatibility": "兼容" if len(issues) == 0 else "不兼容",
        "review_required": len(issues) > 0 or len(warnings) > 0
    }
    
    return json.dumps(result, ensure_ascii=False, indent=2)
