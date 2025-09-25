"""
智能NPC类 - 完整版本
"""
import pygame
import json
import time
import math
import random
import re
import logging
from typing import List, Dict, Optional
from memory_system import MemoryStream, MemoryType
from config import *

class SmartNPC:
    def __init__(self, name: str, x: float, y: float, bailian,
                 dialog_system, chronicle):
        self.name = name
        self.x = x
        self.y = y
        self.bailian = bailian
        self.memory = MemoryStream(name)
        self.chronicle = chronicle
        self.state = "wandering"
        self.last_action_time = time.time()
        self.last_npc_interaction_time = time.time()
        self.first_meeting = True
        self.target_x, self.target_y = x, y
        self.speed = random.uniform(1.0, 2.0)
        self.dialog_system = dialog_system
        self.nearby_npcs = []
        self.nearby_resources = []

        # 生命体征
        self.health = 100
        self.energy = 100
        self.inventory = {
            "水": 0,
            "鱼": 0,
            "果实": 0
        }
        self.inventory_limits = {
            "水": 5,    # 每天消耗约12能量，每份水恢复10 → 上限5
            "鱼": 3,    # 每份鱼恢复20 → 上限3
            "果实": 4   # 每份果实恢复15 → 上限4
        }

        self.is_in_conversation = False
        self.conversation_partner = None
        self.conversation_cooldown = 0
        self.is_conversation_initiator = False
        self.last_conversation_time = 0
        self.is_dead = False

        # 模型调用冷却相关
        self.last_model_call_time = 0
        self.model_response_delay = random.uniform(1.0, 3.0)

        # 预生成名字标签
        self.name_surface = self._pre_render_name_tag(name)
        self.load_state()

    def _pre_render_name_tag(self, name):
        """预生成带背景的名字标签"""
        font_names = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC", "Arial Unicode MS"]
        small_font = pygame.font.SysFont(font_names, 16)
        bg_width = len(name) * 12 + 10
        bg_height = 20
        bg_surf = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA).convert_alpha()
        bg_surf.fill((0, 0, 0, 150))
        name_text = small_font.render(name, True, (255, 255, 255))
        text_x = (bg_width - name_text.get_width()) // 2
        text_y = (bg_height - name_text.get_height()) // 2
        bg_surf.blit(name_text, (text_x, text_y))
        return bg_surf

    def save_state(self):
        """保存NPC状态到JSON"""
        state = {
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "energy": self.energy,
            "inventory": self.inventory,
            "is_dead": self.is_dead
        }
        with open(f"data/npc_{self.name}.json", "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def load_state(self):
        """从JSON加载NPC状态"""
        try:
            with open(f"data/npc_{self.name}.json", "r", encoding="utf-8") as f:
                state = json.load(f)
                self.x = state["x"]
                self.y = state["y"]
                self.energy = state["energy"]
                self.inventory = state["inventory"]
                self.is_dead = state["is_dead"]
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def find_nearby_npcs(self, all_npcs: List['SmartNPC']):
        """找到附近的NPC"""
        self.nearby_npcs = []
        for other_npc in all_npcs:
            if other_npc != self and not other_npc.is_dead:
                distance = math.sqrt((self.x - other_npc.x) ** 2 + (self.y - other_npc.y) ** 2)
                if distance < VOLUME_LOUD_RANGE:
                    self.nearby_npcs.append(other_npc)

    def find_nearby_resources(self, world):
        """找到附近的资源"""
        self.nearby_resources = []
        for x in range(max(0, int(self.x) - 3), min(WORLD_SIZE, int(self.x) + 4)):
            for y in range(max(0, int(self.y) - 3), min(WORLD_SIZE, int(self.y) + 4)):
                if world.resources[x][y] and world.resource_amounts[x][y] > 0:
                    self.nearby_resources.append({
                        "type": world.resources[x][y],
                        "x": x,
                        "y": y,
                        "amount": world.resource_amounts[x][y]
                    })


    def talk(self, message: str):
        """说话，所有人都能听到（删除音量）"""
        if self.is_dead:
            return

        self.energy = max(0, self.energy - 2)
        self.memory.add(f"我说: {message}", MemoryType.COMMUNICATION, 7)

        # 记录到编年史
        self.chronicle.add_event(
            self.name,
            "说话",
            (self.x, self.y),
            f"说: {message}"
        )
        
        # 记录到世界行为日志
        self.chronicle.world.action_log.append({
            "actor": self.name,
            "action": "talk",
            "target": None,
            "message": message,
            "time": time.time()
        })

        # 所有NPC都能听到
        for npc in self.chronicle.world.npcs:
            if npc != self and not npc.is_dead:
                npc.hear_message(self, message)

    def hear_message(self, speaker, message: str):
        """听到消息（删除距离判断）"""
        self.memory.add(
            f"听到{speaker.name}说: {message}",
            MemoryType.COMMUNICATION,
            6
        )

        # 添加到全局对话系统
        self.dialog_system.add_conversation(speaker.name, self.name, message)
        self.dialog_system.add_communication_event(speaker.name, self.name, message)

    def gather_resource(self, resource: Dict, world):
        """采集资源（删除wood相关）"""
        if self.is_dead:
            return

        resource_type = resource["type"]
        resource_info = RESOURCE_TYPES[resource_type]
        gather_amount = min(resource_info["amount"], world.resource_amounts[resource["x"]][resource["y"]])
        
        # 检查库存上限
        target_item = resource_info["gather"]
        if self.inventory[target_item] + gather_amount > self.inventory_limits[target_item]:
            gather_amount = self.inventory_limits[target_item] - self.inventory[target_item]
            if gather_amount <= 0:
                self.memory.add(f"{target_item}库存已满，无法继续采集", MemoryType.ACTION, 5)
                return

        self.inventory[target_item] += gather_amount
        world.resource_amounts[resource["x"]][resource["y"]] -= gather_amount

        self.energy = max(0, self.energy - 5)
        self.memory.add(
            f"采集了{resource_info['name']}，获得{resource_info['gather']}{gather_amount}个，剩余{world.resource_amounts[resource['x']][resource['y']]}",
            MemoryType.ACTION,
            7
        )

        # 记录到编年史和行为日志
        self.chronicle.add_event(
            self.name,
            "采集",
            (self.x, self.y),
            f"采集了{resource_info['name']}，获得{resource_info['gather']}{gather_amount}个"
        )
        world.action_log.append({
            "actor": self.name,
            "action": "gather",
            "target": resource_type,
            "amount": gather_amount,
            "time": time.time()
        })

        # 保存世界状态
        world.save_resources()
    def eat(self):
        """吃东西恢复生命值和能量"""
        if self.is_dead:
            return

        # 寻找可食用的物品
        if self.inventory["果实"] > 0:
            self.inventory["果实"] -= 1
            self.health = min(100, self.health + 10)
            self.energy = min(100, self.energy + 20)
            self.memory.add("吃了1个果实，恢复了生命值和能量", MemoryType.ACTION, 6)
            self.chronicle.add_event(self.name, "进食", (self.x, self.y), "吃了1个果实")
        elif self.inventory["鱼"] > 0:
            self.inventory["鱼"] -= 1
            self.health = min(100, self.health + 15)
            self.energy = min(100, self.energy + 25)
            self.memory.add("吃了1条鱼，恢复了生命值和能量", MemoryType.ACTION, 6)
            self.chronicle.add_event(self.name, "进食", (self.x, self.y), "吃了1条鱼")

    def drink(self):
        """喝水恢复能量"""
        if self.is_dead:
            return

        if self.inventory["水"] > 0:
            self.inventory["水"] -= 1
            self.energy = min(100, self.energy + 30)
            self.memory.add("喝了1份水，恢复了能量", MemoryType.ACTION, 5)
            self.chronicle.add_event(self.name, "饮水", (self.x, self.y), "喝了1份水")

    def give(self, target_npc, resource_info):
            """给予资源给目标NPC"""
            if self.is_dead or target_npc.is_dead:
                return
                
            # 检查是否在同一坐标
            if not (abs(self.x - target_npc.x) < 1 and abs(self.y - target_npc.y) < 1):
                self.memory.add(f"想给{target_npc.name}东西，但不在同一位置", MemoryType.ACTION, 5)
                return
                
            # 解析资源信息（格式："水:1" 或 "鱼:2"）
            try:
                resource_type, amount = resource_info.split(":")
                amount = int(amount)
                if resource_type not in ["水", "鱼", "果实"]:
                    raise ValueError("无效资源类型")
            except:
                self.memory.add(f"给予格式错误，正确格式应为'资源:数量'", MemoryType.ACTION, 5)
                return
                
            # 检查自身是否有足够资源
            if self.inventory.get(resource_type, 0) < amount:
                self.memory.add(f"想给{target_npc.name}{resource_type}{amount}个，但数量不足", MemoryType.ACTION, 5)
                return
                
            # 检查目标是否有足够空间
            remaining_space = target_npc.inventory_limits[resource_type] - target_npc.inventory[resource_type]
            if remaining_space < amount:
                amount = remaining_space
                if amount <= 0:
                    self.memory.add(f"{target_npc.name}的{resource_type}库存已满，无法给予", MemoryType.ACTION, 5)
                    return
                    
            # 转移资源
            self.inventory[resource_type] -= amount
            target_npc.inventory[resource_type] += amount
            
            # 记录记忆
            self.memory.add(f"给了{target_npc.name}{resource_type}{amount}个", MemoryType.ACTION, 7)
            target_npc.memory.add(f"收到{self.name}给的{resource_type}{amount}个", MemoryType.ACTION, 7)
            
            # 记录到编年史和行为日志
            self.chronicle.add_event(
                self.name, "给予", (self.x, self.y), f"给了{target_npc.name}{resource_type}{amount}个"
            )
            self.chronicle.world.action_log.append({
                "actor": self.name,
                "action": "give",
                "target": target_npc.name,
                "resource": resource_type,
                "amount": amount,
                "time": time.time()
            })
            
            # 保存状态
            self.save_state()
            target_npc.save_state()


    def interact_with_nearby_npcs(self):
        """与附近的NPC交互"""
        if self.is_dead or self.is_in_conversation:
            return

        current_time = time.time()

        if self.conversation_cooldown > 0:
            self.conversation_cooldown -= 1
            return

        # 增加NPC互动间隔
        if self.nearby_npcs:
            available_npcs = [npc for npc in self.nearby_npcs if not npc.is_in_conversation]

            if available_npcs:
                if self.first_meeting:
                    self.first_meeting = False
                    target_npc = available_npcs[0]
                    self.greet_npc(target_npc)
                    self.last_npc_interaction_time = current_time
                # 增加互动间隔
                elif current_time - self.last_npc_interaction_time > random.uniform(20, 40):
                    target_npc = random.choice(available_npcs)
                    self.start_conversation_with(target_npc)
                    self.last_npc_interaction_time = current_time

    def greet_npc(self, target_npc):
        """初次见面问候"""
        greeting = f"{target_npc.name}你好"
        self.talk(greeting)
        target_npc.respond_to_greeting(self.name, greeting)

    def respond_to_greeting(self, speaker_name: str, message: str):
        """回应问候"""
        # 检查模型调用冷却
        current_time = time.time()
        if current_time - self.last_model_call_time < MODEL_CALL_COOLDOWN / 2:
            return

        self.last_model_call_time = current_time

        prompt = f"""你是{self.name}，第一次见到{speaker_name}。
{speaker_name}对你说: "{message}"
"""

        # 模拟思考延迟
        time.sleep(self.model_response_delay)

        response = self.bailian.generate_response(self.name, prompt)
        self.talk(response)

        # 添加到全局对话系统
        self.dialog_system.add_conversation(self.name, speaker_name, response)

    def start_conversation_with(self, target_npc):
        """开始与特定NPC的对话"""
        self.is_in_conversation = True
        self.conversation_partner = target_npc
        self.is_conversation_initiator = True
        self.last_conversation_time = time.time()

        target_npc.is_in_conversation = True
        target_npc.conversation_partner = self
        target_npc.is_conversation_initiator = False

        recent_memories = self.memory.retrieve("对话", 3)
        prompt = f"""你是{self.name}，正在与{target_npc.name}在荒岛上对话。
之前的交流: {recent_memories}
请说一句开始对话的话，说话请像人类，尽量自然。"""

        # 模拟思考延迟
        time.sleep(self.model_response_delay)

        response = self.bailian.generate_response(self.name, prompt)
        self.talk(response)
        target_npc.receive_message(self.name, response)

    def receive_message(self, speaker_name: str, message: str):
        """接收并回应消息"""
        # 检查模型调用冷却
        current_time = time.time()
        if current_time - self.last_model_call_time < MODEL_CALL_COOLDOWN / 2:
            return

        self.last_model_call_time = current_time

        recent_memories = self.memory.retrieve(f"{speaker_name} 对话", 3)
        prompt = f"""你是{self.name}，正在与{speaker_name}对话。
{speaker_name}对你说: "{message}"
之前的交流: {recent_memories}
请自然回应。"""

        # 模拟思考延迟
        time.sleep(self.model_response_delay)

        response = self.bailian.generate_response(self.name, prompt)
        self.talk(response)

        # 添加到全局对话系统
        self.dialog_system.add_conversation(self.name, speaker_name, response)

    def continue_conversation(self):
        """继续对话（只有发起者调用）"""
        if not self.conversation_partner or not self.is_conversation_initiator:
            return

        recent_memories = self.memory.retrieve("对话", 5)
        prompt = f"""你是{self.name}，正在与{self.conversation_partner.name}继续对话。
之前的交流: {recent_memories}
请继续对话，保持自然。"""

        # 模拟思考延迟
        time.sleep(self.model_response_delay)

        response = self.bailian.generate_response(self.name, prompt)
        self.talk(response)
        self.conversation_partner.receive_message(self.name, response)

    def should_end_conversation(self):
        """检查是否应该结束对话"""
        if not self.conversation_partner:
            return True

        return random.randint(1, 100) <= 10

    def set_move_away_target(self):
        """设置远离对话伙伴的目标位置"""
        if self.conversation_partner:
            dx = self.x - self.conversation_partner.x
            dy = self.y - self.conversation_partner.y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance > 0:
                move_distance = random.uniform(3, 5)
                self.target_x = max(0, min(WORLD_SIZE - 1, self.x + (dx / distance) * move_distance))
                self.target_y = max(0, min(WORLD_SIZE - 1, self.y + (dy / distance) * move_distance))

    def end_conversation(self):
        """结束对话"""
        if self.conversation_partner:
            partner = self.conversation_partner
            partner.is_in_conversation = False
            partner.conversation_partner = None
            partner.is_conversation_initiator = False
            partner.conversation_cooldown = 3 * FPS

        self.is_in_conversation = False
        self.conversation_partner = None
        self.is_conversation_initiator = False
        self.conversation_cooldown = 5 * FPS

        self.memory.add("结束了一次对话", MemoryType.ACTION, 5)

    def decide_action(self, world_state: str) -> Dict:
        """决定下一步行动"""
        if self.is_dead or self.is_in_conversation:
            return {"action": "idle", "target": None, "details": "无行动", "volume": None}

        # 每144帧检查一次决策（原来是72帧）
        current_time = time.time()
        if current_time - self.last_action_time > (144.0 / FPS):
            self.last_action_time = current_time
            self.last_model_call_time = current_time

            # 收集决策所需信息
            memories = self.memory.retrieve("决策", 5)
            nearby_npcs_info = f"附近有{len(self.nearby_npcs)}个NPC: {[npc.name for npc in self.nearby_npcs]}" if self.nearby_npcs else "附近没有其他NPC"
            nearby_resources_info = f"附近有{len(self.nearby_resources)}种资源: {[res['type'] for res in self.nearby_resources]}" if self.nearby_resources else "附近没有明显资源"
            inventory_info = f"背包: {', '.join([f'{k}:{v}' for k, v in self.inventory.items() if v > 0])}"
            vitals_info = f"生命值: {self.health}, 能量值: {self.energy}"

            prompt = f"""你是{self.name}，在荒岛上生存。
当前状态: {world_state}
生命状态: {vitals_info}
{nearby_npcs_info}
{nearby_resources_info}
{inventory_info}
最近的记忆: {memories}

请决定你接下来的行动。考虑你的生命值和能量，周围的资源和其他NPC。
如果能量低，考虑休息、吃东西或喝水。
如果看到资源，可以考虑采集。
如果看到其他NPC，很大可能交流。Communication时，不要太多考虑，直接和他人说话。
"""

            # 模拟思考延迟
            time.sleep(self.model_response_delay)

            try:
                response = self.bailian.generate_action(self.name, prompt)
                action_data = json.loads(response)
                return action_data
            except Exception as e:
                print(f"解析行动决策失败: {e}")
                return {"action": "rest", "target": None, "details": "暂时休息", "volume": None}
        return {"action": "idle", "target": None, "details": "无行动", "volume": None}

    def execute_action(self, action: Dict, world):
        """执行决策的行动"""
        if self.is_dead:
            return

        action_type = action.get("action", "idle")
        target = action.get("target")
        details = action.get("details", "")
        volume = action.get("volume", "normal")

        self.memory.add(f"周围环境: {world.get_state_str()}", MemoryType.OBSERVATION, 3)

        # 只对 move/gather 行为要求 target 为 dict
        if action_type in ("move", "gather") and isinstance(target, dict):
            self.target_x = max(0, min(WORLD_SIZE - 1, target.get("x", self.x)))
            self.target_y = max(0, min(WORLD_SIZE - 1, target.get("y", self.y)))
            self.memory.add(f"决定移动到({self.target_x:.1f}, {self.target_y:.1f}): {details}", MemoryType.ACTION, 4)
            if action_type == "gather":
                for resource in self.nearby_resources:
                    if (abs(resource["x"] - target.get("x", 0)) < 1 and
                            abs(resource["y"] - target.get("y", 0)) < 1):
                        self.gather_resource(resource, world)
                        break

        # 处理 talk 行为，target 为字符串（NPC 名称）
        elif action_type == "talk" and isinstance(target, str) and details:
            for npc in self.nearby_npcs:
                if npc.name == target:
                    self.talk(details, volume)

        # 处理 gather 行为，target 为字符串（资源类型）
        elif action_type == "gather" and isinstance(target, str):
            # 查找附近同类型的资源
            for resource in self.nearby_resources:
                if resource["type"] == target and resource["amount"] > 0:
                    self.gather_resource(resource, world)
                    break

        elif action_type == "eat":
            self.eat()

        elif action_type == "drink":
            self.drink()

        elif action_type == "rest":
            self.rest()

        else:
            # 其它情况或类型错误，记录日志但不报错
            if target is not None and not isinstance(target, str):
                logging.error(f"action target 类型错误: {target}")

    def process_action(self, action_data: dict, world):
        """处理AI生成的行动"""
        action = action_data.get("action")
        target = action_data.get("target")
        details = action_data.get("details", "")

        if action == "eat":
            self.perform_eat()
        elif action == "drink":
            self.perform_drink()

    def perform_eat(self):
        """执行进食行为"""
        if self.is_dead:
            return

        # 检查可食用资源
        if self.inventory["鱼"] > 0:
            resource = "鱼"
            energy_gain = 20
        elif self.inventory["果实"] > 0:
            resource = "果实"
            energy_gain = 15
        else:
            # 没有可食用资源
            self.memory.add(f"想吃东西，但没有鱼或果实了", MemoryType.ACTION, 6)
            self.chronicle.add_event(
                self.name, "尝试进食", (self.x, self.y), "没有可食用的资源"
            )
            return

        # 消耗资源并恢复能量
        self.inventory[resource] -= 1
        self.energy = min(100, self.energy + energy_gain)
        self.last_action_time = time.time()
        print(f"{self.name}吃了1个{resource}，能量恢复到{self.energy}")

        # 记录记忆和编年史
        self.memory.add(
            f"吃了1个{resource}，能量恢复到{self.energy}。剩余{resource}：{self.inventory[resource]}",
            MemoryType.ACTION, 7
        )
        self.chronicle.add_event(
            self.name, "进食", (self.x, self.y), f"食用了{resource}，能量+{energy_gain}"
        )
        self.save_state()

    def perform_drink(self):
        """执行饮水行为"""
        if self.is_dead:
            return

        # 检查水资源
        if self.inventory["水"] <= 0:
            self.memory.add("想喝水，但没有水了", MemoryType.ACTION, 6)
            self.chronicle.add_event(
                self.name, "尝试饮水", (self.x, self.y), "没有可饮用的水"
            )
            return

        # 消耗水并恢复能量
        self.inventory["水"] -= 1
        energy_gain = 10
        self.energy = min(100, self.energy + energy_gain)
        self.last_action_time = time.time()

        # 记录记忆和编年史
        self.memory.add(
            f"喝了1份水，能量恢复到{self.energy}。剩余水：{self.inventory['水']}",
            MemoryType.ACTION, 7
        )
        self.chronicle.add_event(
            self.name, "饮水", (self.x, self.y), f"饮用了水，能量+{energy_gain}"
        )
        self.save_state()

    def move_towards_target(self, world):
        """平滑移动到目标位置"""
        if self.is_dead or self.is_in_conversation:
            return

        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance > 0.1:
            next_x = self.x + (dx / distance) * self.speed / FPS
            next_y = self.y + (dy / distance) * self.speed / FPS

            tile_x, tile_y = int(next_x), int(next_y)
            if (0 <= tile_x < WORLD_SIZE and 0 <= tile_y < WORLD_SIZE):
                if world.tiles[tile_x][tile_y] != "water":
                    self.x = next_x
                    self.y = next_y
                    self.energy = max(0, self.energy - 0.02)
                    # 记录移动
                    self.memory.add(f"移动到({self.x:.1f}, {self.y:.1f})", MemoryType.ACTION, 2)
                else:
                    # 尝试绕开水域
                    alt_next_x, alt_next_y = self.x, self.y
                    if abs(dx) > abs(dy):
                        alt_next_x = next_x
                        if world.tiles[int(alt_next_x)][tile_y] == "water":
                            alt_next_x = self.x
                            alt_next_y = next_y
                    else:
                        alt_next_y = next_y
                        if world.tiles[tile_x][int(alt_next_y)] == "water":
                            alt_next_y = self.y
                            alt_next_x = next_x

                    alt_tile_x, alt_tile_y = int(alt_next_x), int(alt_next_y)
                    if (0 <= alt_tile_x < WORLD_SIZE and 0 <= alt_tile_y < WORLD_SIZE and
                            world.tiles[alt_tile_x][alt_tile_y] != "water"):
                        self.x = alt_next_x
                        self.y = alt_next_y
                        self.energy = max(0, self.energy - 0.02)
                        # 记录移动
                        self.memory.add(f"移动到({self.x:.1f}, {self.y:.1f})", MemoryType.ACTION, 2)

    def update(self, world):
        """更新NPC状态"""
        if self.is_dead:
            return

        # 自然消耗
        self.energy = max(0, self.energy - 0.01)

        # 能量过低影响生命值
        if self.energy < 20:
            self.health = max(0, self.health - 0.02)

        # 生命值为0则死亡
        if self.health <= 0:
            self.is_dead = True
            self.memory.add("因生命值耗尽而死亡", MemoryType.STATE, 10)
            self.chronicle.add_event(self.name, "死亡", (self.x, self.y), "因生命值耗尽而死亡")

        # 根据能量调整速度
        if self.energy < 30:
            self.speed = 0.5
        else:
            self.speed = random.uniform(1.5, 3.0)

        # 保存状态
        self.save_state()
        chance = random.randint(1, 10)
        if chance == 1:
            reflection = self.memory.check_reflection(self.bailian, self.name)
            if reflection:
                self.chronicle.add_event(self.name, "反思", (self.x, self.y), reflection)

    def draw(self, surf, offset_x, offset_y):
        """绘制NPC"""
        screen_x = int(self.x * TILE_SIZE + offset_x)
        screen_y = int(self.y * TILE_SIZE + offset_y)

        if -TILE_SIZE < screen_x < SCREEN_WIDTH and -TILE_SIZE < screen_y < SCREEN_HEIGHT:
            # 根据状态选择颜色
            if self.is_dead:
                color = COLORS["npc_dead"]
            elif self.is_in_conversation:
                color = COLORS["npc_talking"]
            else:
                color = COLORS["npc"]

            pygame.draw.circle(surf, color,
                               (screen_x + TILE_SIZE // 2, screen_y + TILE_SIZE // 2),
                               TILE_SIZE // 2 - 3)

            # 眼睛（死亡状态不显示）
            if not self.is_dead:
                pygame.draw.circle(surf, (0, 0, 0),
                                   (screen_x + TILE_SIZE // 2 - 5, screen_y + TILE_SIZE // 2 - 3), 2)
                pygame.draw.circle(surf, (0, 0, 0),
                                   (screen_x + TILE_SIZE // 2 + 5, screen_y + TILE_SIZE // 2 - 3), 2)

            # 绘制名字标签
            name_x = screen_x + TILE_SIZE // 2 - self.name_surface.get_width() // 2
            name_y = screen_y - 20
            surf.blit(self.name_surface, (name_x, name_y))


            # 能量值
            energy_percent = self.energy / 100
            pygame.draw.rect(surf, (100, 100, 0),
                             (screen_x, screen_y + TILE_SIZE + 7, TILE_SIZE, 4))
            pygame.draw.rect(surf, (255, 255, 0),
                             (screen_x, screen_y + TILE_SIZE + 7, int(TILE_SIZE * energy_percent), 4))
