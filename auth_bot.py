import sys
sys.path.append('dialog_manager//')
import config_chat_bot_auth
from Chatbot import create_chatbot, host,auth_port,dict_auth
import dotenv
dotenv.load_dotenv()


ds = config_chat_bot_auth.get_dialog_manager(user_info = {"Тип деятельности бизнеса": "Разработка искуственного интеллекта",
                                                                             "Минимальная площадь в м2": 50})
def fn_wrap(msg, history):
    answer = ds.send_msg(msg)
    return answer




if __name__ == '__main__':
        
        demo = create_chatbot(fn_wrap=fn_wrap,auth = True)
        demo.launch(debug = True, server_name=host, server_port=auth_port, auth = dict_auth[True]['creds'])
