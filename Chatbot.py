import gradio as gr
from config import init





logo, model, system_prompt = init()  


def convert_to_text(arr):
    if not arr:
        return ''
    return ' '.join([val for ar_1 in arr for val in ar_1])




def LLM_respond(message, history, model = model, system_prompt = 'Отвечай как будто ты консультант из Маккинзи'):
    input = convert_to_text(history) + message 
    ans = model.generate(system_prompt=system_prompt, 
            user_prompt=input)
    return ans


dict_auth = {True : (('admin','pass'),'Выйти','http://51.250.17.38:8082/'),\
             False : (None,'Авторизация','http://51.250.17.38:8083/')
    }

dict_auth = {True : (('admin','pass'),'Выйти','http://51.250.17.38:8082/'),\
             False : (None,'Авторизация','http://51.250.17.38:8083/')
    }

def create_chatbot(fn_wrap,auth = False):
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
                    text = gr.Markdown(f'<div style="text-align: right;">  Вы авторизовались как <span style="color:#CE0A1E"> admin</span> <a href="{dict_auth[auth][2]}"><img src="https://i.postimg.cc/8z68cTWJ/666d8f904b80f-1718456307-666d8f904b808.png" width="15" height="20" style="display:inline;"></a></div>')

            else:
                button = gr.Button(value = dict_auth[auth][1], link = dict_auth[auth][2], \
                               elem_id="button1", elem_classes = 'button1')
                    
            
            chatbot = gr.ChatInterface(fn = fn_wrap, \
                                        chatbot = gr.Chatbot(
                                                    show_label=False,
                                                    scale=1,  render = False,\
                                                    elem_id="chatbot",
                                                    value = [[None,\
                                                              'Добрый день! Вас привествует чат-бот поддержки инвестиционного портала Москвы']]),\
                                        textbox=gr.Textbox(placeholder="Введите запрос...", \
                                                        render=False, show_label = False, \
                                                        scale=7),\
                                        submit_btn = 'Отправить', retry_btn = 'Повторить',\
                                        clear_btn = 'Очистить историю',\
                                        undo_btn ='Отменить')

        return demo

if __name__ == '__main__':
        
        demo_1 = create_chatbot(fn_wrap = LLM_respond,auth = False)
        demo_1.launch(debug = True, server_name="0.0.0.0", server_port=8082)
        demo_2 = create_chatbot(fn_wrap = LLM_respond,auth = True)
        demo_2.launch(debug = True, server_name="0.0.0.0", server_port=8083,auth = dict_auth[True][0])