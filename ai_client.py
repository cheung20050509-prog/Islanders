"""
阿里云百炼AI客户端
"""
import time
import json
import re
from http import HTTPStatus
from dashscope import Application

class BailianClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.kai_app_id = '61428035a8ce434091be8fa69d46d6c5'
        self.elara_app_id = '4a1b71350ea54ec6bedd304ac6938709'
        self.jax_app_id = 'c0b3c731180148c9ac1c56dc358fd267'
        self.kai_messages = []
        self.elara_messages = []
        self.jax_messages = []
        self.last_call_time = 0  # 记录上次调用时间
        self.call_cooldown = 10.0  # 调用冷却时间（秒）

    def generate_response(self, role: str, message: str) -> str:
        """调用百炼模型生成对应角色的回应"""
        # 检查冷却时间
        current_time = time.time()
        if current_time - self.last_call_time < self.call_cooldown:
            time.sleep(self.call_cooldown - (current_time - self.last_call_time))

        self.last_call_time = time.time()

        try:
            if role == "凯":
                app_id = self.kai_app_id
                messages = self.kai_messages
            elif role == "伊拉拉":
                app_id = self.elara_app_id
                messages = self.elara_messages
            elif role == "贾克斯":
                app_id = self.jax_app_id
                messages = self.jax_messages
            else:
                raise ValueError(f"未知角色: {role}")

            messages.append({'role': 'user', 'content': message})

            response = Application.call(
                api_key=self.api_key,
                app_id=app_id,
                messages=messages
            )

            if response.status_code == HTTPStatus.OK:
                assistant_reply = response.output.text.strip()
                messages.append({'role': 'assistant', 'content': assistant_reply})
                return assistant_reply
            else:
                print(f"百炼API错误: {response.status_code} - {response.message}")
                if messages and messages[-1]['role'] == 'user':
                    messages.pop()
                return ""

        except Exception as e:
            print(f"调用百炼模型失败: {str(e)}")
            if messages and messages[-1]['role'] == 'user':
                messages.pop()
            return ""

    def generate_action(self, role: str, prompt: str) -> str:
        """调用百炼模型生成角色行动决策"""
        # 检查冷却时间
        current_time = time.time()
        if current_time - self.last_call_time < self.call_cooldown:
            time.sleep(self.call_cooldown - (current_time - self.last_call_time))

        self.last_call_time = time.time()

        try:
            if role == "凯":
                app_id = self.kai_app_id
                messages = self.kai_messages
            elif role == "伊拉拉":
                app_id = self.elara_app_id
                messages = self.elara_messages
            else:
                app_id = self.jax_app_id
                messages = self.jax_messages

            system_prompt = """你需要根据提供的信息决定角色的下一步行动。
请以JSON格式返回，包含以下字段：
- action: 行动类型 (move, gather, eat, drink, give, talk, reflect)
- target: 目标位置(x,y)或目标对象名称，无目标则为null
- details: 行动细节描述
- volume: 若为talk行动，需指定volume为"normal"或"loud"，其他行动为null

示例: {"action": "move", "target": {"x": 10.5, "y": 7.2}, "details": "向东北方向移动寻找水源", "volume": null}
"""
            messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': prompt})

            response = Application.call(
                api_key=self.api_key,
                app_id=app_id,
                messages=messages
            )

            if response.status_code == HTTPStatus.OK:
                action_reply = response.output.text.strip()
                # 提取JSON部分
                json_match = re.search(r'\{.*\}', action_reply, re.DOTALL)
                if json_match:
                    action_reply = json_match.group()
                messages.append({'role': 'assistant', 'content': action_reply})
                return action_reply
            else:
                print(f"百炼API错误: {response.status_code} - {response.message}")
                if messages and messages[-1]['role'] == 'user':
                    messages.pop()
                if messages and messages[-1]['role'] == 'system':
                    messages.pop()
                # 返回默认的有效JSON响应
                return '{"action": "rest", "target": null, "details": "暂时休息", "volume": null}'

        except Exception as e:
            print(f"调用百炼模型失败: {str(e)}")
            if messages and messages[-1]['role'] == 'user':
                messages.pop()
            if messages and messages[-1]['role'] == 'system':
                messages.pop()
            # 返回默认的有效JSON响应
            return '{"action": "rest", "target": null, "details": "暂时休息", "volume": null}'