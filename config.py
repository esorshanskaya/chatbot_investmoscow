from GigaChat import GigaChat
from PIL import Image 

params = {'img_path': '.../logo.png',\
          'system_prompt' : 'Отвечай как будто ты работник госуслуг',\
          'auth_token': 'ZGUxYmViNDQtYTgyZS00OGM3LWI0Y2YtYWJmMjY3ZjZlYTY2OjM0NGVlYzVmLWIwYmItNGI1YS1hZmZiLTFiNzNhZmY1ZmEzNg=='}

def init():

    logo = Image.open(params['img_path'])
 

    model = GigaChat(auth_token=params['auth_token'])
    
  

    return logo, model, params['system_prompt']