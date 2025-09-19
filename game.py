"""
游戏主类 - 游戏逻辑和主循环
"""
import pygame
import random
import time
from ai_client import BailianClient
from dialog_system import GlobalDialogSystem
from memory_system import Chronicle
from world import World
from ui import UIRenderer
from config import *


class Game:
    def __init__(self, api_key: str = ""):
        self.bailian = BailianClient(api_key)
        self.dialog_system = GlobalDialogSystem()
        self.chronicle = Chronicle()
        self.world = World(self.bailian, self.dialog_system, self.chronicle)
        self.ui_renderer = UIRenderer()

        self.running = True
        self.show_help = False
        self.show_npc_conversations = True
        self.show_npc_details = False
        self.show_chronicle = False
        self.show_communications = True
        self.selected_npc = None
        self.keys = {}
        self.camera_x = WORLD_SIZE // 2 * TILE_SIZE
        self.camera_y = WORLD_SIZE // 2 * TILE_SIZE
        self.camera_offset_x = 0
        self.camera_offset_y = 0
        self.render_cache = {}
        self.last_render_time = 0
        self.frame_rate_limit = 30

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                # 退出时保存世界状态
                self.world.save_world_state()
            elif event.type == pygame.KEYDOWN:
                self.keys[event.key] = True
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    # 退出时保存世界状态
                    self.world.save_world_state()
                elif event.key == pygame.K_h:
                    self.show_help = not self.show_help
                elif event.key == pygame.K_c:
                    self.show_npc_conversations = not self.show_npc_conversations
                elif event.key == pygame.K_TAB:
                    self.show_npc_details = not self.show_npc_details
                elif event.key == pygame.K_b:
                    self.show_chronicle = not self.show_chronicle
                elif event.key == pygame.K_v:
                    self.show_communications = not self.show_communications
                elif event.key == pygame.K_SPACE:
                    if self.world.npcs:
                        alive_npcs = [npc for npc in self.world.npcs if not npc.is_dead]
                        if alive_npcs:
                            self.selected_npc = random.choice(alive_npcs)
                            self.camera_x = self.selected_npc.x * TILE_SIZE
                            self.camera_y = self.selected_npc.y * TILE_SIZE
            elif event.type == pygame.KEYUP:
                if event.key in self.keys:
                    del self.keys[event.key]
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_x, mouse_y = event.pos
                    world_x = (mouse_x - self.camera_offset_x) / TILE_SIZE
                    world_y = (mouse_y - self.camera_offset_y) / TILE_SIZE

                    for npc in self.world.npcs:
                        if not npc.is_dead and abs(npc.x - world_x) < 0.5 and abs(npc.y - world_y) < 0.5:
                            self.selected_npc = npc
                            break

    def update(self):
        current_time = time.time()

        if current_time - self.last_render_time < 1.0 / self.frame_rate_limit:
            return

        self.last_render_time = current_time

        # 处理相机移动
        camera_dx, camera_dy = 0, 0
        if pygame.K_w in self.keys or pygame.K_UP in self.keys:
            camera_dy -= CAMERA_SPEED
        if pygame.K_s in self.keys or pygame.K_DOWN in self.keys:
            camera_dy += CAMERA_SPEED
        if pygame.K_a in self.keys or pygame.K_LEFT in self.keys:
            camera_dx -= CAMERA_SPEED
        if pygame.K_d in self.keys or pygame.K_RIGHT in self.keys:
            camera_dx += CAMERA_SPEED

        if self.selected_npc and not self.selected_npc.is_dead:
            self.camera_x = self.selected_npc.x * TILE_SIZE
            self.camera_y = self.selected_npc.y * TILE_SIZE
        else:
            self.camera_x += camera_dx
            self.camera_y += camera_dy

            self.camera_x = max(0, min(WORLD_SIZE * TILE_SIZE, self.camera_x))
            self.camera_y = max(0, min(WORLD_SIZE * TILE_SIZE, self.camera_y))

        self.camera_offset_x = SCREEN_WIDTH // 2 - int(self.camera_x)
        self.camera_offset_y = (SCREEN_HEIGHT - HUD_HEIGHT) // 2 - int(self.camera_y)

        # 更新NPC状态
        for npc in self.world.npcs:
            if not npc.is_dead:
                npc.find_nearby_npcs(self.world.npcs)
                npc.find_nearby_resources(self.world)
                npc.interact_with_nearby_npcs()

                # 决策并执行行动
                action = npc.decide_action(self.world.get_state_str())
                npc.execute_action(action, self.world)

                npc.move_towards_target(self.world)

            npc.update(self.world)

        # 更新世界时间
        self.world.update_time()

    def draw(self, screen):
        screen.fill((0, 0, 0))

        # 渲染地形
        visible_area = pygame.Rect(
            self.camera_offset_x,
            self.camera_offset_y,
            SCREEN_WIDTH,
            SCREEN_HEIGHT - HUD_HEIGHT
        )
        screen.blit(self.world.terrain_surface, visible_area, visible_area)

        # 渲染NPC
        for npc in self.world.npcs:
            screen_x = int(npc.x * TILE_SIZE + self.camera_offset_x)
            screen_y = int(npc.y * TILE_SIZE + self.camera_offset_y)

            if (0 <= screen_x < SCREEN_WIDTH and 0 <= screen_y < SCREEN_HEIGHT - HUD_HEIGHT):
                npc.draw(screen, self.camera_offset_x, self.camera_offset_y)

                if npc == self.selected_npc:
                    pygame.draw.rect(screen, (255, 255, 0),
                                     (screen_x - 5, screen_y - 5, TILE_SIZE + 10, TILE_SIZE + 10), 2)

        # 绘制HUD
        self.ui_renderer.draw_hud(screen, self.world, self.camera_x, self.camera_y, self.selected_npc)

        if self.show_help:
            self.ui_renderer.draw_help(screen)

        if self.show_npc_conversations:
            self.ui_renderer.draw_npc_conversations(screen, self.dialog_system)

        if self.show_npc_details:
            self.ui_renderer.draw_npc_details(screen, self.world.npcs, self.selected_npc)

        if self.show_chronicle:
            self.ui_renderer.draw_chronicle(screen, self.chronicle)

        if self.show_communications:
            self.ui_renderer.draw_communication_events(screen, self.dialog_system)

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw(screen)
            clock.tick(FPS)
        pygame.quit()