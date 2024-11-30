import streamlit as st
import requests

# URL вашего API
API_URL_REGISTER = "http://localhost:8000/api/v1/user/register"
API_URL_TOKEN = "http://localhost:8000/api/v1/user/token"
API_URL_LOGIN = "http://localhost:8000/api/v1/user/login"  # Новый URL для проверки авторизации

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
                st.success(f"Авторизация прошла успешно! Ваш токен: {token}")
                # Сохраняем токен в сессии для использования в других запросах
                st.session_state.token = token
            else:
                st.error("Ошибка авторизации!")
        else:
            st.error("Пожалуйста, заполните все поля.")

# Главная страница
def home_page():
    if "token" in st.session_state and st.session_state.token:
        token = st.session_state.token
        if check_authorization(token):
            st.title("Главная страница")
            st.write("Вы в аккаунте!")  # Показываем, что пользователь авторизован
        else:
            st.title("Главная страница")
            st.write("Невалидный токен. Пожалуйста, войдите снова.")
    else:
        st.title("Главная страница")
        st.write("Войдите в аккаунт")  # Если токен отсутствует, показываем сообщение для авторизации

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
    }

    # Панель навигации
    page = st.sidebar.radio("Выберите страницу", options=["Главная", "Регистрация", "Логин"])

    # Открываем соответствующую страницу
    pages[page]()

if __name__ == "__main__":
    main()
