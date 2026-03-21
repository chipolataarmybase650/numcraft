"""
使用示例：多智能体协作G代码生成系统
"""
import requests
import json


def example_basic_hole():
    """示例1: 简单钻孔任务"""
    print("\n" + "="*60)
    print("示例1: 简单钻孔任务")
    print("="*60)
    
    # 请求数据
    data = {
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
        }
    }
    
    # 发送请求
    response = requests.post("http://localhost:5000/run", json=data)
    result = response.json()
    
    # 显示结果
    print(f"\n识别特征数: {len(result.get('features', []))}")
    print(f"刀具数量: {len(result.get('tool_list', []))}")
    print(f"验证通过: {result.get('validation_result', {}).get('is_valid', False)}")
    
    # 显示G代码前20行
    print("\nG代码预览:")
    gcode_lines = result.get('gcode_program', '').split('\n')[:20]
    for line in gcode_lines:
        print(f"  {line}")
    
    return result


def example_complex_part():
    """示例2: 复杂零件加工"""
    print("\n" + "="*60)
    print("示例2: 复杂零件加工")
    print("="*60)
    
    data = {
        "part_description": """
        钢制零件，包含以下特征：
        1. 一个直径10mm深25mm的孔
        2. 一个50x30mm深15mm的槽
        3. 外轮廓加工
        """,
        "material": "45#钢",
        "precision_requirements": {
            "dimensional_tolerance": "±0.05mm",
            "surface_finish": "Ra3.2"
        },
        "machine_type": "三轴加工中心"
    }
    
    response = requests.post("http://localhost:5000/run", json=data)
    result = response.json()
    
    print(f"\n识别特征数: {len(result.get('features', []))}")
    
    # 特征类型统计
    feature_types = {}
    for feature in result.get('features', []):
        ft = feature.get('feature_type')
        feature_types[ft] = feature_types.get(ft, 0) + 1
    
    print("\n特征类型分布:")
    for ft, count in feature_types.items():
        print(f"  - {ft}: {count}")
    
    # 刀具统计
    tool_types = {}
    for tool in result.get('tool_list', []):
        tt = tool.get('tool_type')
        tool_types[tt] = tool_types.get(tt, 0) + 1
    
    print("\n刀具类型分布:")
    for tt, count in tool_types.items():
        print(f"  - {tt}: {count}")
    
    return result


def example_batch_processing():
    """示例3: 批量处理"""
    print("\n" + "="*60)
    print("示例3: 批量处理多个零件")
    print("="*60)
    
    parts = [
        {
            "id": "PART001",
            "description": "铝合金，直径15mm通孔",
            "material": "铝合金"
        },
        {
            "id": "PART002",
            "description": "钢件，30x20mm的槽",
            "material": "钢"
        },
        {
            "id": "PART003",
            "description": "不锈钢，型腔加工40x40mm",
            "material": "不锈钢"
        }
    ]
    
    results = []
    
    for part in parts:
        print(f"\n处理零件 {part['id']}: {part['description']}")
        
        data = {
            "part_description": part['description'],
            "material": part['material']
        }
        
        response = requests.post("http://localhost:5000/run", json=data)
        result = response.json()
        
        results.append({
            "id": part['id'],
            "features_count": len(result.get('features', [])),
            "gcode_size": len(result.get('gcode_program', '')),
            "valid": result.get('validation_result', {}).get('is_valid', False)
        })
    
    # 汇总结果
    print("\n" + "-"*60)
    print("批量处理结果汇总:")
    print("-"*60)
    
    for r in results:
        print(f"{r['id']}: {r['features_count']}特征, {r['gcode_size']}字节G代码, 验证{'通过' if r['valid'] else '失败'}")
    
    return results


def example_with_validation():
    """示例4: 带详细验证的任务"""
    print("\n" + "="*60)
    print("示例4: 带详细验证的任务")
    print("="*60)
    
    data = {
        "part_description": "铝合金零件，直径25mm深40mm的孔，精度要求H7",
        "material": "6061-T6铝合金",
        "precision_requirements": {
            "hole_tolerance": "H7",
            "surface_finish": "Ra0.8"
        },
        "workpiece_dimensions": {
            "x_min": -200,
            "x_max": 200,
            "y_min": -200,
            "y_max": 200,
            "z_min": -100,
            "z_max": 100
        },
        "machine_type": "五轴加工中心"
    }
    
    response = requests.post("http://localhost:5000/run", json=data)
    result = response.json()
    
    # 显示详细验证结果
    validation = result.get('validation_result', {})
    
    print("\n验证结果:")
    print(f"  整体状态: {'通过' if validation.get('is_valid') else '失败'}")
    print(f"  完整性评分: {validation.get('completeness_score', 0):.1f}%")
    print(f"  预估加工时间: {validation.get('machining_time', 0):.1f} 分钟")
    
    if validation.get('errors'):
        print("\n错误:")
        for error in validation['errors']:
            print(f"  ❌ {error}")
    
    if validation.get('warnings'):
        print("\n警告:")
        for warning in validation['warnings']:
            print(f"  ⚠️  {warning}")
    
    if validation.get('optimization_suggestions'):
        print("\n优化建议:")
        for suggestion in validation['optimization_suggestions']:
            print(f"  💡 {suggestion}")
    
    return result


def main():
    """运行所有示例"""
    print("\n" + "#"*60)
    print("# 多智能体协作G代码生成系统 - 使用示例")
    print("#"*60)
    
    try:
        # 示例1
        result1 = example_basic_hole()
        
        # 示例2
        result2 = example_complex_part()
        
        # 示例3
        result3 = example_batch_processing()
        
        # 示例4
        result4 = example_with_validation()
        
        print("\n" + "#"*60)
        print("# 所有示例执行完成！")
        print("#"*60)
        
    except requests.exceptions.ConnectionError:
        print("\n错误: 无法连接到服务器，请确保服务正在运行")
        print("启动服务: python src/main.py -m http -p 5000")
    except Exception as e:
        print(f"\n错误: {e}")


if __name__ == "__main__":
    main()
