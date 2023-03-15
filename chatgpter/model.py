import os
import time
import logging
import openai


def timestamp():
    
    return time.strftime('%Y%m%d', time.localtime())


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
                 logsdir="./logging",
                 logsname=f"chatgpt_{timestamp}.log",
                 trend="general",):
        # 模型参数
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.n = n 
        self.stream = stream
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        # 日志参数
        self.logsdir = logsdir
        self.logsname = logsname
        self.logspath = os.path.join(logsdir, logsname)
        self.logs = self.built_logger()
        # 消息参数
        self.messages = []
        self.token_nums = []
        self.token_gaps = 2**2
        self.total_tokens = 0
        self.trend = trend
        self.system_messages()
    
    def openai_gptapi(self): 
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
            if self.trend == "general":
                self.messages.insert(0, {"role": "system", "content": "You are a helpful assistant."})
                self.total_tokens += (13 + self.token_gaps)
                self.token_nums.insert(0, (13 + self.token_gaps))
            elif self.trend == "poet":
                self.messages.insert(0, {"role": "system", "content": "You are ChatGPT, a large language model trained by OpenAI. You can generate poems based on the user's input. You can write poems in different styles and formats, such as haiku, sonnet, free verse, etc. You are creative, expressive, and poetic."})
                self.total_tokens += (65 + self.token_gaps)
                self.token_nums.insert(0, (65 + self.token_gaps))
            elif self.trend == "tutor":
                self.messages.insert(0, {"role": "system", "content": "You are ChatGPT, a large language model trained by OpenAI. You can follow instructions given by the user. You can perform various tasks such as arithmetic calculations, text manipulation, web search, etc. You are smart, efficient, and reliable."})
                self.total_tokens += (58 + self.token_gaps)
                self.token_nums.insert(0, (58 + self.token_gaps))
            else:
                pass 
    
    def control_messages(self, role, content, usage, mode="message"): 
        if mode == "message":
            if role == "user":
                self.messages.append({"role": "user", "content": content})
            elif role == "assistant":
                self.messages.append({"role": "assistant", "content": content})
            else:
                pass
        elif mode == "increase":
            self.token_nums.append(usage)
            self.total_tokens = self.token_nums[-1].total_tokens
        elif mode == "decrease":
            for _ in range(1+self.n):
                self.messages.pop(1)
            self.total_tokens -= (self.token_nums.pop(1).total_tokens - self.token_gaps)
        else:
            pass
        
    def reset_messages(self):
        self.messages = []
        self.token_nums = []
        self.token_gaps = 2**2
        self.total_tokens = 0
    
    
    def __call__(self, prompt):
        print(1, self.total_tokens)
        while self.total_tokens >= 4096:
            if len(self.messages) >= (1+1+self.n):
                self.control_messages(mode="decrease")
            else:
                self.reset_messages()
                self.system_messages()
        print(2, self.total_tokens)
        self.check_logger()
        self.logs.info(f"提问: {prompt}\n")        
          
        answer_list = []
        
        try:
            self.control_messages(role="user", content=prompt)
            response = self.openai_gptapi() 
            self.control_messages(usage=response.usage, mode="increase")  
            print(3, self.total_tokens)        
        except openai.error.InvalidRequestError: 
            answer_list = ["请求无效，请重新开始！"]
            self.reset_messages()
            self.system_messages()

            return answer_list
        
        answer_dict = {index: response.choices[index].message.content for index in range(self.n)}
        
        for index, answer in answer_dict.items():
            self.control_messages(role="assistant", content=answer)
            if self.n > 1:
                self.check_logger()
                self.logs.info(f"回答({index+1}): {answer.strip()}\n\n")
            else:
                self.check_logger()
                self.logs.info(f"回答: {answer.strip()}\n\n")    
            answer_list.append(answer.strip())
        
        return answer_list
    