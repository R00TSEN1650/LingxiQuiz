import gradio as gr
import time
import logging
from LingxiQuiz import LingxiClient

client: LingxiClient
instruction_answer: str

def init_model(app_id, app_key, embedding_model, theme_selected, difficulty, temperature, top_p):
    global client
    global instruction_answer

    # 配置日志记录
    # 清理已有 handlers
    root_logger = logging.getLogger()
    for h in root_logger.handlers:
        root_logger.removeHandler(h)
    current_time = time.strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"log/pattern1_log_{current_time}.txt"
    logging.basicConfig(level=logging.INFO, handlers=[
                        logging.FileHandler(log_filename, 'a', 'utf-8')])
    logging.info("【当前模式】：机器猜人回答")

    # 处理难度对应猜词范围数，简单难度 5 ，普通难度 10，困难难度 20
    range_num = {
        "简单": 5,
        "普通": 10,
        "困难": 20
    }
    if difficulty not in range_num:
        raise ValueError("Invalid difficulty selected.")

    # 创建 LingxiClient 实例
    client = LingxiClient(app_id, app_key, temperature, top_p, range_num[difficulty])
    client.model = embedding_model
    client.temperature = temperature
    client.top_p = top_p

    # 用户选择主题
    selected_theme = theme_selected

    # 初始化谜题
    truth, range = client.Initialize_20Q_puzzle(selected_theme)


    # 初始化系统提示
    system_prompt = f"你正在参与“用户猜机器回答模式”的游戏，主题是“{selected_theme}”。在这个游戏中，机器已经选择了一个词，"\
                    f"你需要通过提问来猜测这个词。每次提问后，机器将根据你的问题给出回答。请开始你的提问吧！\n"\
                    f"谜底可能是以下词：{range}"
    
    history = [(None, system_prompt)]

    # 打印初始系统提示词
    print("系统: ", history[0][1])
    
    instruction_answer = f"你是一个猜谜语解答助手机器人，用户将会对关于谜底是'{truth}'的谜题进行猜测，你负责基于事实出解答。" \
                         f"假如用户的【回复内容】不包含【谜底】'{truth}'，请根据关于谜底的事实来回答用户的问题"\
                         f"假如用户的【回复内容】不是一个【一般疑问句】(是非疑问句)，回复'您的回复不符合要求，我只能回答是或否'"\
                         f"如果用户的关于谜底的【问题】是正确的，回复'是'，否回复'否'。" \
                         f"不要在回复时透露【谜底】”{truth}“的多余信息。\n"
    return "游戏开始", history

color_map = {
    "question": "crimson",
    "response": "green",
    "answer": "gray",
}


def html_src(content, color_idx):
    return f"""
<div style="display: flex; gap: 5px;padding: 20px 4px;margin-top: 0px">
  <div style="background-color: {color_map[color_idx]}; padding: 10px; border-radius: 5px;">
  {content}
  </div>
</div>
"""


def add_message(history, message):
    # 用户回答
    state = "游戏中"
    user_answer = message["text"]
    history.append((user_answer, None))
    print("用户: ", history[-1][0])
    return history, gr.MultimodalTextbox(value=None, interactive=False)


def update_chat(history, state, info):
    global client
    global instruction_answer
    history = client.answer_bot(history, instruction_answer)
    print("机器人: ", history[-1][1])
    if "猜对了" in history[-1][1]:
        state = "猜对了"

    if state == "猜对了":
        history = history
        info = "您已猜对关键词。点击“初始化模型”按钮可重新开始游戏。"
        gr.Info("您已猜对关键词。点击“初始化模型”按钮可重新开始游戏。")
    return history, state, info


def change_llm_parameter(temperature, top_p):
    global client
    if client not in dir():
        return
    client.temperature = temperature
    client.top_p = top_p
