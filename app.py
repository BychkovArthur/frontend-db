import streamlit as st
import requests
from datetime import datetime, timedelta
from streamlit_cookies_controller import CookieController

# URL вашего API
API_URL_REGISTER = "http://localhost:8000/api/v1/user/register"
API_URL_TOKEN = "http://localhost:8000/api/v1/user/token"
API_URL_LOGIN = "http://localhost:8000/api/v1/user/login"  # Новый URL для проверки авторизации
API_URL_USERS = "http://localhost:8000/api/v1/user/get_all_except_self"  # URL для получения всех пользователей

# Инициализация CookieController
controller = CookieController()

# Функция для регистрации пользователя
def register_user(email: str, password: str, name: str, tag: str):
    user_data = {
        "email": email,
        "password": password,
        "name": name,
        "tag": tag
    }
    response = requests.post(API_URL_REGISTER, json=user_data)
    return response

# Функция для получения токена
def get_token(username: str, password: str):
    response = requests.post(API_URL_TOKEN, data={"username": username, "password": password})
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        st.error("Неверные данные для авторизации!")
        return None

# Функция для проверки авторизации через ручку /login
def check_authorization(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(API_URL_LOGIN, headers=headers)
    return response.status_code == 200

# Функция для получения всех пользователей
def get_all_users(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    with st.spinner('Загрузка пользователей...'):
        response = requests.get(API_URL_USERS, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Ошибка при получении пользователей!")
            return []
    
def get_user_subscriptions(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("http://localhost:8000/api/v1/subscriptions/", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Ошибка при получении подписок.")
        return []
    
def subscribe_user(token, other_user_id):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"http://localhost:8000/api/v1/subscriptions/subscribe/{other_user_id}", headers=headers)
    if response.status_code != 201:
        st.error(f"Ошибка при подписке: {response.json().get('detail', 'Неизвестная ошибка')}")
    st.rerun()

def unsubscribe_user(token, other_user_id):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"http://localhost:8000/api/v1/subscriptions/unsubscribe/{other_user_id}", headers=headers)
    if response.status_code != 200:
        st.error(f"Ошибка при отписке: {response.json().get('detail', 'Неизвестная ошибка')}")
    st.rerun()

# Страница регистрации
def registration_page():
    st.title("Регистрация")

    email = st.text_input("Email")
    password = st.text_input("Пароль", type="password")
    name = st.text_input("Имя")
    tag = st.text_input("Тег")

    if st.button("Зарегистрироваться"):
        if email and password and name and tag:
            response = register_user(email, password, name, tag)
            if response.status_code == 201:
                st.success("Пользователь успешно зарегистрирован! Перейдите на страницу входа.")
                st.session_state.registration_success = True
            else:
                st.error(f"Ошибка: {response.json().get('detail', 'Неизвестная ошибка')}")
        else:
            st.error("Пожалуйста, заполните все поля.")

# Страница входа для получения токена
def login_page():
    st.title("Вход")

    username = st.text_input("Email")
    password = st.text_input("Пароль", type="password")

    if st.button("Войти"):
        if username and password:
            token = get_token(username, password)
            if token:
                st.success(f"Авторизация прошла успешно!")
                
                # Устанавливаем cookie с токеном
                controller.set('jwt_token', token)

                st.session_state.token = token
            else:
                st.error("Ошибка авторизации!")
        else:
            st.error("Пожалуйста, заполните все поля.")

# Логика выхода из аккаунта
def logout():
    # Удаляем токен из cookies и сессии
    controller.remove('jwt_token')
    st.session_state.token = None
    st.success("Вы успешно вышли из аккаунта!")
    st.rerun()

# Главная страница
def home_page():
    # Проверяем токен в cookies
    token = controller.get('jwt_token')

    if token:
        if check_authorization(token):
            st.title("Главная страница")
            st.write("Вы в аккаунте!")  # Показываем, что пользователь авторизован

            # Кнопка для выхода из аккаунта
            if st.button("Выход"):
                logout()
        else:
            st.title("Главная страница")
            st.write("Невалидный токен. Пожалуйста, войдите снова.")
    else:
        st.title("Главная страница")
        st.write("Войдите в аккаунт")  # Если токен отсутствует, показываем сообщение для авторизации

def users_page():
    st.title("Пользователи")

    token = controller.get('jwt_token')
    if token:
        if check_authorization(token):
            users = get_all_users(token)
            subscriptions = get_user_subscriptions(token)
            subscribed_user_ids = set(sub['user_id2'] for sub in subscriptions)
            if users:
                # Add a checkbox to filter subscriptions
                show_subscriptions = st.checkbox("Мои подписки")

                if show_subscriptions:
                    # Filter users to show only those you are subscribed to
                    subscribed_users = [user for user in users if user['id'] in subscribed_user_ids]
                    if subscribed_users:
                        for user in subscribed_users:
                            user_id = user['id']
                            st.write(f"**Имя:** {user['name']} 🎮")
                            st.write(f"**Текущие трофеи:** {user['crowns']} 🏆")
                            st.write(f"**Максимальное количество трофеев:** {user['max_crowns']} 🏆")
                            key = f"button_{user_id}"
                            # Since we're showing subscribed users, show "Отписаться" button
                            if st.button("Отписаться", key=key, help="Отписаться от этого пользователя"):
                                unsubscribe_user(token, user_id)
                                st.toast(f"Отписались от {user['name']}", icon='✅')
                            st.write("---")
                    else:
                        st.write("Нет подписок.")
                else:
                    # Show all users
                    for user in users:
                        user_id = user['id']
                        st.write(f"**Имя:** {user['name']} 🎮")
                        st.write(f"**Текущие трофеи:** {user['crowns']} 🏆")
                        st.write(f"**Максимальное количество трофеев:** {user['max_crowns']} 🏆")
                        key = f"button_{user_id}"
                        if user_id in subscribed_user_ids:
                            if st.button("Отписаться", key=key, help="Отписаться от этого пользователя"):
                                unsubscribe_user(token, user_id)
                                st.toast(f"Отписались от {user['name']}", icon='✅')
                        else:
                            if st.button("Подписаться", key=key, help="Подписаться на этого пользователя"):
                                subscribe_user(token, user_id)
                                st.toast(f"Подписались на {user['name']}", icon='✅')
                        st.write("---")
            else:
                st.write("Нет доступных пользователей.")
        else:
            st.write("Невалидный токен. Пожалуйста, войдите снова.")
    else:
        st.write("Войдите в аккаунт для просмотра пользователей.")

# Основной поток приложения
def main():
    if "registration_success" not in st.session_state:
        st.session_state.registration_success = False

    if "token" not in st.session_state:
        st.session_state.token = None

    pages = {
        "Главная": home_page,
        "Регистрация": registration_page,
        "Логин": login_page,
        "Пользователи": users_page,
    }

    # Панель навигации
    page = st.sidebar.radio("Выберите страницу", options=["Главная", "Регистрация", "Логин", "Пользователи"])

    # Открываем соответствующую страницу
    pages[page]()

if __name__ == "__main__":
    main()
