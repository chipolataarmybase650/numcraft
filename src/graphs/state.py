"""
多智能体协作G代码生成系统 - 状态定义
"""
from typing import TypedDict, Optional, List, Dict, Any, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage


class PrecisionRequirements(TypedDict, total=False):
    """精度要求"""
    dimensional_tolerance: Optional[str]  # 尺寸公差
    surface_finish: Optional[str]         # 表面粗糙度
    geometric_tolerance: Optional[str]    # 几何公差
    hole_tolerance: Optional[str]         # 孔公差
    slot_tolerance: Optional[str]         # 槽公差


class MachiningFeature(TypedDict):
    """加工特征"""
    feature_id: str                       # 特征ID
    feature_type: str                     # 特征类型 (hole, slot, pocket, contour, etc.)
    dimensions: Dict[str, float]          # 尺寸参数
    position: Dict[str, float]            # 位置坐标
    operations: List[str]                 # 操作类型列表
    priority: int                         # 加工优先级
    notes: Optional[str]                  # 备注


class ToolInfo(TypedDict):
    """刀具信息"""
    tool_id: str                          # 刀具编号
    tool_type: str                        # 刀具类型 (end_mill, drill, tap, etc.)
    diameter: float                       # 直径
    length: float                         # 长度
    material: str                         # 刀具材质
    flute_count: int                      # 刃数
    coating: Optional[str]                # 涂层
    cutting_parameters: Dict[str, float]  # 切削参数


class ToolPath(TypedDict):
    """刀具路径"""
    tool_id: str                          # 刀具编号
    operation_type: str                   # 操作类型
    path_points: List[Dict[str, float]]   # 路径点序列
    feed_rate: float                      # 进给速度
    spindle_speed: float                  # 主轴转速
    coolant: Optional[str]                # 冷却液设置


class ProcessPlan(TypedDict):
    """工艺规划"""
    plan_id: str                          # 规划ID
    total_operations: int                 # 总操作数
    setup_sequence: List[Dict[str, Any]]  # 装夹顺序
    machining_sequence: List[Dict[str, Any]]  # 加工顺序
    estimated_time: float                 # 预估时间(分钟)
    notes: Optional[str]                  # 备注


class ValidationResult(TypedDict):
    """验证结果"""
    is_valid: bool                        # 是否有效
    errors: List[str]                     # 错误列表
    warnings: List[str]                   # 警告列表
    safety_issues: List[str]              # 安全问题
    optimization_suggestions: List[str]   # 优化建议


class MachiningState(TypedDict):
    """
    机加工多智能体协作系统的状态定义
    
    这个状态对象在整个协作流程中传递，各个智能体读取和修改相应的字段
    """
    # ========== 输入信息 ==========
    part_description: str                 # 零件描述(自然语言)
    material: str                         # 材料信息
    precision_requirements: PrecisionRequirements  # 精度要求
    workpiece_dimensions: Optional[Dict[str, float]]  # 毛坯尺寸
    machine_type: Optional[str]           # 机床类型
    
    # ========== 工艺规划阶段 ==========
    features: Optional[List[MachiningFeature]]  # 识别出的特征
    process_plan: Optional[ProcessPlan]   # 工艺方案
    
    # ========== 刀具选择阶段 ==========
    tool_list: Optional[List[ToolInfo]]   # 刀具清单
    cutting_parameters: Optional[Dict[str, Any]]  # 切削参数
    
    # ========== 路径规划阶段 ==========
    tool_paths: Optional[List[ToolPath]]  # 刀具路径数据
    
    # ========== G代码生成阶段 ==========
    gcode_program: Optional[str]          # 生成的G代码程序
    gcode_metadata: Optional[Dict[str, Any]]  # G代码元数据
    
    # ========== 验证阶段 ==========
    validation_result: Optional[ValidationResult]  # 验证结果
    
    # ========== 协作控制 ==========
    current_agent: str                    # 当前执行的智能体
    current_stage: str                    # 当前阶段
    iteration: int                        # 迭代次数
    max_iterations: int                   # 最大迭代次数
    feedback: Optional[List[str]]         # 反馈信息
    needs_revision: bool                  # 是否需要修订
    
    # ========== 消息历史 ==========
    messages: Annotated[List[AnyMessage], add_messages]  # 对话消息
    
    # ========== 元数据 ==========
    session_id: Optional[str]             # 会话ID
    created_at: Optional[str]             # 创建时间
    updated_at: Optional[str]             # 更新时间


# 默认状态值
DEFAULT_STATE: MachiningState = {
    "part_description": "",
    "material": "",
    "precision_requirements": {},
    "workpiece_dimensions": None,
    "machine_type": None,
    "features": None,
    "process_plan": None,
    "tool_list": None,
    "cutting_parameters": None,
    "tool_paths": None,
    "gcode_program": None,
    "gcode_metadata": None,
    "validation_result": None,
    "current_agent": "orchestrator",
    "current_stage": "init",
    "iteration": 0,
    "max_iterations": 3,
    "feedback": None,
    "needs_revision": False,
    "messages": [],
    "session_id": None,
    "created_at": None,
    "updated_at": None,
}
