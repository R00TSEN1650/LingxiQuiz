import gradio as gr
import os
session_states = {}


# PAGES can be in external files
def get_not_found_page(local_state):
    with gr.Column() as result:
        gr.Markdown("# 404 - PAGE NOT FOUND")

        gr.Markdown(f"# *{local_state.get('page')}*页面走丢了！请点击左侧导航栏以跳转至游戏")
    return result


def get_home_page(local_state):
    with gr.Column() as result:
        gr.Markdown("# 欢迎")

        gr.Markdown(f"## 请点击左侧导航栏以跳转至游戏。")
        gr.Markdown(f"## ---游戏说明---\n\n"
                    f"### 欢迎来到 **LingxiQuiz**，一个充满乐趣和智慧挑战的20问猜谜游戏！\n"\
                    f"#### 交互模式：\n\n"
                    f"- **⁉️ 人机竞猜**：用户与AI进行对抗，轮流提问和回答，通过团队协作与策略制定赢得胜利。\n\n"
                    f"- **❓ 机器出题，人类猜谜**：AI生成谜底，用户进行猜测，挑战不同类型的知识。\n\n"
                    f"- **❗ 人类出题，机器猜谜**：用户设计谜底，AI进行猜测，考验AI的推理和判断能力。\n\n"
                    f"选择你的模式，开启一场智慧与趣味的猜谜之旅吧！\n")
    return result


def get_compete_page(local_state):
    import guess_compete
    with gr.Column() as result:
        gr.Markdown("# 竞猜")

        with gr.Blocks(css=".component.svelte-x4qvqz.svelte-x4qvqz{max-width:100%;}") as demo:
            with gr.Row(equal_height=False):
                with gr.Column(scale=1):
                    with gr.Row(equal_height=True):
                        with gr.Column(scale=1):
                            app_id = gr.Textbox(
                                label='app_id', type="password", value="")
                            app_key = gr.Textbox(
                                label='app_key', type="password", value="")
                    with gr.Column(scale=1, variant='panel'):
                        embedding_model = gr.Dropdown(choices=['vivo-BlueLM-TB'],
                                                      value='vivo-BlueLM-TB',
                                                      label="选择模型")
                        theme_selected = gr.Dropdown(choices=['生灵探密', '仰望星空'],
                                                     value='生灵探密',
                                                     label="选择主题")
                        difficulty = gr.Radio(
                            choices=['简单', '普通', '困难'], value='简单', label='难度选择')

                        with gr.Accordion(label="文本生成调整参数", open=False):
                            temperature = gr.Slider(
                                label="temperature", minimum=0.1, maximum=1, value=0.7, step=0.05)
                            top_p = gr.Slider(label="top_p", minimum=0,
                                              maximum=1, value=0.9, step=0.05)

                    with gr.Column(scale=1, variant='default'):
                        vector_index_btn = gr.Button(
                            '开始', variant='primary', scale=1)
                        vector_index_msg_out = gr.Markdown("尚未开始...")

                with gr.Column(scale=2):
                    chatbot = gr.Chatbot(
                        elem_id="chatbot",
                        bubble_full_width=False,
                        scale=1,
                        height=900
                    )

                    chat_input = gr.MultimodalTextbox(
                        interactive=True,
                        placeholder="输入你的问题...",
                        show_label=False,
                    )
                    quiz_state = gr.Textbox("游戏中", visible=False)
                    user_turn = gr.Checkbox(True, visible=False)

            temperature.change(guess_compete.change_llm_parameter, [
                temperature, top_p], None)
            top_p.change(guess_compete.change_llm_parameter,
                        [temperature, top_p], None)

            vector_index_btn.click(
                guess_compete.init_model, [app_id, app_key, embedding_model, theme_selected, difficulty, temperature, top_p], [vector_index_msg_out, chatbot])

            chat_input.submit(guess_compete.add_message, [chatbot, chat_input, user_turn], [chatbot, chat_input, user_turn])\
                .then(guess_compete.update_chat_a, [chatbot, quiz_state, user_turn, vector_index_msg_out], [chatbot, quiz_state, user_turn, vector_index_msg_out])\
                .then(guess_compete.update_chat_q, [chatbot, quiz_state, user_turn, vector_index_msg_out], [chatbot, quiz_state, user_turn, vector_index_msg_out])\
                .then(guess_compete.update_chat_a, [chatbot, quiz_state, user_turn, vector_index_msg_out], [chatbot, quiz_state, user_turn, vector_index_msg_out])\
                .then(lambda: gr.MultimodalTextbox(value=None, interactive=True) if quiz_state.value != "猜对了" else gr.MultimodalTextbox(value=None, interactive=False), None, [chat_input])
    return result


