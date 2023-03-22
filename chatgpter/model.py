import os
import io
import time
import json
import warnings
import logging
import openai
import requests
import tiktoken
import mdtex2html



MAXTOKEN = 4096
TAGLENGTH = 6
ymd_stamp = time.strftime('%Y%m%d', time.localtime())


def local_api_key():
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  
        with open(f"{base_dir}/api_key.txt", "r") as f:
            api_key = f.read().split("\n")
            return api_key[0]
    except FileNotFoundError:
        return None


# 加载GPT模型
class CallChatGPT:
    def __init__(self,
                 api_key = "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",
                 model="gpt-3.5-turbo",
                 temperature=1,
                 top_p=1,
                 n=1,
                 stream=False,
                 presence_penalty=0,
                 frequency_penalty=0,
                 proxy_name="127.0.0.1",
                 proxy_port=7890,
                 logsdir="./logging",
                 logsname=f"chatgpt_{ymd_stamp}.log",
                 model_trend="general",
                 request_method="official",):
        # 模型参数
        self.api_key = api_key
        if local_api_key():
            self.api_key = local_api_key()
        self.api_key_infos = self.openai_credit_grants()
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.n = n 
        self.stream = stream
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.proxy_name=proxy_name
        self.proxy_port=proxy_port
        self.proxies = {
            "http": f"http://{proxy_name}:{proxy_port}", 
            "https": f"http://{proxy_name}:{proxy_port}"
        }
        # 日志参数
        self.logsdir = logsdir
        self.logsname = logsname
        self.logspath = os.path.join(logsdir, logsname)
        self.logs = self.built_logger()
        # 消息参数
        try:
            self.tokenizer = tiktoken.encoding_for_model(model)
        except KeyError:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.model_trend = model_trend
        self.request_method = request_method
        self.token_total = 0
        self.token_gaps = 2**2
        self.token_usage_stack = []
        self.token_usage_current = []
        self.messages = []
        self.system_messages()
    
    def openai_credit_grants(self):
        url = 'https://api.openai.com/dashboard/billing/credit_grants'
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers)
        response = json.loads(response.text)
        if response.get("error"):
            infos = f"密钥 {self.api_key} 无效！"
        else:
            infos = f"使用密钥 {self.api_key}，剩余额度 {response['total_available']} 美元！"

        return infos

    def openai_gptapi_1st(self): 
        openai.api_key = self.api_key
        response = openai.ChatCompletion.create(model=self.model,
                                                messages=self.messages,
                                                temperature=self.temperature,
                                                top_p=self.top_p,
                                                n=self.n,
                                                stream=self.stream,
                                                presence_penalty=self.presence_penalty,
                                                frequency_penalty=self.frequency_penalty)
        
        return response
    
    def openai_gptapi_2st(self):
        payload = {
            "model": self.model,
            "messages": self.messages,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "n": self.n,
            "stream": self.stream,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        proxies = self.proxies
        if self.stream:
            timeout = 30
        else:
            timeout = 300
        api_url = "https://api.openai.com/v1/chat/completions"
        response = requests.post(api_url,
                                 json=payload,
                                 headers=headers,
                                 timeout=timeout,
                                 proxies=proxies,
                                 stream=self.stream)
        
        return response    
     
    def built_logger(self):
        os.makedirs(self.logsdir, exist_ok=True)
        logs = logging.getLogger(__name__)
        logs.setLevel(logging.INFO)
        handler = logging.FileHandler(filename=self.logspath, encoding="UTF-8")
        formatter = logging.Formatter(fmt="[%(asctime)s - %(levelname)s]: %(message)s",
                                      datefmt="%Y%m%d %H:%M:%S")
        handler.setFormatter(formatter)
        if not logs.handlers:
            logs.addHandler(handler)    
        
        return logs
    
    def reset_logger(self):
        if self.logs.handlers:
            self.logs.handlers = []
        if os.path.exists(self.logspath):
            os.remove(self.logspath)
        
    def check_logger(self):
        if not os.path.exists(self.logspath) or not self.logs.handlers:
            self.reset_logger()
            self.logs = self.built_logger() 
    
    def reset_states(self):
        self.api_key_infos = self.openai_credit_grants()
        self.token_total = 0
        self.token_gaps = 2**2
        self.token_usage_stack = []
        self.token_usage_current = []
        self.messages = []
        self.system_messages()
    
    def system_messages(self):
        setflag = False
        if not self.messages:
            setflag = True
        else:
            for message in self.messages:
                if message["role"] != "system":
                    setflag = True
                else:
                    setflag = False
                    break
        if setflag:
            if self.model_trend == "general":
                prompt = "You are a helpful assistant."
                self.messages.insert(0, {"role": "system", "content": prompt})
                message = "".join([f"role: {msg['role']}, content: {msg['content']}" for msg in [self.messages[-1]]])
                self.token_total += (len(self.tokenizer.encode(message)))
                self.token_usage_current = {"completion_tokens": 0,
                                            "prompt_tokens": len(self.tokenizer.encode(message)), 
                                            "total_tokens": len(self.tokenizer.encode(message))}
                self.token_usage_stack.insert(0, self.token_usage_current.copy())
            elif self.model_trend == "poet":
                prompt = "You are ChatGPT, a large language model trained by OpenAI. You can generate poems based on the user's input. You can write poems in different styles and formats, such as haiku, sonnet, free verse, etc. You are creative, expressive, and poetic."
                self.messages.insert(0, {"role": "system", "content": prompt})
                message = "".join([f"role: {msg['role']}, content: {msg['content']}" for msg in [self.messages[-1]]])
                self.token_total += (len(self.tokenizer.encode(message)))
                self.token_usage_current = {"completion_tokens": 0,
                                            "prompt_tokens": len(self.tokenizer.encode(message)), 
                                            "total_tokens": len(self.tokenizer.encode(message))}
                self.token_usage_stack.insert(0, self.token_usage_current.copy())
            elif self.model_trend == "tutor":
                prompt = "You are ChatGPT, a large language model trained by OpenAI. You can follow instructions given by the user. You can perform various tasks such as arithmetic calculations, text manipulation, web search, etc. You are smart, efficient, and reliable."
                self.messages.insert(0, {"role": "system", "content": prompt})
                message = "".join([f"role: {msg['role']}, content: {msg['content']}" for msg in [self.messages[-1]]])
                self.token_total += (len(self.tokenizer.encode(message)))
                self.token_usage_current = {"completion_tokens": 0,
                                            "prompt_tokens": len(self.tokenizer.encode(message)), 
                                            "total_tokens": len(self.tokenizer.encode(message))}
                self.token_usage_stack.insert(0, self.token_usage_current.copy())
    
    def control_messages(self,
                         stream=False,
                         role=None,
                         content=None,
                         usage=None,
                         mode=None,): 
        if mode == "message":
            if role == "user":
                self.messages.append({"role": "user", "content": content})
                message = "".join([f"role: {msg['role']}, content: {msg['content']}" for msg in [self.messages[-1]]])
                self.token_total += (len(self.tokenizer.encode(message)))
                if stream:
                    self.token_total += (len(self.tokenizer.encode(message)) + self.token_gaps)
                else:
                    self.token_total += (len(self.tokenizer.encode(message)))
            elif role == "assistant":
                self.messages.append({"role": "assistant", "content": content})
                message = "".join([f"role: {msg['role']}, content: {msg['content']}" for msg in [self.messages[-1]]])
                if stream:
                    self.token_total += (len(self.tokenizer.encode(message)) + self.token_gaps)
                else:
                    self.token_total += (len(self.tokenizer.encode(message)))
        elif mode == "increase":
            if stream:
                self.token_usage_stack.append({"total_tokens": self.token_total - self.token_usage_current["total_tokens"]})
                self.token_usage_current["total_tokens"] = self.token_total
            else:
                self.token_usage_stack.append({"completion_tokens": usage["completion_tokens"],
                                                "prompt_tokens": usage["prompt_tokens"] - self.token_usage_current["total_tokens"], 
                                                "total_tokens": usage["total_tokens"] - self.token_usage_current["total_tokens"]})
                self.token_usage_current["completion_tokens"] = usage["completion_tokens"]
                self.token_usage_current["prompt_tokens"] = usage["prompt_tokens"]
                self.token_usage_current["total_tokens"] = usage["total_tokens"]
                self.token_total = usage["total_tokens"]
        elif mode == "decrease":
            for _ in range(1+self.n):
                self.messages.pop(1)
                self.token_total -= (self.token_usage_stack.pop(1)["total_tokens"])

    def postprocess_messages(self, messages):
        def parse(text):
            lines = text.split("\n")
            lines = [line for line in lines if line != ""]
            count = 0
            for i, line in enumerate(lines):
                if "```" in line:
                    count += 1
                    items = line.split('`')
                    if count % 2 == 1:
                        lines[i] = f'<pre><code class="language-{items[-1]}">'
                    else:
                        lines[i] = f'<br></code></pre>'
                else:
                    if i > 0:
                        if count % 2 == 1:
                            line = line.replace("`", "\`")
                            line = line.replace("<", "&lt;")
                            line = line.replace(">", "&gt;")
                            line = line.replace(" ", "&nbsp;")
                            line = line.replace("*", "&ast;")
                            line = line.replace("_", "&lowbar;")
                            line = line.replace("-", "&#45;")
                            line = line.replace(".", "&#46;")
                            line = line.replace("!", "&#33;")
                            line = line.replace("(", "&#40;")
                            line = line.replace(")", "&#41;")
                            line = line.replace("$", "&#36;")
                        lines[i] = "<br>"+line
            text = "".join(lines)
            return text

        if messages is None:
            return []
        for i, (question, answer) in enumerate(messages):
            messages[i] = (None if question is None else parse(question),
                           None if answer is None else mdtex2html.convert(parse(answer)),)  
        
        return messages
    

    def __call__(self, prompt):
        self.control_messages(role="user", content=prompt, mode="message")
        while self.token_total > MAXTOKEN:  
            if len(self.messages) >= (1+1+self.n):
                self.control_messages(mode="decrease")
                try:
                    response = openai.ChatCompletion.create(model=self.model, messages=self.messages)
                    self.token_total = response.usage["total_tokens"]
                except Exception as e:
                    warnings.warn(f"校准当前token的使用情况发生异常 {e} ！")
            else:
                answer = "输入过长，请精简输入！"
                self.reset_states()
                
                yield answer
        
        self.check_logger()
        self.logs.info(f"提问: {prompt}\n")        
          
        if self.request_method == "official":
            try:
                if self.stream:
                    response = self.openai_gptapi_1st()
                    string_io = io.StringIO()
                    
                    yield string_io.getvalue()
                    for chunk in response:
                        if chunk["choices"][0]["finish_reason"] != "stop":
                            if chunk["choices"][0].get("delta"):
                                if chunk["choices"][0]["delta"].get("content"):
                                    string_io.write(chunk["choices"][0]["delta"]["content"])

                                    yield string_io.getvalue()
                        elif chunk["choices"][0]["finish_reason"] == "length":
                           warnings.warn(f"回答可能不完整因为当前token数已经达到 {MAXTOKEN} ！")
                    answer = string_io.getvalue()
                    self.check_logger()
                    self.logs.info(f"回答: {answer.strip()}\n\n")
                    self.control_messages(stream=True, role="assistant", content=answer, mode="message") 
                    self.control_messages(stream=True, mode="increase")
                else:
                    response = self.openai_gptapi_1st()  
                    usage = response.usage
                    if response["choices"][0]["finish_reason"] == "length":
                        warnings.warn(f"回答可能不完整因为当前token数已经达到 {MAXTOKEN} ！")
                    answer_dict = {index: response.choices[index].message.content for index in range(self.n)}
                    for index, answer in answer_dict.items():            
                        if self.n > 1:
                            self.check_logger()
                            self.logs.info(f"回答({index+1}): {answer.strip()}\n\n")
                        else:
                            self.check_logger()
                            self.logs.info(f"回答: {answer.strip()}\n\n")               

                        yield answer
                        self.control_messages(role="assistant", content=answer, mode="message")         
                    self.control_messages(usage=usage, mode="increase")    
            except openai.error.RateLimitError:
                answer = "延迟较大，请稍后重试！"
                self.reset_states()
                
                yield answer
            except openai.error.InvalidRequestError: 
                answer = "请求无效，将重新启动！"
                self.reset_states()

                yield answer
        elif self.request_method == "post":
            try:
                if self.stream:
                    response = self.openai_gptapi_2st()
                    string_io = io.StringIO()
                    
                    yield string_io.getvalue()
                    for chunk in response.iter_lines():
                        chunk = chunk.decode()
                        chunk = chunk[TAGLENGTH:]
                        chunk_lenght = len(chunk)
                        try:
                            chunk = json.loads(chunk)
                        except json.JSONDecodeError:
                            continue
                        if chunk_lenght > TAGLENGTH:
                            if chunk["choices"][0]["finish_reason"] != "stop":
                                if chunk["choices"][0].get("delta"):
                                    if chunk["choices"][0]["delta"].get("content"): 
                                        string_io.write(chunk["choices"][0]["delta"]["content"])
                                        
                                        yield string_io.getvalue()
                            elif chunk["choices"][0]["finish_reason"] == "length":
                                warnings.warn(f"回答可能不完整因为当前token数已经达到 {MAXTOKEN} ！")
                    answer = string_io.getvalue()
                    self.check_logger()
                    self.logs.info(f"回答: {answer.strip()}\n\n")
                    self.control_messages(stream=True, role="assistant", content=answer, mode="message") 
                    self.control_messages(stream=True, mode="increase")
                else:
                    response = self.openai_gptapi_2st()
                    response = json.loads(response.text)
                    usage = response["usage"]
                    if response["choices"][0]["finish_reason"] == "length":
                        warnings.warn(f"回答可能不完整因为当前token数已经达到 {MAXTOKEN} ！")
                    answer_dict = {index: response["choices"][index]["message"]["content"] for index in range(self.n)}
                    for index, answer in answer_dict.items():           
                        if self.n > 1:
                            self.check_logger()
                            self.logs.info(f"回答({index+1}): {answer.strip()}\n\n")
                        else:
                            self.check_logger()
                            self.logs.info(f"回答: {answer.strip()}\n\n")     
                              
                        yield answer 
                        self.control_messages(role="assistant", content=answer, mode="message")      
                    self.control_messages(usage=usage, mode="increase")                     
            except requests.exceptions.ReadTimeout:
                answer = "延迟较大，请稍后重试！"
                self.reset_states()
                
                yield answer
            except requests.exceptions.ConnectTimeout: 
                answer = "请求无效，请稍后重试！"
                self.reset_states()

                yield answer  
            except requests.exceptions.SSLError:
                answer = "请求无效，请稍后重试！"
                self.reset_states()

                yield answer
    