
# Проект ИИ Чат-бота для Департамента инвестиционной политики города Москвы

## Содеражание
- [Установка](#установка)
- [Авторы](#авторы)


## Установка
Процесс установки делится на 3 этапа:
1) Клонирования репозитория
2) Указать токен для GigaChat
3) Запустить сервера

Для Клонирования нужно запустить команду в терминале
```
git clone https://github.com/esorshanskaya/hackathon_0624.git
cd hackathon_0624
```

Для Gigachat нужно создать файл ```.env``` и добавить туда строчку ```AUTH_TOKEN = <Ваш Gigachat OAuth токен>```. Так же опционально можно указать ```HOST```, если он отличен от localhost.

Для запуска сервиса нужно выполнить следующую команду.

```
bash ./app.sh
```
## Авторы

Команда 2NoNames