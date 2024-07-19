import gradio as gr
import time
import logging
from LingxiQuiz import LingxiClient

client: LingxiClient
instruction_query: str
instruction_answer: str

def init_model(app_id, app_key, embedding_model, theme_selected, difficulty, temperature, top_p):
    global client
    global instruction_answer
    global instruction_query

    # 配置日志记录
    # 清理已有 handlers
    root_logger = logging.getLogger()
    for h in root_logger.handlers:
        root_logger.removeHandler(h)
    current_time = time.strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"log/pattern3_log_{current_time}.txt"
    logging.basicConfig(level=logging.INFO, handlers=[
                        logging.FileHandler(log_filename, 'a', 'utf-8')])
    logging.info("【当前模式】：人和机器竞猜")

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

    # 初始化系统提示
    system_prompt = f"你正在参与“用户和机器竞猜模式”的游戏，主题是“{selected_theme}”。在这个游戏中，" \
                    f"你和猜词机器将轮流提问来猜测一个未知的谜题。" \
                    f"在这个过程中，你和猜测机器所提问题以及答案是共享的，" \
                    f"对于所有的问题，会有一个解答机器进行回答。" \
                    f"所有的问题只能是一般疑问句（是非问句）。" \
                    f"谁先猜出正确的谜底，谁就获得本次竞猜的胜利。\n"\
                    f"谜底可能是以下词：{range}"
    
    history = [(None, system_prompt)]

    # 打印初始系统提示词
    print("系统: ", history[0][1])

    instruction_answer = f"你是一个猜谜语解答助手机器人，用户将会对关于谜底是'{truth}'的谜题进行猜测，你负责基于事实出解答。" \
                         f"假如用户的【回复内容】不包含【谜底】'{truth}'，请根据关于谜底的事实来回答用户的问题"\
                         f"假如用户的【回复内容】不是一个【一般疑问句】(是非疑问句)，回复'您的回复不符合要求，我只能回答是或否'"\
                         f"如果用户的关于谜底的【问题】是正确的，回复'是'，否回复'否'。" \
                         f"不要在回复时透露【谜底】”{truth}“的多余信息。\n"

    instruction_query = f"假设你是一个猜谜语机器人，请和我玩一个游戏，我会在心中想一个和'{theme}'有关的名词。"\
                        f"你需要对我进行提问，问句只能是【一般疑问句】(是非疑问句)，注意不要重复之前的问题。"\
                        f"我的回答只会是以下四种之一：'猜对了'、'是'、'否'、'不知道'。你来推测我选择的名词是什么。"\
                        f"尽量用二分法逐步缩小范围，根据【过往对话】推测出谜底，不要重复提问相同问题。"\
                        f"请基于已知信息给出一个【一般疑问句】(是非疑问句)，尽量简洁。不要调用工具或者括号解释。\n"

    return "游戏开始", history

color_map = {
    "question": "crimson",
    "response": "green",
    "answer": "gray",
}




def add_message(history, message, user_turn):
    global client
    global instruction_answer
    # 用户回答
    state = "游戏中"
    user_question = message["text"]
    history.append(
        (client.make_html(user_question, "file/assets/human_icon.png"), None))
    print("用户: ", history[-1][0])
    user_turn = True

    # 打印聊天历史记录的最新交互
    print(f"用户提问: {history[-1][0]}")
    return history, gr.MultimodalTextbox(value=None, interactive=False), user_turn


def update_chat_q(history, state, user_turn, info):
    global client
    global instruction_query
    if state == "玩家猜对了":
        history = history
    else:
        # 生成机器提问
        history = client.query_bot(history, instruction_query, reverse_side=True)
        question = history[-1][0]
        print(f"猜词机器提问: {question}")
        user_turn = False
    return history, state, user_turn, info


def update_chat_a(history, state, user_turn, info):
    global client
    global instruction_answer
    if "猜对了" in state:
        history = history
    else:
        history = client.answer_bot(history, instruction_answer)
        print(f"解答机器回复: {history[-1][1]}")
    if "猜对了" in history[-1][1]:
        if user_turn:
            state = "玩家猜对了"
            info = "您已猜对关键词。点击“开始”按钮可重新开始游戏。"
        elif state != "玩家猜对了":
            state = "机器猜对了"
            info = "机器已猜对关键词。点击“开始”按钮可重新开始游戏。"

    if "猜对了" in state:
        history = history
        gr.Info(info)
    return history, state, user_turn, info


def change_llm_parameter(temperature, top_p):
    global client
    if client not in dir():
        return
    client.temperature = temperature
    client.top_p = top_p
