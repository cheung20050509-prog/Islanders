"""
纹理生成器
"""
import pygame
import random
from config import TILE_SIZE, COLORS

class TextureGenerator:
    @staticmethod
    def generate_grass_texture():
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        surf.fill(COLORS["grass"])
        for _ in range(10):
            x1 = random.randint(0, TILE_SIZE)
            y1 = random.randint(0, TILE_SIZE)
            x2 = x1 + random.randint(-5, 5)
            y2 = y1 + random.randint(-5, 5)
            pygame.draw.line(surf, (20, 100, 20), (x1, y1), (x2, y2), 1)
        return surf

    @staticmethod
    def generate_water_texture():
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        surf.fill(COLORS["water"])
        for _ in range(5):
            x = random.randint(0, TILE_SIZE)
            y = random.randint(0, TILE_SIZE)
            radius = random.randint(3, 8)
            pygame.draw.circle(surf, (50, 150, 255), (x, y), radius, 1)
        return surf

    @staticmethod
    def generate_sand_texture():
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        surf.fill(COLORS["sand"])
        for _ in range(20):
            x = random.randint(0, TILE_SIZE)
            y = random.randint(0, TILE_SIZE)
            pygame.draw.rect(surf, (210, 180, 140), (x, y, 1, 1))
        return surf

def generate_textures():
    """预生成所有纹理"""
    return {
        "grass": TextureGenerator.generate_grass_texture().convert(),
        "water": TextureGenerator.generate_water_texture().convert(),
        "sand": TextureGenerator.generate_sand_texture().convert()
    }