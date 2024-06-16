import sys
sys.path.append('dialog_manager//')
import config_chat_bot_guest
import dotenv
from Chatbot import create_chatbot,host,guest_port,dict_auth
dotenv.load_dotenv()


ds = config_chat_bot_guest.get_dialog_manager()


def fn_wrap(msg, history):
    answer = ds.send_msg(msg)
    return answer



if __name__ == '__main__':
        
        demo = create_chatbot(fn_wrap=fn_wrap,auth=False, dict_auth = dict_auth)
        demo.launch(debug = True, server_name=host, server_port=guest_port)
