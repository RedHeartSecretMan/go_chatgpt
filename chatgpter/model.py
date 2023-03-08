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
        self.token_num = 0
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
        self.token_num = 0
    
    def count_token(self, content, mode=True):
        if mode:
            self.token_num += 2*(len(content)+2)
        else:
            self.token_num -= 2*(len(content)+2)
    
    def __call__(self, prompt):
        answer_list = []
        tips = ""
        if 2*(len(prompt)+2) >= 4000:
            answer_list = ["内容太长ChatGPT将无法工作"]
            
            return answer_list, tips
        
        self.check_logger()
        self.logs.info(f"提问: {prompt}\n")        
        self.messages.append({"role": "user", "content": prompt})
        self.count_token(prompt, True)
        while self.token_num >= 4000:
            if len(self.messages) != 0:
                self.count_token(self.messages.pop(0)["content"], False)
                tips = ["内容太长ChatGPT将遗忘最初的部分"]
            else:
                self.token_num = 0
        
        response = self.openai_gptapi()     
        
        output_content = {i: response.choices[i].message.content for i in range(self.n)}
        for num, answer in output_content.items():
            self.messages.append({"role": "assistant", "content": answer})
            self.count_token(answer, True)
            if self.n > 1:
                self.check_logger()
                self.logs.info(f"回答({num+1}): {answer.strip()}\n\n")
            else:
                self.check_logger()
                self.logs.info(f"回答: {answer.strip()}\n\n")    
            answer_list.append(answer.strip())

        return answer_list, tips


if __name__ == "__main__":      
    model = CallChatGPT3()
    input_prompt = "你好"
    model(prompt=input_prompt)
    