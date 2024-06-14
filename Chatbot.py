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

def create_chatbot():
        css = """
        #chatbot {background-color: #F8F8F8}
        """

        with gr.Blocks(css = css,theme = gr.themes.Default()\
                    .set(button_primary_background_fill="#CE0A1E", button_secondary_background_fill="#CE0A1E",\
                        button_primary_text_color="white",\
                        button_secondary_text_color="white",\
                        button_primary_background_fill_hover='#B00421',\
                        button_secondary_background_fill_hover='#B00421',
                        )) as demo:
            image = gr.Image(value = logo, show_label=False, show_download_button = False)
            button = gr.Button(value = 'Авторизация', link = 'https://google.com', elem_id="button1", elem_classes = 'button1')
            chatbot = gr.ChatInterface(fn = LLM_respond, \
                                        chatbot = gr.Chatbot(
                            label="Интерактивный помощник", scale=1, render = False,elem_id="chatbot"),\
                                        textbox=gr.Textbox(placeholder="Введите запрос...", \
                                                        render=False, show_label = False, scale=7),\
                                        submit_btn = 'Отправить', retry_btn = 'Повторить',\
                                        clear_btn = 'Очистить историю',\
                                        undo_btn ='Отменить')

        return demo

if __name__ == '__main__':
        
        demo = create_chatbot()
        demo.launch(debug = True, server_name="0.0.0.0", server_port=8081)