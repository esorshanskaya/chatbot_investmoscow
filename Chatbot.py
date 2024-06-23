import gradio as gr
import os
import dotenv

dotenv.load_dotenv()

host = os.environ.get("HOST", "127.0.0.1")
redirect_host = os.environ.get("LINK_HOST", "127.0.0.1")
auth_port = 8082
guest_port = 8083

dict_auth = {True : {'creds': ('admin','pass'), 
                     "button_name": 'Выйти', 
                     "redirect_host": f"{redirect_host}:{auth_port}"},
             
             False : {'creds': (None, None), 
                     "button_name": 'Авторизация', 
                     "redirect_host": f"{redirect_host}:{guest_port}"},
    }


def convert_to_text(arr):
    if not arr:
        return ''
    return ' '.join([val for ar_1 in arr for val in ar_1])




def create_chatbot(fn_wrap, fn_wrap_reset=None, auth = False):
        css = """
        #chatbot {background-color: #F8F8F8}
        #button2 {background-color: transparent; border: none; flex-wrap: nowrap;}
        """

        with gr.Blocks(css = css,theme = gr.themes.Default()\
                    .set(button_primary_background_fill="#CE0A1E", \
                         button_secondary_background_fill="#CE0A1E",\
                         button_primary_text_color="white",\
                         button_secondary_text_color="white",\
                         button_primary_text_color_dark="white",\
                         button_secondary_text_color_dark="white",\
                         button_primary_background_fill_hover='#B00421',\
                         button_secondary_background_fill_hover='#B00421',
                         button_primary_background_fill_dark='#B00421',
                         button_secondary_background_fill_dark="#CE0A1E"
                        )) as demo:
            image = gr.Image(value = 'logo.png', show_label=False, show_download_button = False)
            if auth:
                text = gr.Markdown(\
                         f'<div style="text-align: right;">  Вы авторизовались как <span style="color:#CE0A1E"> admin</span> <a href="{dict_auth[not auth]["redirect_host"]}"><img src="https://i.postimg.cc/8z68cTWJ/666d8f904b80f-1718456307-666d8f904b808.png" width="15" height="20" style="display:inline;"></a></div>')

            else:
                button_auth = gr.Button(value = dict_auth[auth]["button_name"], link = dict_auth[auth]['redirect_host'], \
                               elem_id="button1", elem_classes = 'button1')
                    
            if fn_wrap_reset:
                button_reset = gr.Button(value = 'Сброс диалога', \
                   elem_id="button_reset", elem_classes = 'button_reset')
                button_reset.click(fn_wrap_reset)

            chatbot = gr.ChatInterface(fn = fn_wrap, \
                                        chatbot = gr.Chatbot(
                                                    show_label=False,
                                                    scale=1,  
                                                    render = False,\
                                                    height = 500,
                                                    elem_id="chatbot",
                                                    value = [[None,\
                                                              'Добрый день! Вас привествует чат-бот поддержки инвестиционного портала Москвы']]),\
                                        textbox=gr.Textbox(placeholder="Введите запрос...", \
                                                        render=False, show_label = False, \
                                                        scale=7),\
                                        submit_btn = 'Отправить', 
                                        retry_btn = 'Повторить',\
                                        clear_btn = 'Очистить историю',\
                                        undo_btn = 'Отменить')

        return demo

