"""
荒岛模拟 - 主程序入口
AI驱动的NPC互动模拟游戏
"""
import pygame
import os
import sys
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from game import Game

# 确保数据目录存在
os.makedirs("data", exist_ok=True)

# 初始化pygame
pygame.init()
pygame.font.init()

# 创建屏幕和时钟
screen = pygame.display.set_mode(
    (SCREEN_WIDTH, SCREEN_HEIGHT),
    pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE
)
pygame.display.set_caption("荒岛模拟")
clock = pygame.time.Clock()


def main():
    """主函数"""
    # API密钥 - 请替换为有效的API密钥
    API_KEY = "sk-7cb1a01af2e946d3a075d761cd74a166"

    try:
        # 创建并运行游戏
        game = Game(API_KEY)
        game.run()
    except KeyboardInterrupt:
        print("\n游戏被用户中断")
        pygame.quit()
        sys.exit(0)
    except Exception as e:
        print(f"游戏运行出错: {e}")
        pygame.quit()
        sys.exit(1)


if __name__ == "__main__":
    main()