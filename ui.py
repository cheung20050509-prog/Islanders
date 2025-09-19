"""
UI绘制系统 - 所有UI相关的绘制功能
"""
import pygame
import time
from config import *

class UIRenderer:
    def __init__(self):
        # 初始化字体
        self.game_font, self.small_font, self.large_font, self.tiny_font = init_fonts()

    def draw_hud(self, screen, world, camera_x, camera_y, selected_npc):
        """绘制HUD"""
        pygame.draw.rect(screen, COLORS["ui"],
                         (0, SCREEN_HEIGHT - HUD_HEIGHT, SCREEN_WIDTH, HUD_HEIGHT))
        pygame.draw.line(screen, (200, 200, 200),
                         (0, SCREEN_HEIGHT - HUD_HEIGHT),
                         (SCREEN_WIDTH, SCREEN_HEIGHT - HUD_HEIGHT), 2)

        world_state_text = self.large_font.render(world.get_state_str(), True, (255, 255, 255))
        screen.blit(world_state_text, (20, SCREEN_HEIGHT - HUD_HEIGHT + 15))

        camera_text = self.game_font.render(
            f"相机位置: ({int(camera_x / TILE_SIZE)}, {int(camera_y / TILE_SIZE)})",
            True, (200, 200, 200))
        screen.blit(camera_text, (20, SCREEN_HEIGHT - HUD_HEIGHT + 50))

        alive_npcs = [npc for npc in world.npcs if not npc.is_dead]
        npc_count_text = self.game_font.render(f"存活NPC数量: {len(alive_npcs)}/{len(world.npcs)}", True,
                                          (200, 200, 200))
        screen.blit(npc_count_text, (300, SCREEN_HEIGHT - HUD_HEIGHT + 50))

        if selected_npc:
            status = "死亡" if selected_npc.is_dead else "对话中" if selected_npc.is_in_conversation else "空闲"
            selected_text = self.game_font.render(
                f"选中: {selected_npc.name} - 生命值: {int(selected_npc.health)} - 能量: {int(selected_npc.energy)} - {status}",
                True, (255, 215, 0))
            screen.blit(selected_text, (20, SCREEN_HEIGHT - HUD_HEIGHT + 80))

        hint_text = self.tiny_font.render(
            "WASD/方向键:移动相机 | H:帮助 | C:NPC对话 | V:互动记录 | TAB:NPC详情 | B:全局事件 | 空格:随机聚焦 | 鼠标左键:选择NPC",
            True, (200, 200, 200)
        )
        screen.blit(hint_text, (SCREEN_WIDTH - hint_text.get_width() - 20,
                                SCREEN_HEIGHT - 25))

    def draw_npc_conversations(self, screen, dialog_system):
        """绘制NPC对话记录"""
        conv_rect = pygame.Rect(SCREEN_WIDTH - 400, 10, 390, 300)
        pygame.draw.rect(screen, (20, 20, 20, 200), conv_rect)
        pygame.draw.rect(screen, (100, 100, 100), conv_rect, 2)

        title = self.game_font.render("NPC对话", True, (255, 215, 0))
        screen.blit(title, (SCREEN_WIDTH - 390, 15))

        conversations = dialog_system.get_recent_conversations()

        if not conversations:
            no_conv_text = self.small_font.render("暂无对话", True, (150, 150, 150))
            screen.blit(no_conv_text, (SCREEN_WIDTH - 380, 50))
        else:
            y_offset = 45
            for npc1, npc2, message, timestamp in conversations[-8:]:
                time_diff = time.time() - timestamp
                if time_diff < 60:
                    time_str = f"{int(time_diff)}秒前"
                else:
                    time_str = f"{int(time_diff / 60)}分钟前"

                header_text = self.tiny_font.render(f"{npc1} → {npc2} ({time_str})", True, (200, 200, 100))
                screen.blit(header_text, (SCREEN_WIDTH - 380, y_offset))
                y_offset += 15

                # 处理长消息换行
                max_width = 360
                words = message.split(' ')
                lines = []
                current_line = ""

                for word in words:
                    test_line = current_line + word + " "
                    if self.tiny_font.size(test_line)[0] < max_width:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line.strip())
                        current_line = word + " "

                if current_line:
                    lines.append(current_line.strip())

                for line in lines[:2]:
                    if y_offset < 280:
                        msg_text = self.tiny_font.render(line, True, (255, 255, 255))
                        screen.blit(msg_text, (SCREEN_WIDTH - 370, y_offset))
                        y_offset += 15

                y_offset += 5

                if y_offset > 290:
                    break

    def draw_communication_events(self, screen, dialog_system):
        """绘制communication类型互动"""
        comm_rect = pygame.Rect(10, 320, 300, 250)
        pygame.draw.rect(screen, (20, 20, 20, 200), comm_rect)
        pygame.draw.rect(screen, (100, 100, 100), comm_rect, 2)

        title = self.game_font.render("互动记录", True, (255, 215, 0))
        screen.blit(title, (20, 325))

        communications = dialog_system.get_recent_communications(8)
        y_offset = 360

        if not communications:
            no_comm_text = self.small_font.render("暂无互动记录", True, (150, 150, 150))
            screen.blit(no_comm_text, (30, 370))
        else:
            for comm in reversed(communications):
                timestamp = comm["timestamp"]
                time_diff = time.time() - timestamp
                if time_diff < 60:
                    time_str = f"{int(time_diff)}秒前"
                elif time_diff < 3600:
                    time_str = f"{int(time_diff / 60)}分钟前"
                else:
                    time_str = f"{int(time_diff / 3600)}小时前"

                header_text = self.tiny_font.render(
                    f"{comm['speaker']} 对 {comm['listener']} 说 ({time_str})",
                    True, (200, 200, 100)
                )
                screen.blit(header_text, (20, y_offset))
                y_offset += 15

                # 处理长消息换行
                max_width = 270
                words = comm["message"].split(' ')
                lines = []
                current_line = ""

                for word in words:
                    test_line = current_line + word + " "
                    if self.tiny_font.size(test_line)[0] < max_width:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line.strip())
                        current_line = word + " "

                if current_line:
                    lines.append(current_line.strip())

                for line in lines[:2]:
                    if y_offset < 550:
                        msg_text = self.tiny_font.render(line, True, (255, 255, 255))
                        screen.blit(msg_text, (30, y_offset))
                        y_offset += 15

                y_offset += 5

                if y_offset > 550:
                    break

        close_text = self.tiny_font.render("按V关闭互动记录", True, (200, 200, 200))
        screen.blit(close_text, (comm_rect.centerx - close_text.get_width() // 2, comm_rect.bottom - 20))

    def draw_npc_details(self, screen, npcs, selected_npc):
        """绘制NPC详细信息"""
        detail_rect = pygame.Rect(10, 10, 300, 300)
        pygame.draw.rect(screen, (20, 20, 20, 200), detail_rect)
        pygame.draw.rect(screen, (100, 100, 100), detail_rect, 2)

        title = self.game_font.render("NPC状态", True, (255, 215, 0))
        screen.blit(title, (20, 15))

        y_offset = 45
        for npc in npcs:
            color = (255, 255, 0) if npc == selected_npc else (255, 255, 255)
            status_text = f"{npc.name} {'(死亡)' if npc.is_dead else ''}"
            name_text = self.small_font.render(status_text, True, color)
            screen.blit(name_text, (20, y_offset))

            pos_text = self.tiny_font.render(f"位置: ({int(npc.x)}, {int(npc.y)})", True, (200, 200, 200))
            screen.blit(pos_text, (100, y_offset))

            # 生命值条
            hp_percent = npc.health / 100
            pygame.draw.rect(screen, (100, 0, 0), (20, y_offset + 20, 120, 4))
            pygame.draw.rect(screen, (255, 0, 0), (20, y_offset + 20, int(120 * hp_percent), 4))
            hp_text = self.tiny_font.render(f"生命值: {int(npc.health)}", True, (200, 200, 200))
            screen.blit(hp_text, (150, y_offset + 15))

            # 能量条
            energy_percent = npc.energy / 100
            pygame.draw.rect(screen, (100, 100, 0), (20, y_offset + 40, 120, 4))
            pygame.draw.rect(screen, (255, 255, 0), (20, y_offset + 40, int(120 * energy_percent), 4))
            energy_text = self.tiny_font.render(f"能量值: {int(npc.energy)}", True, (200, 200, 200))
            screen.blit(energy_text, (150, y_offset + 35))

            # 物品栏
            inventory_items = [f"{k}:{v}" for k, v in npc.inventory.items() if v > 0]
            if inventory_items:
                inv_text = self.tiny_font.render(f"物品: {', '.join(inventory_items)}", True, (200, 200, 200))
                screen.blit(inv_text, (20, y_offset + 60))
                y_offset += 20

            # 显示对话状态
            if npc.is_in_conversation and not npc.is_dead:
                conv_text = self.tiny_font.render(f"正在与{npc.conversation_partner.name}对话", True, (100, 150, 255))
                screen.blit(conv_text, (20, y_offset + 60))
                y_offset += 15

            y_offset += 80

            if y_offset > 280:
                break

    def draw_chronicle(self, screen, chronicle):
        """绘制编年史"""
        chronicle_rect = pygame.Rect(SCREEN_WIDTH // 4, 10, SCREEN_WIDTH // 2, 400)
        pygame.draw.rect(screen, (20, 20, 20, 200), chronicle_rect)
        pygame.draw.rect(screen, (100, 100, 100), chronicle_rect, 2)

        title = self.game_font.render("全局事件编年史", True, (255, 215, 0))
        screen.blit(title, (chronicle_rect.centerx - title.get_width() // 2, 15))

        events = chronicle.get_recent_events(10)
        y_offset = 50

        if not events:
            no_event_text = self.small_font.render("暂无事件记录", True, (150, 150, 150))
            screen.blit(no_event_text, (chronicle_rect.centerx - no_event_text.get_width() // 2, 100))
        else:
            # 倒序显示，最新的在上面
            for event in reversed(events):
                timestamp = event["timestamp"]
                time_diff = time.time() - timestamp
                if time_diff < 60:
                    time_str = f"{int(time_diff)}秒前"
                elif time_diff < 3600:
                    time_str = f"{int(time_diff / 60)}分钟前"
                else:
                    time_str = f"{int(time_diff / 3600)}小时前"

                location = event["location"]
                header_text = self.small_font.render(
                    f"{event['agent']} 在({location[0]},{location[1]}) {event['action']} - {time_str}",
                    True, (255, 215, 0)
                )
                screen.blit(header_text, (chronicle_rect.left + 20, y_offset))
                y_offset += 25

                details_text = self.tiny_font.render(f"详情: {event['details']}", True, (255, 255, 255))
                screen.blit(details_text, (chronicle_rect.left + 30, y_offset))
                y_offset += 20

                if y_offset > chronicle_rect.bottom - 30:
                    break

        close_text = self.small_font.render("按B关闭编年史", True, (200, 200, 200))
        screen.blit(close_text, (chronicle_rect.centerx - close_text.get_width() // 2, chronicle_rect.bottom - 30))

    def draw_help(self, screen):
        """绘制帮助界面"""
        help_bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT - HUD_HEIGHT), pygame.SRCALPHA)
        help_bg.fill((0, 0, 0, 200))
        screen.blit(help_bg, (0, 0))

        title = self.large_font.render("游戏帮助 - 上帝视角", True, (255, 215, 0))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

        help_items = [
            ("WASD/方向键", "移动相机视角"),
            ("鼠标左键", "点击选择NPC"),
            ("空格", "随机聚焦到一个NPC"),
            ("C", "显示/隐藏NPC对话记录"),
            ("V", "显示/隐藏互动记录"),
            ("TAB", "显示/隐藏NPC详细信息"),
            ("B", "显示/隐藏全局事件编年史"),
            ("H", "显示/隐藏帮助"),
            ("ESC", "退出游戏")
        ]

        for i, (key, desc) in enumerate(help_items):
            key_text = self.game_font.render(key, True, (255, 215, 0))
            desc_text = self.game_font.render(desc, True, (255, 255, 255))

            screen.blit(key_text, (SCREEN_WIDTH // 2 - 200, 150 + i * 50))
            screen.blit(desc_text, (SCREEN_WIDTH // 2 - 50, 150 + i * 50))

        info_title = self.game_font.render("游戏说明:", True, (255, 100, 100))
        screen.blit(info_title, (SCREEN_WIDTH // 2 - 200, 500))

        info_items = [
            "• 你是上帝视角，可以观察整个岛屿",
            "• NPC会自主行动和对话",
            "• 蓝色NPC表示正在对话中",
            "• 黄色NPC表示空闲状态",
            "• 灰色NPC表示已死亡",
            "• NPC有生命值和能量值，需要通过进食和休息维持",
            "• 岛上有各种资源可供采集利用",
            "• 选中NPC后相机会自动跟随"
        ]

        for i, info in enumerate(info_items):
            info_text = self.small_font.render(info, True, (255, 255, 255))
            screen.blit(info_text, (SCREEN_WIDTH // 2 - 180, 530 + i * 25))

        close_text = self.small_font.render("按H关闭帮助", True, (200, 200, 200))
        screen.blit(close_text, (SCREEN_WIDTH // 2 - close_text.get_width() // 2,
                                 SCREEN_HEIGHT - HUD_HEIGHT - 30))