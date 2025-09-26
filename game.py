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
import asyncio


class Game:
    def __init__(self, api_key: str = "", screen=None):
        # 初始化pygame和屏幕
        pygame.init()
        pygame.font.init()

        if screen is None:
            self.screen = pygame.display.set_mode(
                (SCREEN_WIDTH, SCREEN_HEIGHT),
                pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE
            )
            pygame.display.set_caption("荒岛模拟")
        else:
            self.screen = screen

        self.clock = pygame.time.Clock()

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

    async def update(self):
        # 更新NPC状态
        await asyncio.sleep(0.1)
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

    async def handle_camera_movement(self):
        """异步处理相机移动"""
        camera_dx, camera_dy = 0, 0
        move_speed = CAMERA_SPEED  # 确保在config.py中定义了CAMERA_SPEED

        # 检查方向键或WASD键
        if pygame.K_w in self.keys or pygame.K_UP in self.keys:
            camera_dy -= move_speed
        if pygame.K_s in self.keys or pygame.K_DOWN in self.keys:
            camera_dy += move_speed
        if pygame.K_a in self.keys or pygame.K_LEFT in self.keys:
            camera_dx -= move_speed
        if pygame.K_d in self.keys or pygame.K_RIGHT in self.keys:
            camera_dx += move_speed

        # 如果有选中的NPC且未死亡，相机跟随NPC
        if self.selected_npc and not self.selected_npc.is_dead:
            self.camera_x = self.selected_npc.x * TILE_SIZE
            self.camera_y = self.selected_npc.y * TILE_SIZE
        else:
            # 否则根据按键移动相机
            self.camera_x += camera_dx
            self.camera_y += camera_dy

            # 限制相机移动范围
            self.camera_x = max(0, min(WORLD_SIZE * TILE_SIZE, self.camera_x))
            self.camera_y = max(0, min(WORLD_SIZE * TILE_SIZE, self.camera_y))

        # 更新相机偏移量
        self.camera_offset_x = SCREEN_WIDTH // 2 - int(self.camera_x)
        self.camera_offset_y = (SCREEN_HEIGHT - HUD_HEIGHT) // 2 - int(self.camera_y)

        # 短暂休眠，允许其他任务运行
        await asyncio.sleep(0.01)

    def draw(self):
        self.screen.fill((0, 0, 0))

        # 渲染地形
        visible_area = pygame.Rect(
            self.camera_offset_x,
            self.camera_offset_y,
            SCREEN_WIDTH,
            SCREEN_HEIGHT - HUD_HEIGHT
        )
        self.screen.blit(self.world.terrain_surface, visible_area, visible_area)

        # 渲染NPC
        for npc in self.world.npcs:
            screen_x = int(npc.x * TILE_SIZE + self.camera_offset_x)
            screen_y = int(npc.y * TILE_SIZE + self.camera_offset_y)

            if (0 <= screen_x < SCREEN_WIDTH and 0 <= screen_y < SCREEN_HEIGHT - HUD_HEIGHT):
                npc.draw(self.screen, self.camera_offset_x, self.camera_offset_y)
                if npc == self.selected_npc:
                    pygame.draw.rect(self.screen, (255, 255, 0),
                                     (screen_x - 5, screen_y - 5, TILE_SIZE + 10, TILE_SIZE + 10), 2)

        # 绘制HUD
        self.ui_renderer.draw_hud(self.screen, self.world, self.camera_x, self.camera_y, self.selected_npc)

        if self.show_help:
            self.ui_renderer.draw_help(self.screen)

        if self.show_npc_conversations:
            self.ui_renderer.draw_npc_conversations(self.screen, self.dialog_system)

        if self.show_npc_details:
            self.ui_renderer.draw_npc_details(self.screen, self.world.npcs, self.selected_npc)

        if self.show_chronicle:
            self.ui_renderer.draw_chronicle(self.screen, self.chronicle)

        if self.show_communications:
            self.ui_renderer.draw_communication_events(self.screen, self.dialog_system)

        pygame.display.flip()

    def drawlater(self):
        self.screen.fill((0, 0, 0))

        # 渲染NPC
        for npc in self.world.npcs:
            screen_x = int(npc.x * TILE_SIZE + self.camera_offset_x)
            screen_y = int(npc.y * TILE_SIZE + self.camera_offset_y)

            if (0 <= screen_x < SCREEN_WIDTH and 0 <= screen_y < SCREEN_HEIGHT - HUD_HEIGHT):
                npc.draw(self.screen, self.camera_offset_x, self.camera_offset_y)

                if npc == self.selected_npc:
                    pygame.draw.rect(self.screen, (255, 255, 0),
                                     (screen_x - 5, screen_y - 5, TILE_SIZE + 10, TILE_SIZE + 10), 2)

        # 绘制HUD
        self.ui_renderer.draw_hud(self.screen, self.world, self.camera_x, self.camera_y, self.selected_npc)

        pygame.display.flip()

    async def update_time(self):
        """更新世界时间的异步任务"""
        for _ in range(10):
            await asyncio.sleep(0.1)
            self.world.update_time()
        print("时间更新")

    async def process_events(self):
        """处理事件的异步任务"""
        self.handle_events()
        await asyncio.sleep(0.1)
        print("处理事件")

    async def run(self):
        """主游戏循环"""
        self.draw()
        while self.running:
            self.draw()
            print("画完")
            # 同时运行所有异步任务：相机移动、更新、事件处理和时间更新
            await asyncio.gather(
                #self.handle_camera_movement(),
                self.update(),
                self.process_events(),
                self.update_time()
            )

            # 控制帧率
            await asyncio.sleep(1/self.frame_rate_limit)

        pygame.quit()
