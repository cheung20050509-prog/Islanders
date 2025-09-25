"""
全局对话系统
"""
import json
import time
from typing import List, Tuple, Dict

class GlobalDialogSystem:
    def __init__(self):
        self.npc_conversations = []
        self.communication_events = []  # 专门存储communication类型的互动
        self.max_conversations = 20
        self.max_communication_events = 50

    def add_conversation(self, npc1_name: str, npc2_name: str, message: str):
        timestamp = time.time()
        self.npc_conversations.append((npc1_name, npc2_name, message, timestamp))
        if len(self.npc_conversations) > self.max_conversations:
            self.npc_conversations.pop(0)
        self.save_to_json(npc1_name, npc2_name, message, timestamp)

    def add_communication_event(self, speaker_name: str, listener_name: str, message: str):
        """添加communication类型的互动事件"""
        timestamp = time.time()
        event = {
            "timestamp": timestamp,
            "speaker": speaker_name,
            "listener": listener_name,
            "message": message
        }
        self.communication_events.append(event)
        if len(self.communication_events) > self.max_communication_events:
            self.communication_events.pop(0)

    def get_recent_communications(self, limit: int = 10) -> List[Dict]:
        """获取最近的communication事件"""
        return self.communication_events[-limit:]

    def get_recent_conversations(self) -> List[Tuple[str, str, str, float]]:
        current_time = time.time()
        return [(n1, n2, msg, t) for n1, n2, msg, t in self.npc_conversations
                if current_time - t < 60]

    def save_to_json(self, npc1_name: str, npc2_name: str, message: str, timestamp: float):
        """保存对话到JSON文件"""
        conversation_data = {
            "timestamp": timestamp,
            "npc1": npc1_name,
            "npc2": npc2_name,
            "message": message
        }

        try:
            with open("data/conversations.json", "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []

        data.append(conversation_data)

        with open("data/conversations.json", "w", encoding="utf-8") as f:

            json.dump(data, f, ensure_ascii=False, indent=2)
