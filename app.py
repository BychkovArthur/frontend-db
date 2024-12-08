import streamlit as st
import requests
from datetime import datetime, timedelta
from streamlit_cookies_controller import CookieController
import pandas as pd

API_URL_REGISTER = "http://localhost:8000/api/v1/user/register"
API_URL_TOKEN = "http://localhost:8000/api/v1/user/token"
API_URL_LOGIN = "http://localhost:8000/api/v1/user/login"
API_URL_USERS = "http://localhost:8000/api/v1/user/get_all_except_self"
API_URL_BATTLE_RECORDS = "http://localhost:8000/api/v1/battle_records/"
API_URL_AGGR_BATTLE_RECORDS = "http://localhost:8000/api/v1/battle_records/aggregated"
API_URL_LIST_DUMPS = "http://localhost:8000/api/v1/admin/dumps"
API_URL_CREATE_DUMP = "http://localhost:8000/api/v1/admin/dump"
API_URL_RESTORE_DUMP = "http://localhost:8000/api/v1/admin/restore"


controller = CookieController()


def register_user(email: str, password: str, tag: str):
    user_data = {"email": email, "password": password, "tag": tag}
    response = requests.post(API_URL_REGISTER, json=user_data)
    return response


def get_token(username: str, password: str):
    response = requests.post(
        API_URL_TOKEN, data={"username": username, "password": password}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        st.error("Неверные данные для авторизации!")
        return None


def check_authorization(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(API_URL_LOGIN, headers=headers)
    if response.status_code == 200:
        user_data = response.json()
        return user_data
    else:
        st.error("Ошибка при проверке авторизации!")
        return None


def get_all_users(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    with st.spinner("Загрузка пользователей..."):
        response = requests.get(API_URL_USERS, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Ошибка при получении пользователей!")
            return []


def get_user_subscriptions(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        "http://localhost:8000/api/v1/subscriptions/", headers=headers
    )
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Ошибка при получении подписок.")
        return []


def subscribe_user(token, other_user_id):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"http://localhost:8000/api/v1/subscriptions/subscribe/{other_user_id}",
        headers=headers,
    )
    if response.status_code != 201:
        st.error(
            f"Ошибка при подписке: {response.json().get('detail', 'Неизвестная ошибка')}"
        )
    st.rerun()


def unsubscribe_user(token, other_user_id):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"http://localhost:8000/api/v1/subscriptions/unsubscribe/{other_user_id}",
        headers=headers,
    )
    if response.status_code != 200:
        st.error(
            f"Ошибка при отписке: {response.json().get('detail', 'Неизвестная ошибка')}"
        )
    st.rerun()


def registration_page():
    st.title("Регистрация")

    email = st.text_input("Email")
    password = st.text_input("Пароль", type="password")
    tag = st.text_input("Тег")

    if st.button("Зарегистрироваться"):
        if email and password and tag:
            response = register_user(email, password, tag)
            if response.status_code == 201:
                st.success(
                    "Пользователь успешно зарегистрирован! Перейдите на страницу входа."
                )
                st.session_state.registration_success = True
            else:
                st.error(
                    f"Ошибка: {response.json().get('detail', 'Неизвестная ошибка')}"
                )
        else:
            st.error("Пожалуйста, заполните все поля.")


def login_page():
    st.title("Вход")

    username = st.text_input("Email")
    password = st.text_input("Пароль", type="password")

    if st.button("Войти"):
        if username and password:
            token = get_token(username, password)
            if token:
                st.success(f"Авторизация прошла успешно!")

                controller.set("jwt_token", token)

                st.session_state.token = token
            else:
                st.error("Ошибка авторизации!")
        else:
            st.error("Пожалуйста, заполните все поля.")


def logout():
    controller.remove("jwt_token")
    st.session_state.token = None
    st.success("Вы успешно вышли из аккаунта!")
    st.rerun()


def home_page():
    token = controller.get("jwt_token")

    if token:
        user_data = check_authorization(token)
        if user_data:
            st.title("Главная страница")
            st.write(f"Вы в аккаунте, {user_data['name']}! 😄")
            st.write(f"**Тег:** {user_data['tag']} 🏆")

            if st.button("Выход"):
                logout()
        else:
            st.title("Главная страница")
            st.write("Невалидный токен. Пожалуйста, войдите снова.")
    else:
        st.title("Главная страница")
        st.write("Войдите в аккаунт для просмотра содержимого.")


def users_page():
    st.title("Пользователи")

    token = controller.get("jwt_token")
    if token:
        if check_authorization(token):
            users = get_all_users(token)
            subscriptions = get_user_subscriptions(token)
            subscribed_user_ids = set(sub["user_id2"] for sub in subscriptions)
            if users:
                show_subscriptions = st.checkbox("Мои подписки")

                if show_subscriptions:
                    subscribed_users = [
                        user for user in users if user["id"] in subscribed_user_ids
                    ]
                    if subscribed_users:
                        for user in subscribed_users:
                            user_id = user["id"]
                            st.write(f"**Имя:** {user['name']} 🎮")
                            st.write(f"**Текущие трофеи:** {user['crowns']} 🏆")
                            st.write(
                                f"**Максимальное количество трофеев:** {user['max_crowns']} 🏆"
                            )
                            key = f"button_{user_id}"

                            if st.button(
                                "Отписаться",
                                key=key,
                                help="Отписаться от этого пользователя",
                            ):
                                unsubscribe_user(token, user_id)
                                st.toast(f"Отписались от {user['name']}", icon="✅")
                            st.write("---")
                    else:
                        st.write("Нет подписок.")
                else:
                    for user in users:
                        user_id = user["id"]
                        st.write(f"**Имя:** {user['name']} 🎮")
                        st.write(f"**Текущие трофеи:** {user['crowns']} 🏆")
                        st.write(
                            f"**Максимальное количество трофеев:** {user['max_crowns']} 🏆"
                        )
                        key = f"button_{user_id}"
                        if user_id in subscribed_user_ids:
                            if st.button(
                                "Отписаться",
                                key=key,
                                help="Отписаться от этого пользователя",
                            ):
                                unsubscribe_user(token, user_id)
                                st.toast(f"Отписались от {user['name']}", icon="✅")
                        else:
                            if st.button(
                                "Подписаться",
                                key=key,
                                help="Подписаться на этого пользователя",
                            ):
                                subscribe_user(token, user_id)
                                st.toast(f"Подписались на {user['name']}", icon="✅")
                        st.write("---")
            else:
                st.write("Нет доступных пользователей.")
        else:
            st.write("Невалидный токен. Пожалуйста, войдите снова.")
    else:
        st.write("Войдите в аккаунт для просмотра пользователей.")


def battle_records_page():
    st.title("Мои поединки")

    token = controller.get("jwt_token")
    if token:
        if check_authorization(token):
            try:
                headers = {"Authorization": f"Bearer {token}"}
                response = requests.get(API_URL_BATTLE_RECORDS, headers=headers)
                if response.status_code == 200:
                    battle_records = response.json()
                    if battle_records:
                        for record in battle_records:
                            st.write(f"**Соперник:** {record['name2']} 🎮")
                            st.write(
                                f"**Твой счет:** {record['user1_score']} | **Счет соперника:** {record['user2_score']} 🎮"
                            )
                            st.write(
                                f"**Твои короны:** {record['user1_get_crowns']} | **Короны соперника:** {record['user2_get_crowns']} 🏆"
                            )
                            if record["is_user1_win"]:
                                st.write(f"**Результат:** Победа! 😄")
                            else:
                                st.write(f"**Результат:** Поражение 😢")
                            st.write("---")
                    else:
                        st.write("У вас пока нет поединков.")
                else:
                    st.error("Ошибка при получении поединков.")
            except Exception as e:
                st.error(f"Произошла ошибка: {e}")
        else:
            st.write("Невалидный токен. Пожалуйста, войдите снова.")
    else:
        st.write("Войдите в аккаунт для просмотра поединков.")


def battle_statistics_page():
    st.title("Статистика моих боев")

    token = controller.get("jwt_token")
    if token:
        user_data = check_authorization(token)
        if user_data:
            with st.spinner("Загрузка статистики боев..."):
                headers = {"Authorization": f"Bearer {token}"}
                response = requests.get(API_URL_AGGR_BATTLE_RECORDS, headers=headers)
                if response.status_code == 200:
                    aggr_battle_records = response.json()
                    if aggr_battle_records:
                        df = pd.DataFrame(aggr_battle_records)

                        total_wins = df["score1"].sum()
                        total_losses = df["score2"].sum()
                        total_battles = total_wins + total_losses
                        win_percentage = (
                            (total_wins / total_battles) * 100
                            if total_battles > 0
                            else 0
                        )

                        st.write(f"**Всего боев:** {total_battles}")
                        st.write(f"**Побед:** {total_wins} ({win_percentage:.2f}%)")
                        st.write(
                            f"**Поражений:** {total_losses} ({100 - win_percentage:.2f}%)"
                        )

                        st.subheader("Подробная статистика по соперникам")
                        st.dataframe(df[["name1", "name2", "score1", "score2"]])

                        st.subheader("График побед и поражений")
                        win_loss_df = pd.DataFrame(
                            {
                                "Результат": ["Победы", "Поражения"],
                                "Количество": [total_wins, total_losses],
                            }
                        )
                        st.bar_chart(win_loss_df.set_index("Результат"))

                    else:
                        st.write("У вас нет агрегированных данных по боям.")
                else:
                    st.error(
                        f"Ошибка при получении статистики боев: {response.status_code}"
                    )
        else:
            st.write("Невалидный токен. Пожалуйста, войдите снова.")
    else:
        st.write("Войдите в аккаунт для просмотра статистики боев.")


def admin_page():
    st.title("Администратор")

    token = controller.get("jwt_token")
    if token:
        user_data = check_authorization(token)
        if user_data and user_data.get("is_super_user", False):
            st.write("Добро пожаловать, администратор!")

            try:
                response = requests.post(
                    API_URL_LIST_DUMPS, headers={"Authorization": f"Bearer {token}"}
                )
                response.raise_for_status()
                dumps = response.json().get("dumps", [])
            except requests.exceptions.HTTPError as errh:
                st.error(f"HTTP Error: {errh}")
                dumps = []
            except requests.exceptions.ConnectionError as errc:
                st.error(f"Error Connecting: {errc}")
                dumps = []
            except requests.exceptions.Timeout as errt:
                st.error(f"Timeout Error: {errt}")
                dumps = []
            except requests.exceptions.RequestException as err:
                st.error(f"Error: {err}")
                dumps = []

            st.subheader("Список дампов")
            if dumps:
                for dump in dumps:
                    st.write(f"Дамп: {dump}")
                    if st.button(f"Восстановить из {dump}", key=f"restore_{dump}"):
                        with st.spinner(f"Восстановление из {dump}..."):
                            try:
                                restore_response = requests.post(
                                    API_URL_RESTORE_DUMP,
                                    json={"filename": dump},
                                    headers={"Authorization": f"Bearer {token}"},
                                )
                                restore_response.raise_for_status()
                                st.success(
                                    restore_response.json().get(
                                        "message", "База данных восстановлена успешно."
                                    )
                                )
                            except requests.exceptions.HTTPError as errh:
                                st.error(f"HTTP Ошибка: {errh}")
                            except requests.exceptions.RequestException as err:
                                st.error(f"Ошибка: {err}")
            else:
                st.write("Дампы не найдены.")

            st.subheader("Создать новый дамп")
            if st.button("Создать новый дамп"):
                with st.spinner("Создание нового дампа..."):
                    try:
                        create_response = requests.post(
                            API_URL_CREATE_DUMP,
                            headers={"Authorization": f"Bearer {token}"},
                        )
                        create_response.raise_for_status()
                        st.success(
                            create_response.json().get(
                                "message", "Дамп создан успешно."
                            )
                        )
                    except requests.exceptions.HTTPError as errh:
                        st.error(f"HTTP Ошибка: {errh}")
                    except requests.exceptions.RequestException as err:
                        st.error(f"Ошибка: {err}")
        else:
            st.write("У вас нет доступа к этой странице.")
    else:
        st.write("Войдите в аккаунт для просмотра этой страницы.")


def main():
    if "registration_success" not in st.session_state:
        st.session_state.registration_success = False

    if "token" not in st.session_state:
        st.session_state.token = None

    pages = {
        "Профиль": home_page,
        "Регистрация": registration_page,
        "Вход": login_page,
        "Пользователи": users_page,
        "Мои поединки": battle_records_page,
        "Статистика боев": battle_statistics_page,
        "Администратор": admin_page,
    }

    page = st.sidebar.radio(
        "Выберите страницу",
        options=[
            "Регистрация",
            "Вход",
            "Профиль",
            "Пользователи",
            "Мои поединки",
            "Статистика боев",
            "Администратор",
        ],
    )

    pages[page]()


if __name__ == "__main__":
    main()
