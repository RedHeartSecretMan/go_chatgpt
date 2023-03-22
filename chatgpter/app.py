import os
import re
import json
import socket
import random
import requests
import argparse
import matplotlib
import gradio as gr
from .model import ymd_stamp, CallChatGPT


SEED = 51
SESSIONNUM = 1
matplotlib.pyplot.switch_backend('Agg')
matplotlib.pyplot.rcParams['font.family'] = ['SimSong', 'Times New Roman']
matplotlib.pyplot.rcParams['axes.unicode_minus'] = False


def str2bool(string):
    str2val = {"True": True, "False": False}
    if string in str2val:
        return str2val[string]
    else:
        return None


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def password_generator(seed=51):   
    random.seed(seed)
    num_list = list(range(1, 10))
    random.shuffle(num_list)
    password = ""
    for num in num_list:
        password += str(num)
    password = str(int(password) // 2)

    return password 


# 一、聊天
def chatbot_interaction_1st(question, messages, states):
    text1 = ""
    messages.append((question, ""))
    try:
        match = re.search(r'\d+(\.\d+)?$', states[:-3])
        token_num = match.group()
        text2 = states.replace(f"{states[-(len(str(token_num))+3):]}", f"{gpt_model_1st.token_total} 个！")
    except Exception: 
        text2 = states
    
    if question:
        for answer_stream in gpt_model_1st(question): 
            messages[-1] = (question, answer_stream)

            yield text1, messages, text2
    else:
        answer = "很高兴遇见你！我是一个AI语言模型，我能为你提供准确和公正的信息！"
        messages[-1] = (question, answer)

        yield text1, messages, text2


def clear_text_1st(init_state):
    text = ""
    messages = init_state
    
    return text, messages


def reset_session_1st(init_state):
    gpt_model_1st.reset_states()
    text = ""
    messages = init_state
    
    return text, messages


def check_state_1st(api_key_text, model_text, request_text, stream_text):
    api_key = api_key_text
    url = 'https://api.openai.com/dashboard/billing/credit_grants'
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    response = json.loads(response.text)
    if response.get("error"):
        text = f"密钥 {api_key} 无效！"
        
        return text
    else:
        gpt_model_1st.api_key = api_key
        text1 = f"使用密钥 {api_key}，剩余额度 {response['total_available']} 美元！"

    if model_text:
        if model_text != "gpt-3.5-turbo":
            messages = [{"role": "user", "content": ""}] 
            payload = {
                "model": model_text,
                "messages": messages,
                "temperature": 1,
                "top_p": 1,
                "n": 1,
                "stream": False,
                "presence_penalty": 0,
                "frequency_penalty": 0,
            }
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            proxies = gpt_model_1st.proxies
            api_url = "https://api.openai.com/v1/chat/completions"
            response = requests.post(api_url,
                                    json=payload,
                                    headers=headers,
                                    timeout=200,
                                    proxies=proxies,
                                    stream=True,)

            response = json.loads(response.text)
            if response.get("error"):
                gpt_model_1st.model = "gpt-3.5-turbo"
                text2 = f"模型设置有误，自动使用模型 gpt-3.5-turbo"
            else:
                gpt_model_1st.model = model_text
                text2 = f"使用模型 {model_text}"
        else:
            gpt_model_1st.model = "gpt-3.5-turbo"
            text2 = "使用模型 gpt-3.5-turbo"
    else:
        gpt_model_1st.model = "gpt-3.5-turbo"
        text2 = f"模型设置有误，自动使用模型 gpt-3.5-turbo"
        
    if request_text in ["official", "post"]:
        gpt_model_1st.request_method = request_text
        text3 = f"使用请求 {request_text}"
    else:
        gpt_model_1st.request_method = "official"
        text3 = "请求设置有误，自动使用请求 official"
    
    def bool2use(bool):
        bool2val = {True: "使用", False: "不使用"}
        if bool in bool2val:
            return bool2val[bool]
        else:
            raise ValueError(f"Expected one of {set(bool2val.keys())}, got {bool}")

    if str2bool(stream_text) is None:
        gpt_model_1st.stream = False
        text4 = f"流式设置有误，不使用流式传输数据！"
    elif str2bool(stream_text) is True:
        gpt_model_1st.stream = True
        text4 = f"{bool2use(str2bool(stream_text))}流式传输数据！"
    else:
        gpt_model_1st.stream = False
        text4 = f"{bool2use(str2bool(stream_text))}流式传输数据！"
        
    text5 = f"使用分词数量为 {gpt_model_1st.token_total} 个！"
        
    text = text1 + "\n" + text2 + "，" + text3 + "，" + text4 + "，" + text5
    
    return text


# 二、问答
def chatbot_interaction_2st(question, answer, states):
    text1 = question
    try:
        match = re.search(r'\d+(\.\d+)?$', states[:-3])
        token_num = match.group()
        text2 = states.replace(f"{states[-(len(str(token_num))+3):]}", f"{gpt_model_2st.token_total} 个！")
    except Exception: 
        text2 = states
    
    if question: 
        for answer_stream in gpt_model_2st(question):
            answer = answer_stream

            yield text1, answer, text2
    else:
        answer = "很高兴遇见你！我是一个AI语言模型，我能为你提供准确和公正的信息！"
        
        yield text1, answer, text2


def clear_text_2st():
    text = ""
    answer = ""
     
    return text, answer


def reset_session_2st():
    gpt_model_2st.reset_states()
    text = ""
    answer = ""
     
    return text, answer


def check_state_2st(api_key_text, model_text, request_text, stream_text):
    api_key = api_key_text
    url = 'https://api.openai.com/dashboard/billing/credit_grants'
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    response = json.loads(response.text)
    if response.get("error"):
        text = f"密钥 {api_key} 无效！"
        
        return text
    else:
        gpt_model_2st.api_key = api_key
        text1 = f"使用密钥 {api_key}，剩余额度 {response['total_available']} 美元！"

    if model_text:
        if model_text != "gpt-3.5-turbo":
            messages = [{"role": "user", "content": ""}] 
            payload = {
                "model": model_text,
                "messages": messages,
                "temperature": 1,
                "top_p": 1,
                "n": 1,
                "stream": False,
                "presence_penalty": 0,
                "frequency_penalty": 0,
            }
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            proxies = gpt_model_2st.proxies
            api_url = "https://api.openai.com/v1/chat/completions"
            response = requests.post(api_url,
                                    json=payload,
                                    headers=headers,
                                    timeout=200,
                                    proxies=proxies,
                                    stream=True,)

            response = json.loads(response.text)
            if response.get("error"):
                gpt_model_2st.model = "gpt-3.5-turbo"
                text2 = f"模型设置有误，自动使用模型 gpt-3.5-turbo"
            else:
                gpt_model_2st.model = model_text
                text2 = f"使用模型 {model_text}"
        else:
            gpt_model_2st.model = "gpt-3.5-turbo"
            text2 = "使用模型 gpt-3.5-turbo"
    else:
        gpt_model_2st.model = "gpt-3.5-turbo"
        text2 = f"模型设置有误，自动使用模型 gpt-3.5-turbo"
        
    if request_text in ["official", "post"]:
        gpt_model_2st.request_method = request_text
        text3 = f"使用请求 {request_text}"
    else:
        gpt_model_2st.request_method = "official"
        text3 = "请求设置有误，自动使用请求 official"
    
    def bool2use(bool):
        bool2val = {True: "使用", False: "不使用"}
        if bool in bool2val:
            return bool2val[bool]
        else:
            raise ValueError(f"Expected one of {set(bool2val.keys())}, got {bool}")

    if str2bool(stream_text) is None:
        gpt_model_2st.stream = False
        text4 = f"流式设置有误，不使用流式传输数据"
    elif str2bool(stream_text) is True:
        gpt_model_2st.stream = True
        text4 = f"{bool2use(str2bool(stream_text))}流式传输数据"
    else:
        gpt_model_2st.stream = False
        text4 = f"{bool2use(str2bool(stream_text))}流式传输数据"
        
    text5 = f"使用分词数量为 {gpt_model_2st.token_total} 个！"
        
    text = text1 + "\n" + text2 + "，" + text3 + "，" + text4 + "，" + text5
    
    return text


# 日志 
def load_logs_1st(logs, filename, password):
    if password == password_generator(SEED):
        if not filename:
            text1 = "名称错误，无权操作！"
            text2 = ""
            return logs, text1, text2
        else:
            logspath = os.path.join(gpt_model_1st.logsdir, filename)
           
        if os.path.exists(logspath) and (os.path.splitext(os.path.basename(logspath))[-1] == ".log"):
            with open(logspath, "r") as f:
                logs = f.read()
            text1 = f"日志「{filename}」已导入！"
            text2 = ""
        else:
            text1 = "名称错误，无权操作！"
            text2 = ""
    else:
        text1 = ""
        text2 = "密码错误，无权操作！"
    
    return logs, text1, text2


def clear_text_3st():
    logs = ""
    text1 = ""
    text2 = ""
    
    return logs, text1, text2


def detele_logs_1st(logs, filename, password):
    if password == password_generator(SEED):
        if not filename:
            text1 = "名称错误，无权操作！"
            text2 = ""
            return logs, text1, text2
        else:
            logspath = os.path.join(gpt_model_1st.logsdir, filename)

        if os.path.exists(logspath) and (os.path.splitext(filename)[-1] == ".log"):
            os.remove(logspath)
            text1 = f"日志「{filename}」已删除！"
            text2 = ""
        else:
            text1 = "名称错误，无权操作！"
            text2 = ""
    else:
        text1 = ""
        text2 = "密码错误，无权操作！"
    
    return logs, text1, text2


def reset_session_3st(logs, password):
    if password == password_generator(SEED):
        gpt_model_1st.reset_logger()
        gpt_model_2st.reset_logger()
        text1 = "当前日志已重置！"
        text2 = ""
    else:
        text1 = ""
        text2 = "密码错误，无权操作！"
    
    return logs, text1, text2


def get_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # 核心参数
    parser.add_argument("--api_key", "-ak", type=str, default="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",
                        help="license sequence to call the openai api")
    parser.add_argument("--model", "-m", type=str, default="gpt-3.5-turbo", choices=["gpt-3.5-turbo", "gpt-4"],
                        help="name of the model interface provided by openai")
    parser.add_argument("--model_trend", "-mt", type=str, default="general", choices=["general", "poet", "tutor"],
                        help="set the response bias of the model")
    parser.add_argument("--request_method", "-rm", type=str, default="official", choices=["official", "post"],
                        help="set the method to request access to the api")
    parser.add_argument("--server_name", "-sn", type=str, default="127.0.0.1",
                        help="set the name of the server where the web page will run is usually done on the local machine")
    parser.add_argument("--server_port", "-sp", type=int, default=7860,
                        help="set the exposed port of the server running the web page, as long as the current port is not occupied")
    parser.add_argument("--proxy_name", "-pn", type=str, default="127.0.0.1",
                        help="set for the traffic proxy server are the same as those for running web pages")
    parser.add_argument("--proxy_port", "-pp", type=int, default=7890,
                        help="set the port exposed by the traffic proxy server")
    parser.add_argument("--stream", "-sm", type=str2bool, default=True,
                        help="if False, call the openai api request will receive all the packets at once")
    parser.add_argument("--share", "-se", type=str2bool, default=False,
                        help="if True, will create a public network access url using gradio, but some localhost is not accessible (e.g. Google Colab)")
    # 可选参数
    parser.add_argument("--temperature", type=int, default=1)
    parser.add_argument("--top_p", type=int, default=1)
    parser.add_argument("--n", type=int, default=SESSIONNUM)
    parser.add_argument("--presence_penalty", type=int, default=0)
    parser.add_argument("--frequency_penalty", type=int, default=0)
    parser.add_argument("--logsdir", type=str, default="./logging")
    parser.add_argument("--logsname", type=str, default=f"chatgpt_{ymd_stamp}.log")
    parser.add_argument("--debug", "-d", type=str2bool, default=False)
    
    return parser.parse_args()


def main():
    # 启动参数
    args = get_args()
    
    # 后端
    global gpt_model_1st, gpt_model_2st
    gpt_model_1st = CallChatGPT(api_key=args.api_key,
                            model=args.model,
                            temperature=args.temperature,
                            top_p=args.top_p,
                            n=args.n,
                            stream=args.stream,
                            presence_penalty=args.presence_penalty,
                            frequency_penalty=args.frequency_penalty,
                            proxy_name=args.proxy_name,
                            proxy_port=args.proxy_port,
                            logsdir=args.logsdir,
                            logsname=args.logsname,
                            model_trend=args.model_trend,
                            request_method=args.request_method,)
    gpt_model_2st = CallChatGPT(api_key=args.api_key,
                            model=args.model,
                            temperature=args.temperature,
                            top_p=args.top_p,
                            n=args.n,
                            stream=args.stream,
                            presence_penalty=args.presence_penalty,
                            frequency_penalty=args.frequency_penalty,
                            proxy_name=args.proxy_name,
                            proxy_port=args.proxy_port,
                            logsdir=args.logsdir,
                            logsname=args.logsname,
                            model_trend=args.model_trend,
                            request_method=args.request_method,)


    # 前端
    with gr.Blocks(title="GoChatGPT") as web:
        with gr.Column(variant="panel"):
            """控件显示"""
            # 一、聊天
            with gr.Tab(label="聊天", id=0):    
                gr.Chatbot.postprocess = gpt_model_1st.postprocess_messages
                init_state = gr.State()   
                with gr.Column(variant="panel"):   
                    out_text_1st = gr.Chatbot(label="Bot").style(height=450)
                    with gr.Box():
                        with gr.Row(variant="default").style(equal_height=True):
                            with gr.Column(scale=10, variant="panel"):
                                in_text_1st = gr.Textbox(label="输入",
                                                        show_label=False,
                                                        lines=7,
                                                        max_lines=7,
                                                        placeholder="请输入文字！").style(container=False)
                            with gr.Column(min_width=100, scale=1, variant="panel"):
                                start_btn_1st = gr.Button("开始", variant="primary") 
                                clear_btn_1st = gr.Button("清空", variant="secondary")
                                reset_btn_1st = gr.Button("重启", variant="secondary")
                    # 设置
                    with gr.Accordion(label="Setting", open=False): 
                        with gr.Column(scale=1, variant="panel"):
                            state_text_1st = gr.Textbox(value=f"{gpt_model_1st.api_key_infos}\n使用模型 {gpt_model_1st.model}，使用请求{gpt_model_1st.request_method}，{'使用' if gpt_model_1st.stream else '不使用'}流式传输数据，使用分词数量为 {gpt_model_1st.token_total} 个！",
                                                        label="状态",
                                                        show_label=False,
                                                        lines=3,
                                                        max_lines=3,
                                                        interactive=False,).style(container=False)       
                            with gr.Row(variant="default").style(equal_height=True):
                                with gr.Column(min_width=150, scale=1, variant="default"):
                                    api_key_text_1st = gr.Textbox(value=gpt_model_1st.api_key,
                                                                  label="密钥",
                                                                  show_label=True,
                                                                  lines=1,
                                                                  max_lines=1,
                                                                  interactive=True,
                                                                  placeholder=f"请输入密钥！",).style(container=True)
                                with gr.Column(min_width=150, scale=1, variant="default"):
                                    model_text_1st = gr.Textbox(value=gpt_model_1st.model,
                                                                label="模型",
                                                                show_label=True,
                                                                lines=1,
                                                                max_lines=1,
                                                                interactive=True,
                                                                placeholder=f"gpt-3.5-turbo 或 gpt-4 ！")
                            with gr.Row(variant="default").style(equal_height=True):
                                with gr.Column(min_width=150, scale=1, variant="default"):
                                    stream_text_1st = gr.Textbox(value=gpt_model_1st.stream,
                                                                 label="流式",
                                                                 show_label=True,
                                                                 lines=1,
                                                                 max_lines=1,
                                                                 interactive=True,
                                                                 placeholder="True 或 False ！")
                                with gr.Column(min_width=150, scale=1, variant="default"):
                                    request_text_1st = gr.Textbox(value=gpt_model_1st.request_method,
                                                                  label="请求",
                                                                  show_label=True,
                                                                  lines=1,
                                                                  max_lines=1,
                                                                  interactive=True,
                                                                  placeholder="official 或 post ！")
                    
                                              
            # 二、问答
            with gr.Tab(label="问答", id=1):
                with gr.Column(variant="panel"):
                    out_text_2st = gr.Code(language="markdown", label="Bot")
                    with gr.Box():
                        with gr.Row(variant="default").style(equal_height=True):
                            with gr.Column(scale=10, variant="panel"):
                                in_text_2st = gr.Textbox(label="输入",
                                                            show_label=False,
                                                            lines=7,
                                                            max_lines=7,
                                                            placeholder="请输入问题！").style(container=False) 
                            with gr.Column(min_width=100, scale=1, variant="panel"):                 
                                ask_btn_2st = gr.Button("提问", variant="primary")
                                clear_btn_2st = gr.Button("清空", variant="secondary")
                                reset_btn_2st = gr.Button("重启", variant="secondary")  
                    # 设置        
                    with gr.Accordion(label="Setting", open=False): 
                        with gr.Column(scale=1, variant="panel"):
                            state_text_2st = gr.Textbox(value=f"{gpt_model_2st.api_key_infos}\n使用模型 {gpt_model_2st.model}，使用请求{gpt_model_1st.request_method}，{'使用' if gpt_model_2st.stream else '不使用'}流式传输数据，使用分词数量为 {gpt_model_1st.token_total} 个！",
                                                        label="状态",
                                                        show_label=False,
                                                        lines=3,
                                                        max_lines=3,
                                                        interactive=False,).style(container=False)        
                            with gr.Row(variant="default").style(equal_height=True):
                                with gr.Column(min_width=150, scale=1, variant="default"):
                                    api_key_text_2st = gr.Textbox(value=gpt_model_2st.api_key,
                                                                  label="密钥",
                                                                  show_label=True,
                                                                  lines=1,
                                                                  max_lines=1,
                                                                  interactive=True,
                                                                  placeholder=f"请输入密钥！",).style(container=True)
                                with gr.Column(min_width=150, scale=1, variant="default"):
                                    model_text_2st = gr.Textbox(value=gpt_model_2st.model,
                                                                label="模型",
                                                                show_label=True,
                                                                lines=1,
                                                                max_lines=1,
                                                                interactive=True,
                                                                placeholder=f"gpt-3.5-turbo 或 gpt-4 ！")
                            with gr.Row(variant="default").style(equal_height=True):
                                with gr.Column(min_width=150, scale=1, variant="default"):
                                    stream_text_2st = gr.Textbox(value=gpt_model_2st.stream,
                                                                 label="流式",
                                                                 show_label=True,
                                                                 lines=1,
                                                                 max_lines=1,
                                                                 interactive=True,
                                                                 placeholder="True 或 False ！")
                                with gr.Column(min_width=150, scale=1, variant="default"):
                                    request_text_2st = gr.Textbox(value=gpt_model_2st.request_method,
                                                                  label="请求",
                                                                  show_label=True,
                                                                  lines=1,
                                                                  max_lines=1,
                                                                  interactive=True,
                                                                  placeholder="official 或 post ！")
                                    
       
            # TODO: 20230305 -> 写完论文: 增加语音对话特性与增加绘图作画特性
            # 三、语音       
            with gr.Tab(label="语音", id=2):        
                    gr.Markdown("<center><h3>此模块将提供语音对话功能，类似Siri与小爱同学</h3><h3>敬请期待...</h3></center>") 
            # 四、绘画       
            with gr.Tab(label="绘画", id=3):        
                    gr.Markdown("<center><h3>此模块将提供强化Prompt描述的绘画功能</h3><h3>敬请期待...</h3></center>")        
        

            # 日志                                
            with gr.Tab(label="日志", id=4):
                with gr.Column():
                    log_text_1st = gr.Code(label="Log")
                    with gr.Box():
                        with gr.Column(scale=1, variant="panel"):
                            in_text_3st = gr.Textbox(label="输入",
                                                    show_label=False,
                                                    lines=1,
                                                    max_lines=1,
                                                    placeholder="请输入名称！").style(container=False)
                        with gr.Column(scale=1, variant="panel"):
                            in_text_4st = gr.Textbox(label="输入",
                                                    show_label=False,
                                                    lines=1,
                                                    max_lines=1,
                                                    placeholder="请输入密码！").style(container=False)
                    with gr.Box():
                        with gr.Row(variant="default").style(equal_height=True): 
                            with gr.Column(min_width=100, scale=1, variant="panel"):    
                                load_btn_1st = gr.Button("导入", variant="primary")
                            with gr.Column(min_width=100, scale=1, variant="panel"):
                                clear_btn_3st = gr.Button("清空", variant="secondary")
                            with gr.Column(min_width=100, scale=1, variant="panel"):
                                detele_btn_1st = gr.Button("删除", variant="secondary")
                            with gr.Column(min_width=100, scale=1, variant="panel"):
                                reset_btn_3st = gr.Button("重启", variant="secondary")
            
                           
        # 署名
        gr.Markdown("<center><h3>Welcome To Play · Code By HaoDaXia</h3></center>")
        
        
        """控件行为"""
        # 一、聊天
        if True:
            in_text_1st.submit(chatbot_interaction_1st,
                            inputs=[in_text_1st, out_text_1st, state_text_1st],
                            outputs=[in_text_1st, out_text_1st, state_text_1st],
                            show_progress=True)
            start_btn_1st.click(chatbot_interaction_1st,
                                inputs=[in_text_1st, out_text_1st, state_text_1st],
                                outputs=[in_text_1st, out_text_1st, state_text_1st],
                                show_progress=True)
            clear_btn_1st.click(clear_text_1st,
                                inputs=[init_state],
                                outputs=[in_text_1st, out_text_1st],
                                show_progress=True)
            reset_btn_1st.click(reset_session_1st,
                                inputs=[init_state],
                                outputs=[in_text_1st, out_text_1st],
                                show_progress=True)
            # 设置
            api_key_text_1st.submit(check_state_1st, 
                                    inputs=[api_key_text_1st, model_text_1st, request_text_1st, stream_text_1st],
                                    outputs=[state_text_1st])
            model_text_1st.submit(check_state_1st,
                                inputs=[api_key_text_1st, model_text_1st, request_text_1st, stream_text_1st],
                                outputs=[state_text_1st])
            request_text_1st.submit(check_state_1st,
                                    inputs=[api_key_text_1st, model_text_1st, request_text_1st, stream_text_1st],
                                    outputs=[state_text_1st])
            stream_text_1st.submit(check_state_1st,
                                inputs=[api_key_text_1st, model_text_1st, request_text_1st, stream_text_1st],
                                outputs=[state_text_1st])
        
        
        # 二、问答
        if True:
            in_text_2st.submit(chatbot_interaction_2st,
                            inputs=[in_text_2st, out_text_2st, state_text_2st],
                            outputs=[in_text_2st, out_text_2st, state_text_2st],
                            show_progress=True)
            ask_btn_2st.click(chatbot_interaction_2st,
                            inputs=[in_text_2st, out_text_2st, state_text_2st],
                            outputs=[in_text_2st, out_text_2st, state_text_2st],
                            show_progress=True)
            clear_btn_2st.click(clear_text_2st,
                                inputs=[],
                                outputs=[in_text_2st, out_text_2st],
                                show_progress=True)
            reset_btn_2st.click(reset_session_2st,
                                inputs=[],
                                outputs=[in_text_2st, out_text_2st],
                                show_progress=True)
            # 设置
            api_key_text_2st.submit(check_state_2st, 
                                    inputs=[api_key_text_2st, model_text_2st, request_text_2st, stream_text_2st],
                                    outputs=[state_text_2st])
            model_text_2st.submit(check_state_2st,
                                inputs=[api_key_text_2st, model_text_2st, request_text_2st, stream_text_2st],
                                outputs=[state_text_2st])
            request_text_2st.submit(check_state_2st,
                                    inputs=[api_key_text_2st, model_text_2st, request_text_2st, stream_text_2st],
                                    outputs=[state_text_2st])
            stream_text_2st.submit(check_state_2st,
                                inputs=[api_key_text_2st, model_text_2st, request_text_2st, stream_text_2st],
                                outputs=[state_text_2st])
        
        
        # 日志
        if True:
            load_btn_1st.click(load_logs_1st,
                            inputs=[log_text_1st, in_text_3st, in_text_4st],
                            outputs=[log_text_1st, in_text_3st, in_text_4st])
            clear_btn_3st.click(clear_text_3st,
                                inputs=[],
                                outputs=[log_text_1st, in_text_3st, in_text_4st])
            detele_btn_1st.click(detele_logs_1st,
                                inputs=[log_text_1st, in_text_3st, in_text_4st],
                                outputs=[log_text_1st, in_text_3st, in_text_4st])
            reset_btn_3st.click(reset_session_3st,
                                inputs=[log_text_1st, in_text_4st],
                                outputs=[log_text_1st, in_text_3st, in_text_4st])
    
    
    # 启动网页
    if is_port_in_use(args.server_port):
        args.server_port += 1
    web.queue().launch(server_name=args.server_name,
                       server_port=args.server_port,
                       share=args.share,
                       debug=args.debug)


if __name__ == "__main__":
    main()
