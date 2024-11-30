import streamlit as st
import requests
import json
import os

# Загружаем переменные окружения из .env файла
# load_dotenv()

# URL вашего API (измените на адрес вашего backend)
# API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/user")
API_URL = "http://127.0.0.1:8000/user"

# Страница для авторизации
def login():
    st.title('Авторизация')

    # Ввод данных пользователя
    email = st.text_input('Email')
    password = st.text_input('Пароль', type='password')

    if st.button('Войти'):
        # Формируем данные для запроса
        data = {
            'username': email,
            'password': password
        }

        # Отправка POST запроса на /token для получения токена
        response = requests.post(f"{API_URL}/token", data=data)

        if response.status_code == 200:
            # Сохраняем токен в сессию
            token = response.json()['access_token']
            st.session_state.token = token
            st.success("Вы успешно авторизованы!")
            st.experimental_rerun()
        else:
            st.error("Неправильный email или пароль!")

# Главная страница после авторизации
def dashboard():
    st.title(f"Добро пожаловать, {st.session_state.user_data['email']}!")

    if st.button('Получить данные пользователя'):
        # Отправка GET запроса для получения данных о пользователе
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        response = requests.get(f"{API_URL}/login", headers=headers)

        if response.status_code == 200:
            user_data = response.json()
            st.write("Данные пользователя:", user_data)
        else:
            st.error("Ошибка при получении данных!")

    if st.button('Выйти'):
        st.session_state.clear()  # Очищаем сессию
        st.experimental_rerun()

# Основная логика
if 'token' not in st.session_state:
    st.session_state.token = None

if 'user_data' not in st.session_state:
    st.session_state.user_data = {}

if st.session_state.token:
    # Пользователь авторизован
    dashboard()
else:
    # Если токен отсутствует, показываем форму для авторизации
    login()
