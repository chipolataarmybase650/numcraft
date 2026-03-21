"""
多智能体协作G代码生成系统 - 集成测试
"""
import asyncio
import json
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graphs.graph import graph
from graphs.state import MachiningState


async def test_basic_machining():
    """测试基本的机加工任务"""
    
    print("\n" + "="*80)
    print("测试案例 1: 简单钻孔任务")
    print("="*80)
    
    # 测试数据：简单钻孔任务
    test_input = {
        "part_description": "铝合金零件，包含一个直径20mm深30mm的孔",
        "material": "6061-T6铝合金",
        "precision_requirements": {
            "hole_tolerance": "H7",
            "surface_finish": "Ra1.6"
        },
        "workpiece_dimensions": {
            "x_min": 0,
            "x_max": 100,
            "y_min": 0,
            "y_max": 100,
            "z_min": -50,
            "z_max": 50
        },
        "machine_type": "三轴铣床"
    }
    
    # 执行流程
    result = await graph.ainvoke(test_input)
    
    # 验证结果
    assert result.get("features") is not None, "特征识别失败"
    assert result.get("process_plan") is not None, "工艺规划失败"
    assert result.get("tool_list") is not None, "刀具选择失败"
    assert result.get("tool_paths") is not None, "路径生成失败"
    assert result.get("gcode_program") is not None, "G代码生成失败"
    assert result.get("validation_result") is not None, "验证失败"
    
    print("\n✓ 特征识别成功")
    print(f"  - 识别特征数: {len(result['features'])}")
    
    print("\n✓ 工艺规划成功")
    print(f"  - 总操作数: {result['process_plan']['total_operations']}")
    print(f"  - 预估时间: {result['process_plan']['estimated_time']:.1f} 分钟")
    
    print("\n✓ 刀具选择成功")
    print(f"  - 刀具数量: {len(result['tool_list'])}")
    
    print("\n✓ 路径生成成功")
    print(f"  - 路径数量: {len(result['tool_paths'])}")
    
    print("\n✓ G代码生成成功")
    print(f"  - 代码长度: {len(result['gcode_program'])} 字节")
    print(f"  - 代码行数: {result['gcode_program'].count(chr(10))}")
    
    print("\n✓ 安全验证完成")
    print(f"  - 验证结果: {'通过' if result['validation_result']['is_valid'] else '失败'}")
    print(f"  - 错误数: {len(result['validation_result']['errors'])}")
    print(f"  - 警告数: {len(result['validation_result']['warnings'])}")
    
    # 显示部分G代码
    print("\n" + "-"*80)
    print("G代码预览（前30行）:")
    print("-"*80)
    gcode_lines = result['gcode_program'].split('\n')[:30]
    for line in gcode_lines:
        print(line)
    
    return result


async def test_complex_machining():
    """测试复杂的机加工任务"""
    
    print("\n" + "="*80)
    print("测试案例 2: 复杂特征任务")
    print("="*80)
    
    # 测试数据：复杂零件
    test_input = {
        "part_description": "钢制零件，包含一个直径10mm深25mm的孔、一个50x30mm深15mm的槽和外轮廓加工",
        "material": "45#钢",
        "precision_requirements": {
            "dimensional_tolerance": "±0.05mm",
            "surface_finish": "Ra3.2"
        },
        "workpiece_dimensions": {
            "x_min": 0,
            "x_max": 150,
            "y_min": 0,
            "y_max": 100,
            "z_min": -60,
            "z_max": 50
        },
        "machine_type": "三轴加工中心"
    }
    
    # 执行流程
    result = await graph.ainvoke(test_input)
    
    # 验证结果
    assert result.get("features") is not None, "特征识别失败"
    assert result.get("gcode_program") is not None, "G代码生成失败"
    
    print("\n✓ 复杂特征识别成功")
    print(f"  - 识别特征数: {len(result['features'])}")
    
    feature_types = [f.get("feature_type") for f in result['features']]
    print(f"  - 特征类型: {', '.join(set(feature_types))}")
    
    print("\n✓ 工艺规划完成")
    print(f"  - 预估总时间: {result['process_plan']['estimated_time']:.1f} 分钟")
    
    print("\n✓ 刀具配置完成")
    print(f"  - 刀具总数: {len(result['tool_list'])}")
    
    tool_types = [t.get("tool_type") for t in result['tool_list']]
    print(f"  - 刀具类型: {', '.join(set(tool_types))}")
    
    print("\n✓ G代码生成完成")
    print(f"  - 程序大小: {len(result['gcode_program'])/1024:.2f} KB")
    
    validation = result['validation_result']
    print("\n✓ 安全验证")
    print(f"  - 完整性评分: {validation['completeness_score']:.1f}%")
    print(f"  - 预估加工时间: {validation['machining_time']:.1f} 分钟")
    
    if validation['optimization_suggestions']:
        print("\n优化建议:")
        for suggestion in validation['optimization_suggestions']:
            print(f"  - {suggestion}")
    
    return result


async def test_feature_recognition():
    """单独测试特征识别功能"""
    
    print("\n" + "="*80)
    print("测试案例 3: 特征识别准确性")
    print("="*80)
    
    from tools.process_planning_tools import recognize_features
    
    test_cases = [
        ("直径15mm通孔", "铝合金", "hole"),
        ("30x20mm的槽，深10mm", "钢", "slot"),
        ("型腔 40x40mm，深20mm", "铝合金", "pocket"),
        ("外轮廓加工", "钢", "contour"),
    ]
    
    for description, material, expected_type in test_cases:
        result_json = recognize_features.invoke({
            "part_description": description,
            "material": material
        })
        
        result = json.loads(result_json)
        features = result.get("features", [])
        
        if features:
            feature_type = features[0].get("feature_type")
            status = "✓" if feature_type == expected_type else "✗"
            print(f"{status} '{description}' -> 识别为: {feature_type} (期望: {expected_type})")
        else:
            print(f"✗ '{description}' -> 未识别到特征")
    
    print("\n特征识别测试完成")


async def main():
    """运行所有测试"""
    
    print("\n" + "#"*80)
    print("# 多智能体协作G代码生成系统 - 集成测试套件")
    print("#"*80)
    
    try:
        # 测试1: 简单任务
        result1 = await test_basic_machining()
        
        # 测试2: 复杂任务
        result2 = await test_complex_machining()
        
        # 测试3: 特征识别
        await test_feature_recognition()
        
        print("\n" + "#"*80)
        print("# 所有测试通过！")
        print("#"*80)
        
        # 保存测试结果
        test_results = {
            "test_case_1": {
                "description": "简单钻孔任务",
                "features_count": len(result1.get("features", [])),
                "gcode_size": len(result1.get("gcode_program", "")),
                "validation_passed": result1.get("validation_result", {}).get("is_valid", False)
            },
            "test_case_2": {
                "description": "复杂特征任务",
                "features_count": len(result2.get("features", [])),
                "gcode_size": len(result2.get("gcode_program", "")),
                "validation_passed": result2.get("validation_result", {}).get("is_valid", False)
            }
        }
        
        with open("/tmp/test_results.json", "w", encoding="utf-8") as f:
            json.dump(test_results, f, ensure_ascii=False, indent=2)
        
        print("\n测试结果已保存到: /tmp/test_results.json")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())
