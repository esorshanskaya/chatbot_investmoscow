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

def fn_wrap_reset(*args, **kwargs):
    ds.reset_dialog()


if __name__ == '__main__':
        
        demo = create_chatbot(fn_wrap=fn_wrap, fn_wrap_reset=fn_wrap_reset, auth=False)
        demo.launch(debug = True, server_name=host, server_port=guest_port)
