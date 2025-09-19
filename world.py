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

        # 加载世界状态（天气和天数）
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
            SmartNPC("凯", 5.5, 5.5, bailian, dialog_system, chronicle),
            SmartNPC("伊拉拉", 5.5, 8.5, bailian, dialog_system, chronicle),
            SmartNPC("贾克斯", 6.5, 6.5, bailian, dialog_system, chronicle),
        ]

    def _generate_terrain(self) -> List[List[str]]:
        tiles = [["grass" for _ in range(WORLD_SIZE)] for _ in range(WORLD_SIZE)]

        for x in range(WORLD_SIZE):
            for y in range(WORLD_SIZE):
                distance_from_center = math.sqrt(
                    (x - WORLD_SIZE // 2) ** 2 + (y - WORLD_SIZE // 2) ** 2
                )
                water_chance = min(0.6, distance_from_center / (WORLD_SIZE // 2))

                if random.random() < water_chance * 0.3:
                    tiles[x][y] = "water"
                elif random.random() < 0.1 and tiles[x][y] != "water":
                    tiles[x][y] = "sand"

        # 平滑地形
        for _ in range(2):
            new_tiles = [row.copy() for row in tiles]
            for x in range(1, WORLD_SIZE - 1):
                for y in range(1, WORLD_SIZE - 1):
                    neighbors = [
                        tiles[x - 1][y], tiles[x + 1][y],
                        tiles[x][y - 1], tiles[x][y + 1]
                    ]
                    water_count = neighbors.count("water")
                    sand_count = neighbors.count("sand")

                    if water_count >= 3:
                        new_tiles[x][y] = "water"
                    elif sand_count >= 2 and tiles[x][y] != "water":
                        new_tiles[x][y] = "sand"
            tiles = new_tiles

        return tiles

    def _generate_resources(self):
        """生成岛上的资源"""
        # 在非水域生成资源
        for x in range(WORLD_SIZE):
            for y in range(WORLD_SIZE):
                if self.tiles[x][y] != "water":
                    # 随机生成资源
                    rand = random.random()
                    if rand < 0.15:  # 15% 概率生成树木
                        self.resources[x][y] = "tree"
                        self.resource_amounts[x][y] = random.randint(5, 10)
                    elif rand < 0.20:  # 5% 概率生成淡水
                        self.resources[x][y] = "freshwater"
                        self.resource_amounts[x][y] = random.randint(10, 20)
                    elif rand < 0.25:  # 5% 概率生成果树
                        self.resources[x][y] = "fruit"
                        self.resource_amounts[x][y] = random.randint(3, 7)
                    elif rand < 0.28 and self.tiles[x][y] == "sand":  # 3% 概率在沙滩生成残骸
                        self.resources[x][y] = "wreckage"
                        self.resource_amounts[x][y] = random.randint(2, 5)

        # 在水域生成鱼群
        for x in range(WORLD_SIZE):
            for y in range(WORLD_SIZE):
                if self.tiles[x][y] == "water" and random.random() < 0.2:
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
                    if res_type == "tree":
                        pygame.draw.rect(tile_surf, COLORS["tree"], (10, 10, 12, 12))
                    elif res_type == "freshwater":
                        pygame.draw.circle(tile_surf, COLORS["freshwater"], (16, 16), 8)
                    elif res_type == "fish":
                        pygame.draw.polygon(tile_surf, COLORS["fish"], [(10, 16), (22, 16), (16, 10), (16, 22)])
                    elif res_type == "fruit":
                        pygame.draw.circle(tile_surf, COLORS["fruit"], (16, 16), 5)
                    elif res_type == "wreckage":
                        pygame.draw.rect(tile_surf, COLORS["wreckage"], (8, 8, 16, 16))

                self.terrain_surface.blit(tile_surf, (x * TILE_SIZE, y * TILE_SIZE))

    def update_time(self):
        self.time = (self.time + 0.02) % 24

        if self.time < 0.02:
            self.day += 1
            if self.day % 15 == 0:
                seasons = ["春天", "夏天", "秋天", "冬天"]
                self.season = seasons[(seasons.index(self.season) + 1) % 4]

            weather_types = ["晴朗", "多云", "下雨", "刮风"]
            self.weather = random.choices(
                weather_types, [0.5, 0.3, 0.15, 0.05]
            )[0]

            # 每天有概率刷新一些资源
            self.refresh_resources()

    def refresh_resources(self):
        """每天刷新部分资源"""
        for x in range(WORLD_SIZE):
            for y in range(WORLD_SIZE):
                if self.resources[x][y] and self.resource_amounts[x][y] == 0:
                    # 已耗尽的资源有概率刷新
                    if random.random() < 0.3:
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
        return f"{self.season}第{self.day}天 {time_str}，天气{self.weather}"

    def save_world_state(self):
        """保存世界状态（天气和天数）到JSON"""
        world_data = {
            "day": self.day,
            "time": self.time,
            "season": self.season,
            "weather": self.weather
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
                self.season = world_data.get("season", "春天")
                self.weather = world_data.get("weather", "晴朗")
        except (FileNotFoundError, json.JSONDecodeError):
            # 如果文件不存在或解析错误，使用默认值
            self.day = 1
            self.time = 12.0
            self.season = "春天"
            self.weather = "晴朗"