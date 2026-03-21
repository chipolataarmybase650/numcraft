"""
测试单个工具
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from tools.tool_selection_tools import select_tools_for_features
import json

# 测试数据
features_json = '[{"feature_id": "F001", "feature_type": "hole", "dimensions": {"diameter": 10.0, "depth": 25.0}, "position": {"x": 0.0, "y": 0.0, "z": 0.0}, "operations": ["drilling", "reaming"], "priority": 1, "notes": "直径10.0mm的孔"}]'

material = "钢"

try:
    result = select_tools_for_features.invoke({
        "features": features_json,
        "material": material
    })
    
    print("成功!")
    print(result)
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
