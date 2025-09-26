"""
荒岛模拟 - 主程序入口
AI驱动的NPC互动模拟游戏
"""
import os
import sys
from game import Game
import asyncio
# 确保数据目录存在
os.makedirs("data", exist_ok=True)

def main():
    """主函数"""
    # API密钥 - 请替换为有效的API密钥
    API_KEY = "sk-7cb1a01af2e946d3a075d761cd74a166"

    try:
        # 创建并运行游戏
        game = Game(API_KEY)
        asyncio.run(game.run())
    except KeyboardInterrupt:
        print("\n游戏被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"游戏运行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()