"""
工具辅助函数
"""
import json
from typing import Any, Union, Dict, List


def parse_json_param(param: Any, default=None) -> Union[Dict, List, None]:
    """
    解析JSON参数，支持字符串、字典、列表等多种输入格式
    
    Args:
        param: 输入参数，可以是字符串、字典、列表或None
        default: 解析失败时的默认返回值
    
    Returns:
        解析后的字典或列表，或默认值
    """
    if param is None:
        return default if default is not None else {}
    
    if isinstance(param, str):
        try:
            return json.loads(param)
        except json.JSONDecodeError:
            return default if default is not None else {}
    
    if isinstance(param, (dict, list)):
        return param
    
    return default if default is not None else {}
