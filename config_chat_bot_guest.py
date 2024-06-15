import sys
sys.path.append('dialog_manager//')
import gradio as gr
from DialogNodes import *
from DialogManager import *
from params import *
from MaintenanceAssistant import prompt_dict
import pandas as pd
from GigaChat import GigaChat
import regex as re
import tqdm
import json
import pprint
import chromadb
import os
import dotenv
import copy

dotenv.load_dotenv()


def get_dialog_manager(user_info={}):
    auth_token = os.environ.get('AUTH_TOKEN')
    
    gc = GigaChat(auth_token=auth_token)
    
    chroma_client = chromadb.PersistentClient(path='./chroma/')
    collection = chroma_client.get_or_create_collection(name="okved_collection")
    
    
    df_park = pd.read_excel(r'raw_data//ОЭЗ и технопарки.xlsx')
    df_land = pd.read_excel(r'raw_data/_Помещения и сооружения_clean.xlsx')
    
    
    park_list = ['Наименование объекта', 'Налог на прибыль', 'Как стать резидентом', ]
    df_park = df_park.rename(columns = {"Наименование объекта": "Название технопарка"})
    
    df_park['Название технопарка'] = df_park['Название технопарка'].str.strip('\n').str.strip()
    df_land['Название площадки'] = df_land['Название площадки'].str.replace('\n', '')
    park_list = ['Название технопарка', 'Налог на прибыль', 'Как стать резидентом', ]
    df_park = df_park[df_park['Название технопарка'].isin(df_land['Название технопарка'])]
    
    df_land = df_land.merge(df_park, on = ['Название технопарка'])
    df_land['Ссылка на форму подачи заявки'] = df_land['Ссылка на форму подачи заявки'].str.strip('\n').str.strip()
    mandatory_land_list = [
                'Перечень видов экономической деятельности, возможных к реализации на площадке',
                'Стоимость, руб./год за кв.м.',
                'Водоснабжение Наличие (Да/Нет)',
                'Газоснабжение Наличие (Да/Нет)',
                'Электроснабжение Наличие (Да/Нет)',
                'Теплоснабжение Наличие (Да/Нет)',
                'Вывоз ТКО Наличие (Да/Нет)',
                'Наличие МАИП',
                'Стоимость объекта, руб. (покупки или месячной аренды)', 
                'Свободная площадь здания, сооружения, помещения, кв. м',
    ]
    
    info_land_list = [
                'Название площадки',
                'Объект инфраструктуры поддержки',
                'Название технопарка',
                # 'Адрес объекта',
                'Ссылка на форму подачи заявки',
                # 'Сайт',
                'Описание процедуры подачи заявки',
                'Стоимость, руб./год за кв.м.', 
                'Налог на прибыль', 
                'Как стать резидентом'
    ]
    
    df_land = df_land[info_land_list + mandatory_land_list]
    service_data = pd.read_excel("raw_data/Региональные меры поддержки Москва.xlsx")
    
    df_land['Свободная площадь здания, сооружения, помещения, кв. м'] =\
            df_land['Свободная площадь здания, сооружения, помещения, кв. м'].str.replace(',', '.').astype(float)
    
    
    
    system_prompt_service_classification = \
    """
    Тебе необходимо классифицировать обращение пользователя по одному из 5 вариантов. Первые 4 относятся к вопросам про бизнес, всё остальное нужно относить к 5 классу
    Пользователи отправлят запросы для чат-бота сайта департамента инвестиций Москвы
    Классы обращений:
    1) Подобрать помещение для бизнеса, пользователь хочет узнать про варианты аренды и помещений. В этот класс входят вопросы про аренду, помещения или площадки.
    2) Подобрать меру поддержки для бизнеса - пользователь хочет узнать про гранты, сопровождения, субсидии и т.д. В этот класс не входят вопросы про площадки и помещения.
    3) Общая информация по порталу - как регистрироваться, чем мы занимаемся, какие есть услуги и т.д.
    4) Пользователь спрашиват про инвестицинный калькулятор для рассчита возможного объема затрат для создания бизнеса \ предприятия. Также пользовать просит рассчитать объем инвестиций
    5) Пользователь спрашиват про оформление паспорта объекта культурного наследия. Также пользователь хочет зарегестрировать объект культурного наследия
    6) Другое. Если вопрос или текст не связан с бизнес активностью или определить невозможно - использовать этот вариант
    Укажи номер класса
    Второй строкой объясни почему запрос пользователя относится к указанному классу.
    """
    template_not_found = 'Мне не удалось найти необходимую Вам информацию. Пожалуйста, воспользуйтесь официальным сайтом: https://investmoscow.ru/'
    
    system_prompt_casual_info = """
    Использую информацию из контекста ниже чтобы ответить на вопрос пользователя
    Контекст:
    Для регистрации на Портале необходимо в верхнем правом углу страницы Портала нажать (скриншот), далее следует заполнить соответствующие поля: тип пользователя (укажите, кем вы являетесь: юридическим лицом, ИП, физическим лицом), введите персональные данные, установите пароль. 
    В случае возникновения дополнительных вопросов готовы переключить Вас на соответствующего специалиста.
    Для того, чтобы найти интересующие торги, необходимо на Инвестиционном Портале investmoscow.ru (инвестмоскоу точка ру) зайти в раздел «Имущество от города», далее в «Расширенном поиске» сформировать критерии поиска интересующих торгов: цену, тип объекта, вид торгов, площадь помещения, предпочтительный район или станцию метро. 
    В случае возникновения дополнительных вопросов, готовы переключить Вас на соответствующего специалиста.
    Сейчас на Портале работает более 100 онлайн-сервисов. С их помощью можно подать заявки на получение льгот, направить на рассмотрение концессионную инициативу, записаться на осмотр городской недвижимости, выставленной на торги, задать вопрос или сообщить в Правительство столицы о проблеме, связанной с инвестированием и многое другое. Найти сервисы можно на Инвестиционном портале investmoscow.ru (инвестмоскоу точка ру) в разделе «Каталог сервисов». Ссылка на него доступна на главной странице сайта вверху. 
    Сроки рассмотрения обращений на линию прямых обращений не более 14 дней для физических лиц и не более 30 дней для юридических лиц. Также обращение в орган исполнительной власти города Москвы можно направить через онлайн-сервис «Московский инвестор». Средний срок ответа составляет 10 рабочих дней. 
    
    
    Используй информацию из контекста чтобы ответить на вопрос пользователя:
    Налоги для всех особенных экономических зон и всех Технопарков
    -налог на прибыль – 2%
    -налог на имущество – 2%
    -транспортный налог – 0%
    -таможенные пошлины – 0%
    
    Заявка на аренду помещения в технопарке подаётся в электронном виде при помощи Инвестиционного портала города Москвы.
    Выберите заинтересовавший Вас технопарк и направьте заявку.
    Срок рассмотрения заявки физических лиц не превышает 14 календарных дней.
    Срок рассмотрения заявки юридических лиц и индивидуальных предпринимателей не превышает 30 календарных дней."""
    
    
    system_prompt_land_classification = \
    """Тебе необходимо классифицировать обращение пользователя по одному из 3 вариантов.
    Классы обращений:
    1) Пользователь просит подобрать варианты аренды помещений или технопарков под его бизнес, пользователь не знает про конкретные варианты
    2) Пользователь спрашивает про конкретную программу аренды помещений или технопарки.
    3) Другое или невозможно определить
    Примеры ответов:
    2 - Технопарк Москвы
    3 - невозможно определить
    """
    
    system_prompt_land_ner = """Тебе необходимо извлечь информацию в формате JSON по следующим параметрам:
        Тип деятельности бизнеса
        Если информации нет, не добавляй в JSON файл
        Пример 1 - {"Тип деятельности бизнеса": "Разработка приложений"}
        Пример 2 - {"Тип деятельности бизнеса": "Разведение пчел", "Минимальная площадь в м2": 130}
        Не отвечай на вопрос, вытащи информацию в формате JSON, не пиши ничего больше будет ошибка парсинга.
        Пользователь интересуется арендой помещения под бизнес, аренда помещений не является сутью бизнеса.
        Не указывай в "Тип деятельности бизнеса" аренду помещений 
        В Минимальная площади укавай только число"""
    
    
    df_land_instruct_context = str(df_land[['Название площадки', 'Название технопарка', 'Ссылка на форму подачи заявки', 
             'Свободная площадь здания, сооружения, помещения, кв. м']].to_dict(orient='records'))
    
    system_prompt_land_instruct = f"""
    Используй информацию из контекста чтобы ответить на вопрос пользователя:
    Налоги для всех особенных экономических зон и всех Технопарков
    -налог на прибыль – 2%
    -налог на имущество – 2%
    -транспортный налог – 0%
    -таможенные пошлины – 0%
    
    Таблица с возможными вариантами аренды площадок для бизнеса: {df_land_instruct_context}
    """
    
    
    init_node = {"id": "init_node",
                 "type": LLM_Classifier, 
                 "system_prompt": system_prompt_service_classification,
                 "default_class": 6,
                 "key": "last_msg",
                 "description":  "Основной классификатор диалога",
                 "childs": {}}
    
    # =============================================================================
    
    # Короткие Dummy заглушки
    
    
    # 3 Ветка с общей инфой
    instruct_causal_info = {"id": "init_node",
                     "type": LLM_Generator, 
                     "system_prompt": system_prompt_casual_info,
                     "key": "last_msg",
                     "description":  "Основной классификатор диалога",
                     "childs": {}}
    init_node['childs'][3] = instruct_causal_info
    
    # 4 Инвест калькулятор
    dummy_invest_calc = {"id": "dummy_invest_calc",
                       "type": LLM_Generator, 
                       "key": "last_msg",
                       "dummy_answer": "Ссылка на Инвестиционный калькулятор: https://investmoscow.ru/catalog/23",
                       "description":  "Инвест калькулятор",
                       "childs": {}}
    init_node['childs'][4] = dummy_invest_calc
    
    # 5 Паспорт объекта культурного наследия
    dummy_culture_passport = {"id": "dummy_culture_passport",
                               "type": LLM_Generator, 
                               "key": "last_msg",
                               "dummy_answer": "Ссылка на оформление паспорта объекта культурного наследия: https://investmoscow.ru/catalog/88",
                               "description":  "Паспорт объекта культурного наследия",
                               "childs": {}}
    init_node['childs'][5] = dummy_culture_passport
    
    
    # 6 Короткая ветка с заглушкой - Не найдено
    dummy_not_found = {"id": "dummy_not_found",
                       "type": LLM_Generator, 
                       "required_answer": False, 
                       "key": "last_msg",
                       "dummy_answer": template_not_found,
                       "description":  "Dummy заглушка основного классификатора",
                       "childs": {}}
    init_node['childs'][init_node['default_class']] = dummy_not_found
    
    
    # =============================================================================
    
    
    # 1 Ветка Land
    land_request_classification = {"id": "land_request_classification",
                                   "key": "last_request",
                                   "type": LLM_Classifier, 
                                   "key": "last_msg",
                                   "system_prompt": system_prompt_land_classification,
                                   "default_class": 3,
                                   "description": "Классификатор земельных вопросов",
                                   "childs": {}}
    init_node['childs'][1] = land_request_classification
    
    # 1.1 - Пользователь хочет подобрать меры поддержки
    # 1.1.1 Вычленение сущностей, если пользователь просит подобрать землю
    ner_land_params = {"id": "ner_land_params",
                       "type": LLM_Extractor, 
                       "key": "last_msg",
                       "system_prompt": system_prompt_land_ner,
                       "entity_list": ["Тип деятельности бизнеса", "Минимальная площадь в м2"],
                       "description": "NER для подбора земли",
                       "childs": {}}
    ner_land_params_2_iter = {"id": "ner_land_params_2_iter",
                       "type": ner_land_params['type'], 
                       "key": "last_msg",
                       "system_prompt": ner_land_params['system_prompt'],
                       "entity_list": ner_land_params['entity_list'],
                       "description": ner_land_params['description'],
                       "childs": {}}
    land_request_classification['childs'][1] = ner_land_params
    
    # 1.1.2 Если пользователь указал не всю информацию
    dummy_get_more_info_land = {"id": "dummy_get_more_info_land",
                               "type": LLM_Generator, 
                               "key": "last_msg",
                               "dummy_answer": 'Пожалуйста, Опишите деятельность вашего бизнеса и желаемую площадь для более корректного поиска',
                               "description":  "Dummy заглушка - необходимо больше информации",
                               "childs": {}}
    
    # вторая итерция - переспросить еще раз
    ner_land_params['childs'][status_extractor_not_found] = dummy_get_more_info_land
    # 1.1.2.1 - Узнать ОКВЕД по RAG
    rag_okved_ok = {"id": "rag_okved_ok",
                       "type": RAG_Classifier, 
                       "collection": collection,
                       "target_field": 'code',
                       "top_n": 3,
                       "description": 'RAG классификатор ОКВЭД',
                       "key": "Тип деятельности бизнеса",
                       "childs": {}}
    ner_land_params['childs'][status_extractor_ok] = rag_okved_ok
    
    rag_okved_not_found = {"id": "rag_okved_not_found",
                           "type": RAG_Classifier,
                           "collection": collection,
                           "target_field": 'code',
                           "top_n": 3,
                           "description": 'RAG классификатор ОКВЭД',
                           "key": "last_msg",
                           "childs": {}}
    dummy_get_more_info_land['childs'][default_child_key] = ner_land_params_2_iter
    ner_land_params_2_iter['childs'][status_extractor_not_found] = rag_okved_not_found
    ner_land_params_2_iter['childs'][status_extractor_ok] = rag_okved_ok
    
    rag_okved_not_found = {"id": "rag_okved_not_found",
                           "type": RAG_Classifier,
                           "collection": collection,
                           "target_field": 'code',
                           "top_n": 3,
                           "description": 'RAG классификатор ОКВЭД',
                           "key": "last_msg",
                           "childs": {}}
    
    dim_search_land = {"id": "dim_search_land",
                       "type": Dim_Search_Land,
                       "dim": df_land.copy(),
                       "description": "Генерация ответа по справочным данным",
                       "childs": {}}
    
    rag_okved_ok['childs'][default_child_key] = dim_search_land
    rag_okved_not_found['childs'][default_child_key] = dim_search_land
    
    
    # 1.2 Пользователь хочет узнать про конкретный парк
    land_instruct = { "id": "land_instruct",
                       "type": LLM_Generator, 
                       "key": "last_msg",
                       "system_prompt": system_prompt_land_instruct,
                       "description": "Выдача информации по Технопаркам",
                       "childs": {}}
    land_request_classification['childs'][2] = land_instruct
    
    
    
    # 1.3 Непоятно что пользователь хочет 
    land_request_classification['childs'][3] = dummy_not_found
    
    # =============================================================================
    # 2 - Вторая ветка - MaintenanceAssistant
    ma_node = {"id": "ma_node",
               "type": MaintenanceAssistant_Node,
               "prompt_dict": prompt_dict,
               "service_data": service_data,
               "description": 'MaintenanceAssistant Нода',
               "key": "last_msg",
               "childs": {}}
    # dummy_flow_2 = {"id": "dummy_flow_2",
    #                            "type": LLM_Generator, 
    #                            "key": "last_msg",
    #                            "dummy_answer": 'Здесь кое-что скоро будет!!',
    #                            "description":  "Dummy заглушка",
    #                            "childs": {}}
    init_node['childs'][2] = ma_node
    
    
    # Создать дерево диалога
    dialog_tree = get_dialog_tree(init_node, gc=gc)

    ds = DialogSession(dialog_tree, user_id='user', user_info=user_info)

    return ds
