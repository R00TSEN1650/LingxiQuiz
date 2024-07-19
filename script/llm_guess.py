import gradio as gr
import time
import logging
from LingxiQuiz import LingxiClient

client: LingxiClient
instruction_query: str


def init_model(app_id, app_key, embedding_model, theme_selected, difficulty, temperature, top_p):
    global client
    global instruction_query
    # 配置日志记录
    # 清理已有 handlers
    root_logger = logging.getLogger()
    for h in root_logger.handlers:
        root_logger.removeHandler(h)
    current_time = time.strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"log/pattern2_log_{current_time}.txt"
    logging.basicConfig(level=logging.INFO, handlers=[
                        logging.FileHandler(log_filename, 'a', 'utf-8')])
    logging.info("【当前模式】：人猜机器回答")

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
    theme = "天文、航空与航天" if selected_theme == "仰望星空" else "生物"

    # 初始化谜题
    truth, range = client.Initialize_20Q_puzzle(selected_theme)
    
    state = "游戏中"

    # 初始化系统提示
    system_prompt = f"你正在参与“机器猜用户回答模式”的游戏，主题是“{selected_theme}”。在这个游戏中，被选择的谜底是“{truth}”，"\
                    f"接下来，机器会通过问问题的方式来猜测这个词。\n"\
                    f"你的回答只能是以下四种之一：'猜对了'、'是'、'否'、'不知道'。"\
                    f"请准备好，并根据机器的提问给予准确的回答。\n"\
                    f"谜底可能是以下词：{range}"
    
    history = [(None, system_prompt), (None, None)]

    # 打印初始系统提示词
    print("系统: ", history[0][1])

    instruction_query = f"假设你是一个猜谜语机器人，请和我玩一个游戏，我会在心中想一个和'{theme}'有关的名词。"\
                        f"你需要对我进行提问，问句只能是【一般疑问句】(是非疑问句)，注意不要重复之前的问题。"\
                        f"我的回答只会是以下四种之一：'猜对了'、'是'、'否'、'不知道'。你来推测我选择的名词是什么。"\
                        f"尽量用二分法逐步缩小范围，根据【过往对话】推测出谜底，不要重复提问相同问题。"\
                        f"请基于已知信息给出一个【一般疑问句】(是非疑问句)，尽量简洁。不要调用工具或者括号解释。\n"

    history = client.query_bot(history, instruction_query)
    return "游戏开始", history, state

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
    user_answer = message
    if user_answer not in ['猜对了', '是', '否', '不知道']:
        gr.Warning("无效的回答，请使用指定的回答格式：'猜对了'、'是'、'否'、'不知道'")
    else:
        # history[-1] = (user_answer, history[-1][1])
        history.append((user_answer, None))
        print("用户: ", history[-1][0])

        # 如果用户回答了"猜对了"，结束
        if user_answer == "猜对了":
            state = "猜对了"
            logging.info("机器猜对了关键词")
            gr.Info("机器猜对了关键词。点击“初始化模型”按钮可重新开始游戏。")
    return history, state


def update_chat(history, state, info):
    global client
    global instruction_query
    if state == "猜对了":
        history = history
        info = "机器猜对了关键词。点击“初始化模型”按钮可重新开始游戏。"
    else:
        # 生成机器提问
        history = client.query_bot(history, instruction_query)
        print("机器人: ", history[-1][1])
    return history, info


def toggle_button_state(state, button_1, button_2, button_3, button_4,):
    if state=="猜对了":
        return gr.Button(value="是", interactive=False), gr.Button(value="否", interactive=False), gr.Button(value="不知道", interactive=False), gr.Button(value="猜对了", interactive=False)
    else:
        return gr.Button(value="是", interactive=True), gr.Button(value="否", interactive=True), gr.Button(value="不知道", interactive=True), gr.Button(value="猜对了", interactive=True)


def change_llm_parameter(temperature, top_p):
    global client
    if client not in dir():
        return
    client.temperature = temperature
    client.top_p = top_p