import pandas as pd
import gradio as gr
import logging
import random
import uuid
import requests
from auth_util import gen_sign_headers

class LingxiClient:
    def __init__(self, app_id, app_key, temperature, top_p, range_num):
        # 设置蓝心大模型 API 的参数
        self.app_id = app_id
        self.app_key = app_key
        self.uri = '/vivogpt/completions'
        self.domain = 'api-ai.vivo.com.cn'
        self.method = 'POST'
        self.temperature = temperature
        self.top_p = top_p
        self.knowledge_database = []
        self.selected_keyword = None
        self.selected_encyclopedia = None
        self.random_keys_str = None
        self.conversation_count = 0
        self.range_num = range_num

    # 函数：调用蓝心大模型生成聊天回复
    def chat(self, messages, systemPrompt):
        params = {
            'requestId': str(uuid.uuid4())
        }
        data = {
            'messages': messages,
            'model': 'vivo-BlueLM-TB',
            'sessionId': str(uuid.uuid4()),
            'extra': {
                'temperature': self.temperature,
                'top_p': self.top_p
            },
            'systemPrompt': systemPrompt
        }
        headers = gen_sign_headers(self.app_id, self.app_key, self.method, self.uri, params)
        headers['Content-Type'] = 'application/json'

        url = f'https://{self.domain}{self.uri}'
        response = requests.post(url, json=data, headers=headers, params=params)
        if response.status_code == 200:
            res_obj = response.json()
            if res_obj['code'] == 0 and res_obj.get('data'):
                content = res_obj['data']['content']
                return content
        else:
            logging.error(f"请求失败: {response.status_code} - {response.text}")
            return None


    def make_html(self, content, icon):
        return gr.HTML(f"""
            <div style="display: flex; padding: 0px 0px; margin-top: 0px;">
                <div style="padding: 10px; flex-shrink: 0;">
                    <!--CONTENT_BEGIN-->{content}<!--CONTENT_END-->
                </div>
                <div style="flex-shrink: 0; margin: 0px; width: 50px; height: 50px; background-image: url({icon}); background-size: cover; border-radius: 50%;" />
            </div>
        """)

    def extract_content(self, html: gr.HTML):
        html_string = html.value
        # 定位 content 开始的注释
        start = html_string.find("<!--CONTENT_BEGIN-->") + \
            len("<!--CONTENT_BEGIN-->")
        # 定位 content 结束的注释
        end = html_string.find("<!--CONTENT_END-->")
        # 截取并返回 content
        return html_string[start:end].strip()

    # 函数：猜词机器人提问
    def query_bot(self, history, instruction, reverse_side=False):
        self.conversation_count += 1  # 获取当前对话次数

        # 将 history 转换为 messages 格式
        messages = [{'role': 'user', 'content': '接下来让我们来开始猜词游戏！'}]
        for i, (user_text, assistant_text) in enumerate(history[2:], start=2):
            if isinstance(user_text, gr.HTML):
                user_text = self.extract_content(user_text)
            if isinstance(assistant_text, gr.HTML):
                assistant_text = self.extract_content(assistant_text)
            if reverse_side:
                messages.append({"role": "assistant", "content": user_text})
                messages.append({"role": "user", "content": assistant_text if assistant_text is not None else ""})
            else:
                if i % 2 == 0:
                    messages.append({"role": "assistant", "content": assistant_text})
                else:
                    messages.append({"role": "user", "content": user_text})

        # 确保 messages 的最后一个成员为当前请求的信息
        if len(messages) % 2 == 0:
            messages.pop()

        logging.info(f"【猜词：蓝心Prompt{self.conversation_count:02d}】 {messages}")
        chatResult = self.chat(messages, instruction + "谜底包含在以下词中：" + self.random_keys_str)
        logging.info(f"【猜词：蓝心Question{self.conversation_count:02d}】 {chatResult}\n")
        if reverse_side:
            history.append(
                (self.make_html(chatResult, "file/assets/robot_icon.jpg"), None))
        else:
            history.append((None, chatResult))
        return history

    # 函数：解答机器人回复
    def answer_bot(self, history, instruction):

        # 只记录最新的一组对话
        print(history)
        latest_user_text = history[-1][0]
        print(latest_user_text)
        if isinstance(latest_user_text, gr.HTML):
            latest_user_text = self.extract_content(latest_user_text)

        messages = [{"role": "user", "content": latest_user_text}]

        self.conversation_count += 1  # 获取当前对话次数
        logging.info(f"【解答：蓝心Prompt{self.conversation_count:02d}】 {messages}")
        if self.selected_keyword in latest_user_text:
            chatResult = "猜对了"
        else:
            chatResult = self.chat(messages, instruction + "回答时参考谜底的百科：" + self.selected_encyclopedia)
            chatResult = "是。" if chatResult and chatResult[0] in ["是", "对","正确"] else "否。"
        logging.info(f"【解答：蓝心Answer{self.conversation_count:02d}】 {chatResult}\n")
        history[-1] = (history[-1][0], chatResult)
        return history

    # 函数：从知识库中随机选择一个关键词
    def select_keyword(self):
        if not self.knowledge_database:
            raise ValueError("Knowledge keywords are not loaded.")
        self.selected_keyword = random.choice(list(self.knowledge_database.keys()))
        self.selected_encyclopedia = self.knowledge_database[self.selected_keyword]
        self.random_keys_str = self.random_keys_with_selected(self.selected_keyword, self.range_num)
        logging.info(f"【机器选择的词】 {self.selected_keyword}")
        logging.info(f"【选择词的百科】{self.selected_encyclopedia}")
        logging.info(f"【谜底的范围】{self.random_keys_str}")
        return self.selected_keyword, self.random_keys_str

    # 函数：生成随机的猜词范围
    def random_keys_with_selected(self, selected_key, num=10):
        # 检查 selected_key 是否在知识库中
        if selected_key not in self.knowledge_database:
            raise ValueError(f"Selected key '{selected_key}' 不在知识库中。")
        # 检查请求的键的数量是否超过知识库的大小
        if num > len(self.knowledge_database):
            raise ValueError("请求的键的数量超过了知识库的大小。")

        # 获取所有的键并确保包含 selected_key
        keys = list(self.knowledge_database.keys())
        keys.remove(selected_key)  # 移除 selected_key 以便稍后添加
        # 从剩余的键中随机选择 (num - 1) 个键
        random_keys = random.sample(keys, num - 1)
        # 将 selected_key 添加回已选择的键中
        random_keys.append(selected_key)
        # 打乱最终列表的顺序
        random.shuffle(random_keys)
        # 将列表转换为用分号隔开的字符串
        random_keys_str = "；".join(random_keys) + "。"
        return random_keys_str

    # 函数：初始化20Q谜题
    def Initialize_20Q_puzzle(self, theme):
        # 通过用户所选主题进行知识库初始化
        theme_files = {
            "仰望星空": "data/仰望星空.xlsx",
            "生灵探密": "data/生灵探密.xlsx",
        }
        if theme not in theme_files:
            raise ValueError("Invalid theme selected.")
        data = pd.read_excel(theme_files[theme])

        # 将数据转换为字典
        self.knowledge_database = dict(zip(data['keyword'], data['encyclopedia']))

        chosen_keyword, random_keys_str = self.select_keyword()
        return chosen_keyword, random_keys_str