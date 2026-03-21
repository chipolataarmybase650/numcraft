"""
完整诊断测试脚本
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from tools.process_planning_tools import recognize_features, generate_process_plan
from tools.tool_selection_tools import select_tools_for_features
import json

def test_feature_recognition():
    """测试特征识别"""
    print("\n" + "="*60)
    print("测试 1: 特征识别")
    print("="*60)
    
    test_description = "铝合金零件，包含一个直径20mm深30mm的孔"
    material = "6061-T6铝合金"
    
    result = recognize_features.invoke({
        "part_description": test_description,
        "material": material
    })
    
    data = json.loads(result)
    print(f"识别特征数: {len(data.get('features', []))}")
    
    return result

def test_process_plan(features_json):
    """测试工艺规划"""
    print("\n" + "="*60)
    print("测试 2: 工艺规划")
    print("="*60)
    
    result = generate_process_plan.invoke({
        "features": features_json,
        "material": "6061-T6铝合金",
        "precision_requirements": "{}"
    })
    
    data = json.loads(result)
    print(f"总操作数: {data.get('total_operations', 0)}")
    print(f"预估时间: {data.get('estimated_time', 0):.1f} 分钟")
    
    return result

def test_tool_selection(features_json):
    """测试刀具选择"""
    print("\n" + "="*60)
    print("测试 3: 刀具选择")
    print("="*60)
    
    result = select_tools_for_features.invoke({
        "features": features_json,
        "material": "6061-T6铝合金"
    })
    
    data = json.loads(result)
    tools = data.get("tool_list", [])
    print(f"选择刀具数: {len(tools)}")
    
    if tools:
        print("\n刀具清单:")
        for tool in tools[:3]:  # 只显示前3个
            print(f"  - {tool['tool_id']}: {tool['tool_type']} 直径{tool['diameter']}mm")
    
    return result

def main():
    """运行所有测试"""
    print("\n开始诊断测试...")
    
    try:
        # 测试特征识别
        features_json = test_feature_recognition()
        
        # 测试工艺规划
        plan_json = test_process_plan(features_json)
        
        # 测试刀具选择
        tools_json = test_tool_selection(features_json)
        
        print("\n" + "="*60)
        print("所有基础工具测试通过！")
        print("="*60)
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