def get_user_guess_page(local_state):
    import user_guess
    with gr.Column() as result:
        gr.Markdown("# 猜谜")

        with gr.Blocks(fill_height=True, css=None) as demo:
            with gr.Row(equal_height=False):
                with gr.Column(scale=1):
                    with gr.Row(equal_height=True):
                        with gr.Column(scale=1):
                            eb_token = gr.Textbox(
                                label='app_id', type="password", value="")
                            app_key = gr.Textbox(
                                label='app_key', type="password", value="")
                    with gr.Column(scale=1, variant='panel'):
                        embedding_model = gr.Dropdown(choices=['vivo-BlueLM-TB'],
                                                    value='vivo-BlueLM-TB',
                                                    label="选择模型")
                        theme_selected = gr.Dropdown(choices=['生灵探密', '仰望星空'],
                                                     value='生灵探密',
                                                     label="选择主题")
                        difficulty = gr.Radio(
                            choices=['简单', '普通', '困难'], value='简单', label='难度选择')

                        with gr.Accordion(label="文本生成调整参数", open=False):
                            temperature = gr.Slider(
                                label="temperature", minimum=0.1, maximum=1, value=0.7, step=0.05)
                            top_p = gr.Slider(label="top_p", minimum=0,
                                            maximum=1, value=0.9, step=0.05)

                    with gr.Column(scale=1, variant='default'):
                        vector_index_btn = gr.Button(
                            '开始', variant='primary', scale=1)
                        vector_index_msg_out = gr.Markdown("尚未开始...")

                with gr.Column(scale=2):
                    chatbot = gr.Chatbot(
                        elem_id="chatbot",
                        bubble_full_width=False,
                        scale=1,
                        height=900
                    )

                    chat_input = gr.MultimodalTextbox(
                        interactive=True,
                        placeholder="输入你的问题...",
                        show_label=False,
                    )
                    quiz_state = gr.Textbox("游戏中", visible=False)

            temperature.change(user_guess.change_llm_parameter, [
                temperature, top_p], None)
            top_p.change(user_guess.change_llm_parameter, [temperature, top_p], None)

            vector_index_btn.click(
                user_guess.init_model, [eb_token, app_key, embedding_model, theme_selected, difficulty, temperature, top_p], [vector_index_msg_out, chatbot])

            chat_msg = chat_input.submit(
                user_guess.add_message, [chatbot, chat_input], [chatbot, chat_input])
            bot_msg = chat_msg.then(user_guess.update_chat, [chatbot, quiz_state, vector_index_msg_out], [
                chatbot, quiz_state, vector_index_msg_out])
            bot_msg.then(lambda: gr.MultimodalTextbox(interactive=True) if quiz_state.value !=
                        "猜对了" else gr.MultimodalTextbox(interactive=False), None, [chat_input])
    return result


