import os
import time
import logging
import openai
from transformers import pipeline

timestamp = time.strftime('%Y%m%d', time.localtime())


# 加载GPT-2模型
def call_chatgpt2(task="text-generation"):
    models = pipeline(task=task, model='gpt2')
    
    return models


# 加载GPT-3模型
class CallChatGPT3:
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
                 logsname=f"chatgpt_{timestamp}.log"):
        self.api_key = api_key
        self.model = model
        self.messages = []
        self.token_nums = []
        self.total_tokens = 0
        self.temperature = temperature
        self.top_p = top_p
        self.n = n 
        self.stream = stream
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.logsdir = logsdir
        self.logsname = logsname
        self.logspath = os.path.join(logsdir, logsname)
        self.logs = self.built_logger()
    
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
    
    def reset_messages(self):
        self.messages = []
        self.token_nums = []
        self.total_tokens = 0
    
    def control_token(self, mode=True): 
        if mode:
            self.total_tokens = self.token_nums[-1].total_tokens
        else:
            self.total_tokens -= (self.token_nums.pop(0).total_tokens - 2**2)
    
    def __call__(self, prompt):
        while self.total_tokens >= 4096:
            if len(self.messages) != 0:
                for _ in range(2):
                    self.messages.pop(0)
                self.control_token(False)
            else:
                self.messages = []
                self.token_nums = []
                self.total_tokens = 0

        self.check_logger()
        self.logs.info(f"提问: {prompt}\n")        
          
        answer_list = []
        try:
            self.messages.append({"role": "user", "content": prompt})
            response = self.openai_gptapi() 
            self.token_nums.append(response.usage)
            self.control_token(True)          
        except openai.error.InvalidRequestError: 
            answer_list = ["输入内容的编码数超过OpenAI所允许的上限值4096，请精简输入内容！"]
            
            return answer_list
        
        outputs = {index: response.choices[index].message.content for index in range(self.n)}
        for index, answer in outputs.items():
            self.messages.append({"role": "assistant", "content": answer})
            if self.n > 1:
                self.check_logger()
                self.logs.info(f"回答({index+1}): {answer.strip()}\n\n")
            else:
                self.check_logger()
                self.logs.info(f"回答: {answer.strip()}\n\n")    
            answer_list.append(answer.strip())
        
        return answer_list
    