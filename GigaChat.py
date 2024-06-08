import requests
import uuid
import json
import datetime
import pandas as pd


class GigaChat:
    def __init__(self, auth_token):
        self.auth_token = auth_token
        # links
        self.url_iam_token = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        self.url_gen = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
        self.url_emb = "https://gigachat.devices.sberbank.ru/api/v1/embeddings"

        self._update_iam_token()


    def _update_iam_token(self):
        
        rq_uid = str(uuid.uuid4()) 
        
        payload='scope=GIGACHAT_API_PERS'
        headers = {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Accept': 'application/json',
          'RqUID': rq_uid,
          'Authorization': f'Basic {self.auth_token}'
        }
        self.iam_token = json.loads(requests.request("POST", self.url_iam_token, 
                                                     headers=headers, data=payload, verify=False).text)['access_token']
        self.iam_token_time = datetime.datetime.now()
        print('New iam token was generated')

    def _check_iam_token(self):
        now = datetime.datetime.now()
        if (now - self.iam_token_time)/pd.Timedelta(minutes=1)>20:
            self._update_iam_token()

    def generate(self, system_prompt, user_prompt, gen_params = {}, model = "GigaChat-Pro"):
        self._check_iam_token()
        headers = {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Authorization': f'Bearer {self.iam_token}'
        }
        payload = json.dumps({
          "model": f"{model}",
          "messages": [
            {
              "role": "system",
              "content": system_prompt,
            },
            {
              "role": "user",
              "content": user_prompt,
            },
          ],
        })
        for k,v in gen_params:
            payload[k] = v

        try:
            response = requests.request("POST", self.url_gen, headers=headers, data=payload, verify=False)
            msg = json.loads(response.text)['choices'][0]['message']['content']
            return msg
        except:
            print(requests)
            print(response)
            raise
            


    def get_embedding(self, docs: list):
        self._check_iam_token()
        headers = {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Authorization':  f'Bearer {self.iam_token}'
        }
        if type(docs) is str:
            docs = [docs]
            
        payload = json.dumps({
          "model": "Embeddings",
          "input": docs
        })

        try:
            response = requests.request("POST", self.url_emb, headers=headers, data=payload, verify=False)
            result = json.loads(response.text)
            embeddings = [i['embedding'] for i in result['data']]
            return embeddings
        except:
            print(requests)
            print(response)
            raise
