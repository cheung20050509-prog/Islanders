"""
记忆流系统和编年史系统
"""
import json
import time
import math
import logging
from enum import Enum
from typing import List, Tuple, Dict, Optional

# 记忆类型枚举
class MemoryType(Enum):
    OBSERVATION = "observation"  # 观察到的事件
    ACTION = "action"  # 自己的行动
    COMMUNICATION = "communication"  # 交流内容
    STATE = "state"  # 状态变化

# 记忆流系统
class MemoryStream:
    def __init__(self, owner_name: str):
        self.owner_name = owner_name
        self.memories = []
        self.load_from_json()

    def add(self, content: str, memory_type: MemoryType, importance: int = 5):
        """添加记忆，包含类型和重要性"""
        memory = {
            "timestamp": time.time(),
            "content": content,
            "type": memory_type.value,
            "importance": importance
        }
        if memory["type"] != "observation":
            self.memories.append(memory)
            self.save_to_json()

    def retrieve(self, query: str, limit: int = 5) -> List[str]:
        """根据时间、重要性和相关性检索记忆"""
        now = time.time()
        scored = []
        for mem in self.memories:
            # 计算时效性分数（最近的记忆分数高）
            recency = math.exp(-0.001 * (now - mem["timestamp"]))
            # 计算相关性分数
            relevance = sum(1 for w in query.split() if w in mem["content"]) / (len(query.split()) + 1)
            # 计算重要性分数
            importance = mem["importance"] / 10
            # 综合分数
            score = 0.4 * relevance + 0.3 * recency + 0.3 * importance
            scored.append((-score, mem["content"]))  # 负号用于升序排序
        return [c for _, c in sorted(scored)[:limit]]

    def get_communication_memories(self, limit: int = 10) -> List[Dict]:
        """获取communication类型的记忆"""
        communications = [m for m in self.memories if m["type"] == MemoryType.COMMUNICATION.value]
        # 按时间排序，取最近的
        communications.sort(key=lambda x: x["timestamp"], reverse=True)
        return communications[:limit]

    def save_to_json(self):
        """保存记忆到JSON文件"""
        with open(f"data/memory_{self.owner_name}.json", "w", encoding="utf-8") as f:
            json.dump(self.memories, f, ensure_ascii=False, indent=2)

    def load_from_json(self):
        """从JSON文件加载记忆"""
        try:
            with open(f"data/memory_{self.owner_name}.json", "r", encoding="utf-8") as f:
                self.memories = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.memories = []

    def check_reflection(self, bailian, npc_name: str,
                         importance_threshold: int = 7, count_threshold: int = 5):
        """检查是否需要触发反思，并生成新的高重要性记忆"""
        high_importance = [m for m in self.memories if m["importance"] >= importance_threshold]

        if len(high_importance) >= count_threshold:
            # 取最近的若干条重要记忆
            selected = high_importance[-count_threshold:]
            contents = [m["content"] for m in selected]

            prompt = f"""你是{npc_name}。
以下是你最近的一些重要记忆：
{json.dumps(contents, ensure_ascii=False, indent=2)}

请你进行一次反思，总结这些记忆中的规律或经验，并生成一条简短的反思性总结。"""

            try:
                summary = bailian.generate_response(npc_name, prompt)
                if summary:
                    self.add(f"反思总结: {summary}", MemoryType.STATE, importance=8)
                    return summary
            except Exception as e:
                logging.error(f"Reflection 生成失败: {e}")
        return None

# 全局编年史系统
class Chronicle:
    def __init__(self):
        self.events = []
        self.load_from_json()

    def add_event(self, agent_name: str, action: str, location: Tuple[float, float], details: str):
        """添加事件到编年史"""
        event = {
            "timestamp": time.time(),
            "agent": agent_name,
            "action": action,
            "location": (round(location[0], 1), round(location[1], 1)),
            "details": details
        }
        if event["action"]!="observation":
            print(f"{agent_name} {action} {location} {details}")
            self.events.append(event)
            self.save_to_json()

    def save_to_json(self):
        """保存编年史到JSON文件"""
        with open("data/chronicle.json", "w", encoding="utf-8") as f:
            json.dump(self.events, f, ensure_ascii=False, indent=2)

    def load_from_json(self):
        """从JSON文件加载编年史"""
        try:
            with open("data/chronicle.json", "r", encoding="utf-8") as f:
                self.events = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.events = []

    def get_recent_events(self, limit: int = 10) -> List[Dict]:
        """获取最近的事件"""
        return self.events[-limit:]