"""
游戏配置和常量定义
"""
import pygame

# 游戏常量
WORLD_SIZE = 30
TILE_SIZE = 32
SCREEN_WIDTH, SCREEN_HEIGHT = 1024, 768
HUD_HEIGHT = 120
FPS = 10
CAMERA_SPEED = 10

# 声音范围常量
VOLUME_NORMAL_RANGE = 10.0  # 正常说话范围
VOLUME_LOUD_RANGE = 15.0  # 喊叫范围

# 大模型调用冷却时间（秒）
MODEL_CALL_COOLDOWN = 10

# 资源类型与采集量
RESOURCE_TYPES = {
    "tree": {"name": "树木", "gather": "wood", "amount": 3},
    "freshwater": {"name": "淡水", "gather": "水", "amount": 5},
    "fish": {"name": "鱼群", "gather": "鱼", "amount": 2},
    "fruit": {"name": "果树", "gather": "果实", "amount": 4},
    "wreckage": {"name": "残骸", "gather": "杂物", "amount": 3}
}

# 颜色定义
COLORS = {
    "grass": (34, 139, 34),
    "water": (0, 100, 200),
    "sand": (244, 164, 96),
    "wood": (139, 69, 19),
    "stone": (169, 169, 169),
    "food": (255, 215, 0),
    "npc": (255, 215, 0),  # 黄色 - 非对话时的颜色
    "npc_talking": (100, 150, 255),  # 蓝色 - 对话时的颜色
    "npc_dead": (100, 100, 100),  # 灰色 - 死亡状态
    "ui": (50, 50, 50),
    "highlight": (255, 255, 0, 100),
    "tree": (34, 139, 34),
    "freshwater": (0, 200, 255),
    "fish": (255, 100, 100),
    "fruit": (255, 0, 0),
    "wreckage": (100, 100, 100)
}

# 初始化字体
def init_fonts():
    """初始化游戏字体"""
    pygame.font.init()
    font_names = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC", "Arial Unicode MS"]
    game_font = pygame.font.SysFont(font_names, 24)
    small_font = pygame.font.SysFont(font_names, 16)
    large_font = pygame.font.SysFont(font_names, 32)
    tiny_font = pygame.font.SysFont(font_names, 12)
    return game_font, small_font, large_font, tiny_font