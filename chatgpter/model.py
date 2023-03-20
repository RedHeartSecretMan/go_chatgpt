import os
import time
import json
import logging
import openai
import requests
import tiktoken


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
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.n = n 
        self.stream = stream
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.proxy_name=proxy_name
        self.proxy_port=proxy_port
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
        self.messages = []
        self.token_nums = []
        self.token_usage = []
        self.token_gaps = 2**2
        self.token_current = 0
        self.system_messages()
    
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
        proxies = {
            "http": f"http://{self.proxy_name}:{self.proxy_port}",
            "https": f"http://{self.proxy_name}:{self.proxy_port}"
        }
        if self.stream:
            timeout = 30
        else:
            timeout = 200
        api_url = "https://api.openai.com/v1/chat/completions"
        response = requests.post(api_url,
                                 json=payload,
                                 headers=headers,
                                 timeout=timeout,
                                 proxies=proxies,
                                 stream=True)
        response = json.loads(response.text)
        
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
                self.token_current += (len(self.tokenizer.encode(message)) + self.token_gaps)
                self.token_usage = {"completion_tokens": 0,
                                    "prompt_tokens": (len(self.tokenizer.encode(message)) + self.token_gaps), 
                                    "total_tokens": (len(self.tokenizer.encode(message)) + self.token_gaps)}
                self.token_nums.insert(0, self.token_usage.copy())
            elif self.model_trend == "poet":
                prompt = "You are ChatGPT, a large language model trained by OpenAI. You can generate poems based on the user's input. You can write poems in different styles and formats, such as haiku, sonnet, free verse, etc. You are creative, expressive, and poetic."
                self.messages.insert(0, {"role": "system", "content": prompt})
                message = "".join([f"role: {msg['role']}, content: {msg['content']}" for msg in [self.messages[-1]]])
                self.token_current += (len(self.tokenizer.encode(message)) + self.token_gaps)
                self.token_usage = {"completion_tokens": 0,
                                    "prompt_tokens": (len(self.tokenizer.encode(message)) + self.token_gaps), 
                                    "total_tokens": (len(self.tokenizer.encode(message)) + self.token_gaps)}
                self.token_nums.insert(0, self.token_usage.copy())
            elif self.model_trend == "tutor":
                prompt = "You are ChatGPT, a large language model trained by OpenAI. You can follow instructions given by the user. You can perform various tasks such as arithmetic calculations, text manipulation, web search, etc. You are smart, efficient, and reliable."
                self.messages.insert(0, {"role": "system", "content": prompt})
                message = "".join([f"role: {msg['role']}, content: {msg['content']}" for msg in [self.messages[-1]]])
                self.token_current += (len(self.tokenizer.encode(message)) + self.token_gaps)
                self.token_usage = {"completion_tokens": 0,
                                    "prompt_tokens": (len(self.tokenizer.encode(message)) + self.token_gaps), 
                                    "total_tokens": (len(self.tokenizer.encode(message)) + self.token_gaps)}
                self.token_nums.insert(0, self.token_usage.copy())
    
    def control_messages(self,
                         role=None,
                         content=None,
                         usage=None,
                         mode=None): 
        if mode == "message":
            if role == "user":
                self.messages.append({"role": "user", "content": content})
                message = "".join([f"role: {msg['role']}, content: {msg['content']}" for msg in [self.messages[-1]]])
                self.token_current += (len(self.tokenizer.encode(message)) + self.token_gaps)
            elif role == "assistant":
                self.messages.append({"role": "assistant", "content": content})
                message = "".join([f"role: {msg['role']}, content: {msg['content']}" for msg in [self.messages[-1]]])
                self.token_current += (len(self.tokenizer.encode(message)) + self.token_gaps)
        elif mode == "decrease":
            for _ in range(1+self.n):
                self.messages.pop(1)
            self.token_current -= (self.token_nums.pop(1)["total_tokens"] - self.token_gaps)
        elif mode == "increase":
            self.token_nums.append({"completion_tokens": usage["completion_tokens"],
                                    "prompt_tokens": usage["prompt_tokens"] - self.token_usage["total_tokens"], 
                                    "total_tokens": usage["total_tokens"] - self.token_usage["total_tokens"]})
            self.token_usage["completion_tokens"] = usage["completion_tokens"]
            self.token_usage["prompt_tokens"] = usage["prompt_tokens"]
            self.token_usage["total_tokens"] = usage["total_tokens"]
            self.token_current = usage["total_tokens"]
        
    def reset_messages(self):
        self.messages = []
        self.token_nums = []
        self.token_usage = []
        self.token_gaps = 2**2
        self.token_current = 0
        self.system_messages()
    
    
    def __call__(self, prompt):
        self.control_messages(role="user", content=prompt, mode="message")
        while self.token_current >= 4096:
            if len(self.messages) >= (1+1+self.n):
                self.control_messages(mode="decrease")
            else:
                answer_list = ["输入过长，请精简输入！"]
                self.reset_messages()
                
                return answer_list
        
        self.check_logger()
        self.logs.info(f"提问: {prompt}\n")        
          
        answer_list = []
        if self.request_method == "official":
            try:
                response = self.openai_gptapi_1st()  
                answer_dict = {index: response.choices[index].message.content for index in range(self.n)}
                for index, answer in answer_dict.items():
                    self.control_messages(role="assistant", content=answer, mode="message")            
                    if self.n > 1:
                        self.check_logger()
                        self.logs.info(f"回答({index+1}): {answer.strip()}\n\n")
                    else:
                        self.check_logger()
                        self.logs.info(f"回答: {answer.strip()}\n\n")    
                    answer_list.append(answer.strip())            
                self.control_messages(usage=response.usage, mode="increase")             
            except openai.error.RateLimitError:
                answer_list = ["延迟较大，请稍后重试！"]
                self.reset_messages()
                
                return answer_list
            except openai.error.InvalidRequestError: 
                answer_list = ["请求无效，将重新启动！"]
                self.reset_messages()

            return answer_list
        elif self.request_method == "post":
            try:
                response = self.openai_gptapi_2st()
                answer_dict = {index: response["choices"][index]["message"]["content"] for index in range(self.n)}
                for index, answer in answer_dict.items():
                    self.control_messages(role="assistant", content=answer, mode="message")            
                    if self.n > 1:
                        self.check_logger()
                        self.logs.info(f"回答({index+1}): {answer.strip()}\n\n")
                    else:
                        self.check_logger()
                        self.logs.info(f"回答: {answer.strip()}\n\n")    
                    answer_list.append(answer.strip())            
                self.control_messages(usage=response["usage"], mode="increase")             
            except requests.exceptions.ReadTimeout:
                answer_list = ["延迟较大，请稍后重试！"]
                self.reset_messages()
                
                return answer_list
            except requests.exceptions.ConnectTimeout: 
                answer_list = ["请求无效，请稍后重试！"]
                self.reset_messages()

                return answer_list     
            except requests.exceptions.SSLError:
                answer_list = ["请求无效，请稍后重试！"]
                self.reset_messages()

                return answer_list
        
        return answer_list
    