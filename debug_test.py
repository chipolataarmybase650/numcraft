"""
诊断测试脚本
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from tools.process_planning_tools import recognize_features
import json

# 测试特征识别
test_description = "铝合金零件，包含一个直径20mm深30mm的孔"
material = "6061-T6铝合金"

print(f"测试输入: {test_description}")
print(f"材料: {material}")

try:
    result = recognize_features.invoke({
        "part_description": test_description,
        "material": material
    })
    
    print("\n特征识别结果:")
    print(result)
    
    data = json.loads(result)
    print(f"\n识别特征数: {len(data.get('features', []))}")
    
    if data.get('features'):
        for feature in data['features']:
            print(f"  - {feature['feature_type']}: {feature['notes']}")
    
except Exception as e:
    print(f"\n错误: {e}")
    import traceback
    traceback.print_exc()