def get_llm_guess_page(local_state):
    import llm_guess
    with gr.Column() as result:
        gr.Markdown("# AI猜谜")

        with gr.Blocks(fill_height=True) as demo:
            with gr.Row(equal_height=False):
                with gr.Column(scale=1):
                    with gr.Row(equal_height=True):
                        with gr.Column(scale=1):
                            eb_token = gr.Textbox(
                                label='app_id', type="password", value="")
                            app_key = gr.Textbox(
                                label='app_key', type="password", value="")
                    with gr.Column(scale=1, variant='panel'):
                        embedding_model = gr.Dropdown(choices=['vivo-BlueLM-TB'],
                                                    value='vivo-BlueLM-TB',
                                                    label="选择模型")
                        theme_selected = gr.Dropdown(choices=['生灵探密', '仰望星空'],
                                                     value='生灵探密',
                                                     label="选择主题")
                        difficulty = gr.Radio(
                            choices=['简单', '普通', '困难'], value='简单', label='难度选择')

                        with gr.Accordion(label="文本生成调整参数", open=False):
                            temperature = gr.Slider(
                                label="temperature", minimum=0.1, maximum=1, value=0.7, step=0.05)
                            top_p = gr.Slider(label="top_p", minimum=0,
                                            maximum=1, value=0.9, step=0.05)

                    with gr.Column(scale=1, variant='default'):
                        vector_index_btn = gr.Button(
                            '开始', variant='primary', scale=1)
                        vector_index_msg_out = gr.Markdown("尚未开始...")

                with gr.Column(scale=2):
                    chatbot = gr.Chatbot(
                        elem_id="chatbot",
                        bubble_full_width=False,
                        scale=1,
                        height=900
                    )

                    with gr.Row():
                        answer_button_1 = gr.Button(value="是")
                        answer_button_2 = gr.Button(value="否")
                        answer_button_3 = gr.Button(value="不知道")
                        answer_button_4 = gr.Button(value="猜对了")
                        quiz_state = gr.Textbox("游戏中", visible=False)

            temperature.change(llm_guess.change_llm_parameter,
                            [temperature, top_p], None)
            top_p.change(llm_guess.change_llm_parameter, [temperature, top_p], None)

            vector_index_btn.click(
                llm_guess.init_model, [eb_token, app_key, embedding_model, theme_selected, difficulty, temperature, top_p], [vector_index_msg_out, chatbot, quiz_state])

            answer_button_1.click(llm_guess.add_message, [chatbot, answer_button_1], [
                chatbot, quiz_state]).then(llm_guess.update_chat, [chatbot, quiz_state, vector_index_msg_out], [chatbot, vector_index_msg_out])
            answer_button_2.click(llm_guess.add_message, [chatbot, answer_button_2], [
                chatbot, quiz_state]).then(llm_guess.update_chat, [chatbot, quiz_state, vector_index_msg_out], [chatbot, vector_index_msg_out])
            answer_button_3.click(llm_guess.add_message, [chatbot, answer_button_3], [
                chatbot, quiz_state]).then(llm_guess.update_chat, [chatbot, quiz_state, vector_index_msg_out], [chatbot, vector_index_msg_out])
            answer_button_4.click(llm_guess.add_message, [chatbot, answer_button_4], [
                chatbot, quiz_state]).then(llm_guess.update_chat, [chatbot, quiz_state, vector_index_msg_out], [chatbot, vector_index_msg_out])
            quiz_state.change(llm_guess.toggle_button_state, [quiz_state, answer_button_1, answer_button_2, answer_button_3, answer_button_4], [
                answer_button_1, answer_button_2, answer_button_3, answer_button_4])
    return result


page_dict = {"home": get_home_page,
             "compete": get_compete_page,
             "uguess": get_user_guess_page,
             "lguess": get_llm_guess_page,
             "404": get_not_found_page}

# APP_SHELL - for multiple pages
with gr.Blocks(css=".component{max-width:100%; max-height:100%;}") as demo:

    def init_state(request: gr.Request):
        session_id = request.session_hash
        if request:
            session_id = request.session_hash
            print(f"** session_id: {session_id}")
            if session_id not in session_states:
                session_states[session_id] = {
                    "user": "test",
                    "session_id": session_id,
                    "tasks": [],
                    "page": "",
                }
        result = session_states[session_id]

        # PULL URL PARAMS HERE
        result["page"] = request.query_params.get("page")
        return result  # this result populates "state"

    state = gr.State()

    # POPULATE user "state" with request data
    demo.load(
        fn=init_state,
        inputs=None,
        outputs=state,
        queue=True,
        show_progress=False,
    )

    content = gr.HTML("Loading...")

    @gr.render(inputs=[state], triggers=[state.change])
    def page_content(local_state):
        with gr.Row(variant="panel") as result:
            with gr.Column(scale=0, min_width=50):
                anchor = gr.HTML("<h1>🔍</h1>")

                # BUTTONS FOR PAGE NAVIGATION
                with gr.Column() as result:
                    # gr.Button("👥", link="/")
                    gr.Button("⁉️", link="/?page=compete")
                    gr.Button("❓", link="/?page=uguess")
                    gr.Button("❗", link="/?page=lguess")

            with gr.Column(scale=12):
                # SIMPLE PAGE ROUTING HERE
                page_now = ""
                if (
                    local_state == None
                    or local_state["page"] == None
                    or len(local_state["page"]) < 1
                ):
                    page_now = "home"
                elif local_state["page"] not in page_dict:
                    page_now = "404"
                else:
                    page_now = local_state["page"]
                
                return (page_dict[page_now](local_state), local_state,)

    # HACK: Would be nice to delay rendering until state is populated
    def page_content_update(local_state):
        return gr.HTML("Loading...", visible=False)

    state.change(fn=page_content_update, inputs=state, outputs=content)

if __name__ == '__main__':
    demo.queue()
    demo.launch(allowed_paths=["assets/"])
