import streamlit as st
import os
import sys
import json
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from uploaders.youtube import YouTubeUploader
    from uploaders.tiktok import TikTokUploader
    from uploaders.instagram import InstagramUploader
    from utils.VideoProcessor import VideoProcessor
    from utils.config import Config
    from queue_manager import add_to_queue, show_queue_tab, load_queue, remove_from_queue, publish_from_queue
    from stories_manager import show_stories_tab, add_to_stories, load_stories, remove_from_stories, publish_story
    from default_settings import show_default_settings_tab, get_default_video_settings, get_default_stream_settings
    from ai_assistant import show_ai_config, get_ai_config, is_ai_configured, process_video_with_ai, \
        generate_content_from_transcript
except ImportError as e:
    st.error(f"Ошибка импорта модулей: {e}")
    st.error("Убедитесь что все файлы находятся в правильных папках")
    st.stop()

st.set_page_config(
    page_title="Video Uploader",
    page_icon="🎥",
    layout="wide"
)

CONFIG_FILE = "config/platforms_config.json"


def load_platforms_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Ошибка загрузки конфигурации: {e}")

    return {
        'youtube': {'enabled': False, 'client_id': '', 'client_secret': '', 'authenticated': False},
        'tiktok': {'enabled': False, 'username': '', 'password': '', 'authenticated': False},
        'instagram': {'enabled': False, 'username': '', 'password': '', 'authenticated': False}
    }


