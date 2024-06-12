class MaintenanceAssistant():
    def __init__(self, prompt_dict, model, service_data):
        #LLM
        self.model = model
        # данные
        self.service_data = service_data
        self.types = [f'{i+1}){type}' for i,type in enumerate(self.service_data['Вид поддержки'].unique())] + ['1000) Другое или невозможно определить']
        self.names = names = [f'{i+1}){name}' for i,name in enumerate(self.service_data['Наименование меры поддержки'].unique())] + ['1000) Другое или невозможно определить']
        self.okved_dict = self.__okved_dict()
        # общий классификатор по разделам
        self.system_prompt_classification = prompt_dict['general_classification']
        # ОКВЭД/виды бизнеса
        self.system_prompt_business_classification = prompt_dict['business_classification'].format(okved = list(okved_dict.keys()))
        #Конкретная мера поддержки
        self.system_prompt_service_classification = prompt_dict['service_classification'].format(names = self.names)
        self.system_prompt_service_information = prompt_dict['service_information']
        # Виды меры поддержки
        self.system_prompt_type_classification = prompt_dict['type_classification'].format(types = self.types)


        
    
        
    def respond(self,req):
        self.log = {}
        ans = self.model.generate(system_prompt=self.system_prompt_classification, 
        user_prompt=req)
        q_class = self.__convert_class(ans, negative_class = 4)
        self.log['gen_class'] = q_class
        match q_class:
            case 1:
                ans = self.__business_request(req)
            case 2:
                ans = self.__service_request(req)
            case 3:
                ans = self.__type_request(req)
            case -1:
                ans = self.__other_request(req)
        return ans, self.log
                
    def __business_request(self,req):
        ans = self.model.generate(system_prompt=self.system_prompt_business_classification, 
        user_prompt=req)
        service_list = self.okved_dict.get(ans,None)
        if service_list:
            service_list = self.service_data.iloc[service_list]['Наименование меры поддержки'].values
            return f'По вашей экономической деятельности найден следующий список мер поддержки и услуг: {",/n".join(service_list)}'
        else:
            return 'Вид экономической деятельности не определен. Попробуйте переформулировать запрос'
    
    def __service_request(self,req):
        ans = self.model.generate(system_prompt=self.system_prompt_service_classification, 
        user_prompt=req)
        service_num = self.__convert_class(ans,negative_class = 1000)
        self.log['service_num'] = service_num
        if service_num != -1:
            info = dict(self.service_data.iloc[service_num - 1])
            ans = self.model.generate(system_prompt=self.system_prompt_service_information.format(info = info), 
                                                                                        user_prompt=req)
            add = f'Для получения более подробной информации, пожалуйста, воспользуйтесь ссылкой на форму поддачи: {info["Ссылка на форму подачи заявки"]}'
            return ans+add
        else:
            return 'Запрашиваемая информация не найдена. Попробуйте переформулировать запрос'
    
    def __type_request(self,req):
        ans = self.model.generate(system_prompt=self.system_prompt_type_classification, 
                user_prompt=req)
        type_num = self.__convert_class(ans,negative_class = 1000)
        self.log['type_num'] = type_num
        if type_num != -1:
            service_list = self.service_data[self.service_data['Вид поддержки']== self.service_data['Вид поддержки'].unique()[type_num-1]]['Наименование меры поддержки']
            return f'По данному виду доступные следующие меры поддержки и услуги: {";/n".join(service_list)}'
        else:
            return f'Запрашиваемый вид мер поддержки не найден. Доступные меры: {",/n".join(self.types)}'
    
    def __other_request(self,req):
        return 'Мне не удалось найти необходимую Вам информацию. Пожалуйста, воспользуйтесь официальным сайтом: https://investmoscow.ru/'

    
    
    def __convert_class(self,ans, negative_class):
        try:
            cls = int(ans[0])
            return cls if cls != negative_class else -1
        except Exception:
            return -1
    
    def __okved_dict(self):
        def get_service_dict(okved):
            target_list = []
            for idx, row in self.service_data.iterrows():
                if okved in row['ОКВЭД']:
                    target_list.append(idx)
            return target_list
        
        self.service_data['ОКВЭД'] = self.service_data['ОКВЭД'].str.replace('\xa0',' ').str.replace('газом и паром;','газом и паром,')\
            .str.replace('офисов;','офисов,').str.replace('Сбор, обработка и утилизация отходов;','Сбор, обработка и утилизация отходов,')\
            .str.replace('проектирования; технических','проектирования, технических').str.replace('Нет ограничений','00 - Нет ограничений')\
            .str.replace('11-','11 -')
        okved_dict = {x.split(' ')[0] : get_service_dict(x.split(' ')[0]) for x in okved_list}
        return okved_dict
    
    
prompt_dict = {
    'general_classification': """Тебе необходимо классифицировать обращение пользователя по одному из 4 вариантов.
Классы обращений:
1) Пользователь просит перечислить доступные меры поддержки по ОКВЭД/типу бизнеса
2) Пользователь спрашивает информацию про конкретную меру поддержки бизнеса/услугу/государственные программы
3) Пользователь просит перечислить все доступные меры поддержки какого-то конкретного вида (Например "субсидии и гранты", "льготы","консультации")
4) Другое или невозможно определить (Все нерелеватные вопросы, в т.ч. по площадкам, земельным участкам и пр.)
Укажи номер класса в виде числа без дополнительный символов
Второй строкой объясни почему запрос пользователя относится к указанному классу.
""",\
    
    'business_classification': """ Тебе необходимо классифицировать запрос пользователя по одному из следующех вариантов: {okved}
Не отвечай на сам запрос! Ответ выдай только в виде номера класса""",\
    
    'service_classification' : """ Тебе необходимо классифицировать запрос пользователя по одному из следующех вариантов: {names}
Не отвечай на сам запрос! Ответ выдай только в виде номера класса""",\
    
    'type_classification' : """Тебе необходимо классифицировать запрос пользователя на один из следующих вариантов: {types}
Не отвечай на сам запрос! Ответ выдай только в виде номера класса""",\
    
    'service_information' : """Используй информацию из следующего словаря для ответа на запрос пользователя: {info}. /n 
Дай краткое описание услуги и ответь на интересующий вопрос пользователя при помощи данной информации.
Не указывай ссылки в ответе! Не упоминай, что ты используешь словарь""",
    
    
}    
    
# Пример использования:
# df_service = pd.read_excel('Региональные меры поддержки Москва.xlsx')
# assistant = MaintenanceAssistant(prompt_dict = prompt_dict, model = gc, service_data = df_service)
# assistan.respond('Интересует возможность вступления в реестр альтернативных поставщиков?')