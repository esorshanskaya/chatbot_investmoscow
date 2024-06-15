from GigaChat import GigaChat
from PIL import Image 
import os
import dotenv

dotenv.load_dotenv()

params = {'img_path': '.../logo.png',\
          'system_prompt' : 'Отвечай как будто ты работник госуслуг',\
          'auth_token': os.environ.get('AUTH_TOKEN')}

def init():

    logo = Image.open(params['img_path'])
 

    model = GigaChat(auth_token=params['auth_token'])
    
  

    return logo, model, params['system_prompt']