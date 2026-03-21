"""
直接测试Agent
"""
import os
import sys
import asyncio

# 设置环境
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
os.chdir('/workspace/projects')

async def test():
    """直接测试Agent"""
    from agents.agent import build_agent
    from coze_coding_utils.runtime_ctx.context import new_context
    
    # 创建上下文
    ctx = new_context(method="test")
    
    # 构建agent
    print("构建Agent...")
    agent = build_agent(ctx)
    
    # 测试调用
    print("\n测试Agent调用...")
    test_input = {
        "messages": [{"type": "human", "content": "铝合金零件，包含一个直径20mm深30mm的孔"}]
    }
    
    config = {"configurable": {"thread_id": ctx.run_id}}
    
    try:
        result = await agent.ainvoke(test_input, config=config, context=ctx)
        print("\nAgent响应:")
        print(result)
        return result
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    asyncio.run(test())