def save_platforms_config(config):
    try:
        os.makedirs('config', exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Ошибка сохранения конфигурации: {e}")


def test_youtube_connection(client_id, client_secret):
    try:
        uploader = YouTubeUploader()
        result = uploader.authenticate(client_id, client_secret)
        if result:
            st.success("YouTube API успешно подключен!")
            return True
        else:
            st.error("Не удалось подключиться к YouTube API")
            return False
    except Exception as e:
        st.error(f"Ошибка подключения к YouTube: {str(e)}")
        return False


def test_tiktok_connection(username, password):
    try:
        st.info("🤖 Запускаем браузер для TikTok...")
        st.info("💡 **Если увидите QR код - отсканируйте его телефоном!**")
        st.info("📱 Или используйте любой другой способ входа в браузере")

        uploader = TikTokUploader()
        result = uploader.login(username, password)

        if result:
            st.success("✅ TikTok аккаунт успешно подключен!")
            st.info("🎉 Теперь можно загружать видео на TikTok!")
            uploader.close()
            return True
        else:
            st.error("❌ Не удалось войти в TikTok")
            st.info("💡 **Что можно попробовать:**")
            st.markdown("""
            - Войти через QR код (отсканировать телефоном)
            - Решить капчу если появилась
            - Пройти SMS верификацию
            - Попробовать другой аккаунт
            """)
            uploader.close()
            return False
    except Exception as e:
        st.error(f"Ошибка подключения к TikTok: {str(e)}")
        st.info("🔧 **Возможные решения:**")
        st.markdown("""
        - Перезапустить приложение
        - Обновить Chrome браузер
        - Проверить интернет соединение
        - Создать новый TikTok аккаунт
        """)
        return False


def test_instagram_connection(username, password):
    try:
        uploader = InstagramUploader()
        result = uploader.login(username, password)
        if result:
            st.success("Instagram аккаунт успешно подключен!")
            return True
        else:
            st.error("Не удалось войти в Instagram аккаунт")
            return False
    except Exception as e:
        st.error(f"Ошибка подключения к Instagram: {str(e)}")
        return False


def show_youtube_config():
    config = st.session_state.platforms_config

    st.markdown("### 🔗 Настройка YouTube API")

    with st.expander("📋 Инструкция по настройке", expanded=False):
        st.markdown("""
        1. Перейдите в [Google Cloud Console](https://console.cloud.google.com)
        2. Создайте проект или выберите существующий
        3. Включите YouTube Data API v3
        4. Создайте OAuth 2.0 credentials
        5. Скопируйте Client ID и Client Secret
        """)

    client_id = st.text_input("Client ID",
                              value=config['youtube']['client_id'],
                              type="password",
                              key="yt_client_id")
    client_secret = st.text_input("Client Secret",
                                  value=config['youtube']['client_secret'],
                                  type="password",
                                  key="yt_client_secret")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔍 Проверить подключение", key="test_yt"):
            if client_id and client_secret:
                with st.spinner("Проверяем подключение..."):
                    if test_youtube_connection(client_id, client_secret):
                        config['youtube']['client_id'] = client_id
                        config['youtube']['client_secret'] = client_secret
                        config['youtube']['authenticated'] = True
                        config['youtube']['enabled'] = True
                        save_platforms_config(config)
                        st.success("✅ YouTube подключен успешно!")
                        st.session_state.show_youtube_config = False
                        st.rerun()
                    else:
                        st.error("❌ Ошибка подключения к YouTube")
            else:
                st.error("Заполните все поля")

    with col2:
        if st.button("💾 Сохранить", key="save_yt"):
            config['youtube']['client_id'] = client_id
            config['youtube']['client_secret'] = client_secret
            save_platforms_config(config)
            st.success("Настройки сохранены")

    with col3:
        if st.button("❌ Закрыть", key="close_yt"):
            st.session_state.show_youtube_config = False
            st.rerun()


def show_tiktok_config():
    config = st.session_state.platforms_config

    st.markdown("### 🎵 Настройка TikTok")
    st.warning("⚠️ Рекомендуется использовать отдельный аккаунт для автоматизации")

    username = st.text_input("Username/Email",
                             value=config['tiktok']['username'],
                             key="tt_username")
    password = st.text_input("Password",
                             value=config['tiktok']['password'],
                             type="password",
                             key="tt_password")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔍 Проверить подключение", key="test_tt"):
            if username and password:
                with st.spinner("Проверяем подключение... (может занять время)"):
                    if test_tiktok_connection(username, password):
                        config['tiktok']['username'] = username
                        config['tiktok']['password'] = password
                        config['tiktok']['authenticated'] = True
                        config['tiktok']['enabled'] = True
                        save_platforms_config(config)
                        st.success("✅ TikTok подключен успешно!")
                        st.session_state.show_tiktok_config = False
                        st.rerun()
                    else:
                        st.error("❌ Ошибка подключения к TikTok")
            else:
                st.error("Заполните все поля")

    with col2:
        if st.button("💾 Сохранить", key="save_tt"):
            config['tiktok']['username'] = username
            config['tiktok']['password'] = password
            save_platforms_config(config)
            st.success("Настройки сохранены")

    with col3:
        if st.button("❌ Закрыть", key="close_tt"):
            st.session_state.show_tiktok_config = False
            st.rerun()


def show_instagram_config():
    config = st.session_state.platforms_config

    st.markdown("### 📷 Настройка Instagram")
    st.warning("⚠️ Рекомендуется использовать отдельный аккаунт для автоматизации")

    username = st.text_input("Username",
                             value=config['instagram']['username'],
                             key="ig_username")
    password = st.text_input("Password",
                             value=config['instagram']['password'],
                             type="password",
                             key="ig_password")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔍 Проверить подключение", key="test_ig"):
            if username and password:
                with st.spinner("Проверяем подключение..."):
                    if test_instagram_connection(username, password):
                        config['instagram']['username'] = username
                        config['instagram']['password'] = password
                        config['instagram']['authenticated'] = True
                        config['instagram']['enabled'] = True
                        save_platforms_config(config)
                        st.success("✅ Instagram подключен успешно!")
                        st.session_state.show_instagram_config = False
                        st.rerun()
                    else:
                        st.error("❌ Ошибка подключения к Instagram")
            else:
                st.error("Заполните все поля")

    with col2:
        if st.button("💾 Сохранить", key="save_ig"):
            config['instagram']['username'] = username
            config['instagram']['password'] = password
            save_platforms_config(config)
            st.success("Настройки сохранены")

    with col3:
        if st.button("❌ Закрыть", key="close_ig"):
            st.session_state.show_instagram_config = False
            st.rerun()


def show_upload_tab():
    config = st.session_state.platforms_config

    with st.sidebar:
        st.header("⚙️ Настройки платформ")

        st.subheader("YouTube")
        col1, col2 = st.columns([3, 1])
        with col1:
            if config['youtube']['authenticated']:
                st.success("✅ Подключено")
            else:
                st.error("❌ Не подключено")
        with col2:
            if st.button("⚙️", key="yt_config"):
                st.session_state.show_youtube_config = True
                st.rerun()

        youtube_enabled = st.checkbox("Включить YouTube",
                                      value=False,
                                      disabled=not config['youtube']['authenticated'])

        st.subheader("TikTok")
        col1, col2 = st.columns([3, 1])
        with col1:
            if config['tiktok']['authenticated']:
                st.success("✅ Подключено")
            else:
                st.error("❌ Не подключено")
        with col2:
            if st.button("⚙️", key="tt_config"):
                st.session_state.show_tiktok_config = True
                st.rerun()

        tiktok_enabled = st.checkbox("Включить TikTok",
                                     value=False,
                                     disabled=not config['tiktok']['authenticated'])

        st.subheader("Instagram")
        col1, col2 = st.columns([3, 1])
        with col1:
            if config['instagram']['authenticated']:
                st.success("✅ Подключено")
            else:
                st.error("❌ Не подключено")
        with col2:
            if st.button("⚙️", key="ig_config"):
                st.session_state.show_instagram_config = True
                st.rerun()

        instagram_enabled = st.checkbox("Включить Instagram",
                                        value=False,
                                        disabled=not config['instagram']['authenticated'])

        st.subheader("ChatGPT")
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.session_state.ai_config.get('authenticated', False):
                st.success("✅ Подключено")
            else:
                st.error("❌ Не подключено")
        with col2:
            if st.button("⚙️", key="openai_config"):
                st.session_state.show_openai_config = True
                st.rerun()

        config['youtube']['enabled'] = youtube_enabled
        config['tiktok']['enabled'] = tiktok_enabled
        config['instagram']['enabled'] = instagram_enabled
        save_platforms_config(config)

        st.divider()

        st.subheader("🔧 Управление браузерами")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Перезапустить TikTok браузер", help="Закрывает и создает новый браузер TikTok"):
                try:
                    TikTokUploader.close_browser()
                    st.success("Браузер TikTok перезапущен!")
                except Exception as e:
                    st.error(f"Ошибка: {e}")

        with col2:
            if st.button("❌ Закрыть все браузеры", help="Закрывает все открытые браузеры"):
                try:
                    TikTokUploader.close_browser()
                    st.success("Все браузеры закрыты!")
                except Exception as e:
                    st.error(f"Ошибка: {e}")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("📁 Загрузка видео")

        uploaded_file = st.file_uploader(
            "Выберите видео файл",
            type=['mp4', 'mov', 'avi', 'mkv'],
            help="Поддерживаемые форматы: MP4, MOV, AVI, MKV"
        )

        if uploaded_file:
            col_video1, col_video2, col_video3 = st.columns([1, 1, 2])
            with col_video1:
                st.video(uploaded_file, start_time=0)

            # Кнопка транскрипции
            if st.button("🎵 Создать транскрипцию", help="Извлечь текст из аудиодорожки видео"):
                if is_ai_configured():
                    temp_video_path = f"temp/temp_analysis_{int(time.time())}.mp4"
                    os.makedirs('temp', exist_ok=True)

                    with open(temp_video_path, "wb") as f:
                        f.write(uploaded_file.getvalue())

                    try:
                        with st.spinner("Создаем транскрипцию..."):
                            transcript, _, _ = process_video_with_ai(temp_video_path)
                            if transcript:
                                st.session_state.video_transcript = transcript
                                st.success("✅ Транскрипция готова!")
                                with st.expander("📝 Просмотр транскрипции", expanded=False):
                                    st.text_area("Транскрипция:", value=transcript, height=100, disabled=True)
                    finally:
                        if os.path.exists(temp_video_path):
                            os.remove(temp_video_path)
                else:
                    st.warning("🤖 ChatGPT не подключен. Настройте в боковой панели для AI функций.")

            st.subheader("📝 Метаданные")

            default_settings = get_default_video_settings()

            col_meta1, col_meta2 = st.columns(2)

            with col_meta1:
                # НАЗВАНИЕ ВИДЕО
                st.write("**Название видео:**")
                col_title1, col_title2 = st.columns([4, 1])

                with col_title1:
                    title = st.text_input("Название видео",
                                          value="",
                                          max_chars=100,
                                          label_visibility="collapsed",
                                          key="title_input")

                with col_title2:
                    # Временно уберем проверку is_ai_configured() для отладки
                    # st.write(f"AI configured: {is_ai_configured()}")  # Отладка
                    # st.write(f"AI config: {st.session_state.ai_config}")  # Отладка

                    # Показываем кнопку всегда, но делаем неактивной если AI не настроен
                    ai_configured = is_ai_configured()
                    if st.button("🤖", key="generate_title_btn",
                                 help="Сгенерировать название" if ai_configured else "Настройте ChatGPT в боковой панели",
                                 disabled=not ai_configured):
                        if st.session_state.get('video_transcript'):
                            with st.spinner("Генерируем название..."):
                                title_ai, _ = generate_content_from_transcript(
                                    st.session_state.video_transcript, "title"
                                )
                                if title_ai:
                                    st.session_state.generated_title = title_ai
                                    st.rerun()
                        else:
                            st.error("❌ Сначала создайте транскрипцию видео!")

                # Показываем предложенное название, если есть
                if st.session_state.get('generated_title'):
                    st.success("✅ Предложенное название:")
                    st.info(st.session_state.generated_title)

                    col_confirm1, col_confirm2 = st.columns(2)
                    with col_confirm1:
                        if st.button("✅ Принять", key="accept_title"):
                            # Очищаем сгенерированное и обновляем поле
                            st.session_state.generated_title = ""
                            st.rerun()
                    with col_confirm2:
                        if st.button("❌ Отмена", key="decline_title"):
                            st.session_state.generated_title = ""
                            st.rerun()

                # ОПИСАНИЕ
                st.write("**Описание:**")
                col_desc1, col_desc2 = st.columns([4, 1])

                with col_desc1:
                    description = st.text_area("Описание",
                                               value=default_settings['description'],
                                               max_chars=2000,
                                               height=100,
                                               label_visibility="collapsed",
                                               key="description_input")

                with col_desc2:
                    # Показываем кнопку всегда, но делаем неактивной если AI не настроен
                    ai_configured = is_ai_configured()
                    if st.button("🤖", key="generate_desc_btn",
                                 help="Сгенерировать описание" if ai_configured else "Настройте ChatGPT в боковой панели",
                                 disabled=not ai_configured):
                        if st.session_state.get('video_transcript'):
                            with st.spinner("Генерируем описание..."):
                                _, desc_ai = generate_content_from_transcript(
                                    st.session_state.video_transcript, "description"
                                )
                                if desc_ai:
                                    st.session_state.generated_description = desc_ai
                                    st.rerun()
                        else:
                            st.error("❌ Сначала создайте транскрипцию видео!")

                # Показываем предложенное описание, если есть
                if st.session_state.get('generated_description'):
                    st.success("✅ Предложенное описание:")
                    st.info(st.session_state.generated_description)

                    col_confirm1, col_confirm2 = st.columns(2)
                    with col_confirm1:
                        if st.button("✅ Принять", key="accept_desc"):
                            # Добавляем к текущему описанию
                            current_desc = st.session_state.get('description_input', default_settings['description'])
                            new_description = f"{current_desc}\n\n{st.session_state.generated_description}"
                            st.session_state.description_input = new_description
                            st.session_state.generated_description = ""
                            st.rerun()
                    with col_confirm2:
                        if st.button("❌ Отмена", key="decline_desc"):
                            st.session_state.generated_description = ""
                            st.rerun()

                tags = st.text_input("Теги (через запятую)",
                                     value=default_settings['tags'])

            with col_meta2:
                category = st.selectbox("Категория", [
                    "Entertainment", "Gaming", "Comedy", "Music",
                    "Sports", "Education", "Technology", "Lifestyle"
                ], index=["Entertainment", "Gaming", "Comedy", "Music",
                          "Sports", "Education", "Technology", "Lifestyle"].index(default_settings['category']))

                privacy = st.selectbox("Приватность", [
                    "public", "unlisted", "private"
                ], index=["public", "unlisted", "private"].index(default_settings['privacy']))

                made_for_kids = st.selectbox("Контент для детей", [
                    "Нет, это видео не для детей",
                    "Да, это видео для детей"
                ], index=["Нет, это видео не для детей", "Да, это видео для детей"].index(
                    default_settings['made_for_kids']))

                thumbnail = st.file_uploader(
                    "Превью (опционально)",
                    type=['jpg', 'jpeg', 'png']
                )

            platforms = []
            if config['youtube']['enabled'] and config['youtube']['authenticated']:
                platforms.append("YouTube")
            if config['tiktok']['enabled'] and config['tiktok']['authenticated']:
                platforms.append("TikTok")
            if config['instagram']['enabled'] and config['instagram']['authenticated']:
                platforms.append("Instagram")

            if platforms:
                selected_platforms = st.multiselect(
                    "Выберите платформы для загрузки:",
                    platforms,
                    default=platforms
                )

                col_btn1, col_btn2 = st.columns(2)

                with col_btn1:
                    if st.button("🚀 Начать загрузку", type="primary"):
                        # Используем значения из полей, а не из session_state
                        final_title = title if st.session_state.get('generated_title') == "" else title
                        final_description = description

                        if final_title and selected_platforms:
                            try:
                                upload_video(
                                    uploaded_file, final_title, final_description, tags,
                                    category, privacy, thumbnail, selected_platforms, made_for_kids
                                )
                            except Exception as e:
                                st.error(f"Ошибка при загрузке: {str(e)}")
                        else:
                            st.error("Заполните название и выберите платформы")

                with col_btn2:
                    if st.button("📋 Добавить в очередь", type="secondary"):
                        # Используем значения из полей
                        final_title = title
                        final_description = description

                        if final_title and selected_platforms:
                            try:
                                queue_id = add_to_queue(
                                    uploaded_file, final_title, final_description, tags,
                                    category, privacy, thumbnail, selected_platforms, made_for_kids
                                )
                                st.success(f"✅ Добавлено в очередь! ID: {queue_id[:8]}")
                                st.info("📋 Откройте менеджер очереди для управления")
                            except Exception as e:
                                st.error(f"Ошибка добавления в очередь: {str(e)}")
                        else:
                            st.error("Заполните название и выберите платформы")
            else:
                st.warning("Настройте и подключите хотя бы одну платформу")

    with col2:
        st.header("📊 Статус загрузок")

        if st.session_state.upload_status:
            for video_id, status_data in st.session_state.upload_status.items():
                with st.expander(f"📹 {status_data['title']}", expanded=True):
                    st.write(f"**Время:** {status_data['timestamp']}")

                    for platform, status in status_data['platforms'].items():
                        if status == "uploading":
                            st.info(f"🔄 {platform}: Загружается...")
                        elif status == "success":
                            st.success(f"✅ {platform}: Загружено")
                        elif status == "error":
                            st.error(f"❌ {platform}: Ошибка")
                        else:
                            st.warning(f"⏳ {platform}: Ожидание")
        else:
            st.info("Загрузок пока нет")


def upload_video(file, title, description, tags, category, privacy, thumbnail, platforms, made_for_kids):
    video_id = f"video_{int(time.time())}"
    config = st.session_state.platforms_config

    st.session_state.upload_status[video_id] = {
        'title': title,
        'timestamp': datetime.now().strftime("%H:%M:%S"),
        'platforms': {platform: "pending" for platform in platforms}
    }

    os.makedirs('temp', exist_ok=True)
    temp_path = f"temp/temp_{video_id}.mp4"
    with open(temp_path, "wb") as f:
        f.write(file.getvalue())

    st.info("Начинаем загрузку видео...")

    processor = VideoProcessor()

    is_for_kids = made_for_kids.startswith("Да")

    for platform in platforms:
        st.session_state.upload_status[video_id]['platforms'][platform] = "uploading"

        with st.spinner(f"Загружаем на {platform}..."):
            try:
                if platform == "YouTube":
                    uploader = YouTubeUploader()
                    uploader.authenticate(
                        config['youtube']['client_id'],
                        config['youtube']['client_secret']
                    )
                    result = uploader.upload(temp_path, title, description, tags, category, privacy, is_for_kids)

                elif platform == "TikTok":
                    processed_video = processor.prepare_for_tiktok(temp_path)
                    uploader = TikTokUploader()

                    if not uploader._check_logged_in():
                        st.warning("⚠️ Сессия TikTok истекла, выполняется повторный вход...")
                        login_success = uploader.login(config['tiktok']['username'], config['tiktok']['password'])
                        if not login_success:
                            raise Exception("Не удалось войти в TikTok повторно")

                    tiktok_caption = f"{title}\n\n{description}"
                    tiktok_hashtags = f"#{tags.replace(', ', ' #').replace(',', ' #')}"

                    st.info("🎯 Подготавливаем TikTok к загрузке...")
                    st.warning("⚠️ После заполнения полей вам нужно будет ВРУЧНУЮ нажать кнопку 'Post' в браузере!")

                    result = uploader.prepare_for_upload(processed_video, tiktok_caption, tiktok_hashtags)

                    if result:
                        st.success("✅ TikTok: Все поля заполнены! Теперь нажмите кнопку 'Post' в браузере.")
                        st.info("👆 Кнопка публикации подсвечена красным в браузере")
                    else:
                        st.error("❌ TikTok: Ошибка подготовки к загрузке")

                elif platform == "Instagram":
                    processed_video = processor.prepare_for_instagram(temp_path)
                    uploader = InstagramUploader()
                    uploader.login(config['instagram']['username'], config['instagram']['password'])

                    instagram_caption = f"{title}\n\n{description}"
                    instagram_tags = f"#{tags.replace(', ', ' #').replace(',', ' #')}"

                    result = uploader.upload(processed_video, instagram_caption, instagram_tags)

                if result:
                    st.session_state.upload_status[video_id]['platforms'][platform] = "success"
                    st.success(f"✅ {platform}: Загружено успешно!")
                else:
                    st.session_state.upload_status[video_id]['platforms'][platform] = "error"
                    st.error(f"❌ {platform}: Ошибка загрузки")

            except Exception as e:
                st.session_state.upload_status[video_id]['platforms'][platform] = "error"
                st.error(f"❌ Ошибка загрузки на {platform}: {str(e)}")

            time.sleep(1)

    try:
        os.remove(temp_path)
    except:
        pass

    st.success("🎉 Загрузка завершена! Проверьте результаты справа.")


def init_session_state():
    if 'upload_status' not in st.session_state:
        st.session_state.upload_status = {}
    if 'config' not in st.session_state:
        st.session_state.config = Config()
    if 'platforms_config' not in st.session_state:
        st.session_state.platforms_config = load_platforms_config()
    if 'ai_config' not in st.session_state:
        st.session_state.ai_config = get_ai_config()
    if 'show_youtube_config' not in st.session_state:
        st.session_state.show_youtube_config = False
    if 'show_tiktok_config' not in st.session_state:
        st.session_state.show_tiktok_config = False
    if 'show_instagram_config' not in st.session_state:
        st.session_state.show_instagram_config = False
    if 'show_openai_config' not in st.session_state:
        st.session_state.show_openai_config = False
    if 'current_tab' not in st.session_state:
        st.session_state.current_tab = "upload"
    if 'editing_item' not in st.session_state:
        st.session_state.editing_item = None
    if 'video_transcript' not in st.session_state:
        st.session_state.video_transcript = None
    if 'generated_title' not in st.session_state:
        st.session_state.generated_title = ""
    if 'generated_description' not in st.session_state:
        st.session_state.generated_description = ""


def main():
    init_session_state()

    st.title("🎥 Multi-Platform Video Uploader")
    st.markdown("Автоматическая загрузка видео на YouTube, TikTok и Instagram")

    config = st.session_state.platforms_config

    if st.session_state.show_youtube_config:
        show_youtube_config()
        return

    if st.session_state.show_tiktok_config:
        show_tiktok_config()
        return

    if st.session_state.show_instagram_config:
        show_instagram_config()
        return

    if st.session_state.show_openai_config:
        show_ai_config()
        return

    tab1, tab2, tab3, tab4 = st.tabs(["📤 Загрузка", "📋 Очередь", "📺 Stream Notification", "⚙️ Default Settings"])

    with tab1:
        show_upload_tab()

    with tab2:
        show_queue_tab()

    with tab3:
        show_stories_tab()

    with tab4:
        show_default_settings_tab()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Закрытие приложения...")
        TikTokUploader.close_browser()
    except Exception as e:
        print(f"Ошибка приложения: {e}")
        TikTokUploader.close_browser()