"""
世界类 - 地形、资源和环境管理
"""
import pygame
import json
import random
import math
from typing import List
from npc import SmartNPC
from texture import generate_textures
from config import *


class World:
    def __init__(self, bailian, dialog_system, chronicle):
        self.tiles = self._generate_terrain()
        self.resources = [[None for _ in range(WORLD_SIZE)] for _ in range(WORLD_SIZE)]
        self.resource_amounts = [[0 for _ in range(WORLD_SIZE)] for _ in range(WORLD_SIZE)]
        self._generate_resources()
        self.load_resources()

        # 加载世界状态（仅保留天数和时间）
        self.load_world_state()

        # 地形渲染缓存
        self.terrain_surface = pygame.Surface(
            (WORLD_SIZE * TILE_SIZE, WORLD_SIZE * TILE_SIZE),
            pygame.HWSURFACE
        ).convert()

        # 生成纹理
        self.textures = generate_textures()
        self._pre_render_terrain()

        self.npcs = [
            SmartNPC("凯", 13, 13, bailian, dialog_system, chronicle),
            SmartNPC("伊拉拉", 14, 15, bailian, dialog_system, chronicle),
            SmartNPC("贾克斯", 15, 14, bailian, dialog_system, chronicle),
        ]
        
        # 新增：记录所有NPC的行为，用于观察
        self.action_log = []

    def _generate_terrain(self) -> List[List[str]]:
        # 初始化所有格子为水
        tiles = [["water" for _ in range(WORLD_SIZE)] for _ in range(WORLD_SIZE)]

        center = WORLD_SIZE // 2  # 计算中心点坐标
        radius = 10  # 岛屿半径

        for x in range(WORLD_SIZE):
            for y in range(WORLD_SIZE):
                # 计算与中心的距离
                distance_from_center = math.sqrt(
                    (x - center) ** 2 + (y - center) ** 2
                )

                # 在圆形范围内生成陆地
                if distance_from_center <= radius:
                    # 中心区域更可能是草地
                    grass_chance = 1.0 - (distance_from_center / radius) * 0.7

                    # 距离中心越远，沙地可能性越高
                    sand_chance = min(0.6, (distance_from_center / radius) * 0.8)

                    # 随机决定地形类型
                    if random.random() < sand_chance:
                        tiles[x][y] = "sand"
                    else:
                        tiles[x][y] = "grass"

        # 平滑地形，使过渡更自然
        for _ in range(2):
            new_tiles = [row.copy() for row in tiles]
            for x in range(1, WORLD_SIZE - 1):
                for y in range(1, WORLD_SIZE - 1):
                    # 只处理圆形范围内的格子
                    distance_from_center = math.sqrt(
                        (x - center) ** 2 + (y - center) ** 2
                    )
                    if distance_from_center > radius + 1:
                        continue

                    # 检查四个方向的邻居
                    neighbors = [
                        tiles[x - 1][y], tiles[x + 1][y],
                        tiles[x][y - 1], tiles[x][y + 1]
                    ]
                    water_count = neighbors.count("water")
                    sand_count = neighbors.count("sand")
                    grass_count = neighbors.count("grass")

                    # 根据邻居情况调整地形
                    if water_count >= 3:
                        new_tiles[x][y] = "water"
                    elif sand_count >= 3:
                        new_tiles[x][y] = "sand"
                    elif grass_count >= 3:
                        new_tiles[x][y] = "grass"
                    # 边界附近更可能变成沙地
                    elif distance_from_center > radius - 2 and random.random() < 0.7:
                        new_tiles[x][y] = "sand"

            tiles = new_tiles

        return tiles

    def _generate_resources(self):
        """生成岛上的资源（删除了残骸）"""
        # 在非水域生成资源
        for x in range(WORLD_SIZE):
            for y in range(WORLD_SIZE):
                if self.tiles[x][y] != "water":
                    # 随机生成资源（删除了树木）
                    rand = random.random()
                    if rand < 0.05:  # 20% 概率生成淡水
                        self.resources[x][y] = "freshwater"
                        self.resource_amounts[x][y] = random.randint(10, 20)
                    elif rand < 0.07:  # 5% 概率生成果树
                        self.resources[x][y] = "fruit"
                        self.resource_amounts[x][y] = random.randint(3, 7)

        # 在水域生成鱼群
        for x in range(WORLD_SIZE):
            for y in range(WORLD_SIZE):
                if self.tiles[x][y] == "water" and random.random() < 0.1:
                    self.resources[x][y] = "fish"
                    self.resource_amounts[x][y] = random.randint(3, 8)



    def save_resources(self):
        """保存资源状态到JSON"""
        resource_data = {
            "resources": self.resources,
            "amounts": self.resource_amounts
        }
        with open("data/resources.json", "w", encoding="utf-8") as f:
            json.dump(resource_data, f, ensure_ascii=False, indent=2)

    def load_resources(self):
        """从JSON加载资源状态"""
        try:
            with open("data/resources.json", "r", encoding="utf-8") as f:
                resource_data = json.load(f)
                self.resources = resource_data["resources"]
                self.resource_amounts = resource_data["amounts"]
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def _pre_render_terrain(self):
        """预渲染所有地形到缓存Surface"""
        for x in range(WORLD_SIZE):
            for y in range(WORLD_SIZE):
                tile_type = self.tiles[x][y]
                tile_surf = self.textures[tile_type].copy()

                # 绘制资源
                if self.resources[x][y] and self.resource_amounts[x][y] > 0:
                    res_type = self.resources[x][y]                    
                    if res_type == "freshwater":
                        pygame.draw.circle(tile_surf, COLORS["freshwater"], (16, 16), 8)
                    elif res_type == "fish":
                        pygame.draw.polygon(tile_surf, COLORS["fish"], [(10, 16), (22, 16), (16, 10), (16, 22)])
                    elif res_type == "fruit":
                        pygame.draw.circle(tile_surf, COLORS["fruit"], (16, 16), 5)

                self.terrain_surface.blit(tile_surf, (x * TILE_SIZE, y * TILE_SIZE))

    def update_time(self):
        self.time = (self.time + 0.02) % 24

        if self.time < 0.02:
            self.day += 1

            # 每天有概率刷新一些资源
            self.refresh_resources()

    def refresh_resources(self):
        """每天刷新部分资源"""
        for x in range(WORLD_SIZE):
            for y in range(WORLD_SIZE):
                if self.resources[x][y] and self.resource_amounts[x][y] == 0:
                    # 已耗尽的资源有概率刷新
                    if random.random() < 0.03:
                        if self.resources[x][y] == "tree":
                            self.resource_amounts[x][y] = random.randint(3, 7)
                        elif self.resources[x][y] == "freshwater":
                            self.resource_amounts[x][y] = random.randint(5, 15)
                        elif self.resources[x][y] == "fruit":
                            self.resource_amounts[x][y] = random.randint(2, 5)
                        elif self.resources[x][y] == "fish":
                            self.resource_amounts[x][y] = random.randint(2, 6)

        # 更新地形渲染
        self._pre_render_terrain()
        self.save_resources()

    def get_state_str(self) -> str:
        hour = int(self.time)
        minute = int((self.time % 1) * 60)
        time_str = f"{hour:02d}:{minute:02d}"
        # 删除天气和季节信息
        return f"第{self.day}天 {time_str}"

    def save_world_state(self):
        """保存世界状态（天气和天数）到JSON"""
        world_data = {
            "day": self.day,
            "time": self.time
        }
        with open("data/world_state.json", "w", encoding="utf-8") as f:
            json.dump(world_data, f, ensure_ascii=False, indent=2)

    def load_world_state(self):
        """从JSON加载世界状态（天气和天数）"""
        try:
            with open("data/world_state.json", "r", encoding="utf-8") as f:
                world_data = json.load(f)
                self.day = world_data.get("day", 1)
                self.time = world_data.get("time", 12.0)
        except (FileNotFoundError, json.JSONDecodeError):
            # 如果文件不存在或解析错误，使用默认值
            self.day = 1
            self.time = 12.0

            
