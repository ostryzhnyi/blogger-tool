import streamlit as st
import os
import json
import time
from datetime import datetime

SETTINGS_FILE = "config/default_settings.json"


def load_default_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Ошибка загрузки настроек: {e}")

    return {
        'video_upload': {
            'description': 'Новое видео! Подписывайтесь на канал и ставьте лайки!\n\n#контент #видео #подписка',
            'tags': 'видео, контент, развлечение',
            'category': 'Entertainment',
            'privacy': 'public',
            'made_for_kids': 'Нет, это видео не для детей'
        },
        'stream_notification': {
            'story_text': 'Скоро стрим!\nНе пропустите!',
            'hashtags': '#стрим #игры #live',
            'mentions': '',
            'stream_link': '',
            'location': 'Киев',
            'default_time': '20:00'
        },
        'youtube': {
            'default_thumbnail': True,
            'auto_tags': True,
            'notification_subscribers': True
        },
        'tiktok': {
            'auto_hashtags': True,
            'default_caption_prefix': '🔥',
            'add_trending_sounds': False
        },
        'instagram': {
            'auto_location': False,
            'default_story_duration': 15,
            'add_music_sticker': False
        }
    }


def save_default_settings(settings):
    try:
        os.makedirs('config', exist_ok=True)
        settings['last_updated'] = datetime.now().isoformat()
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Ошибка сохранения настроек: {e}")
        return False


def reset_to_defaults():
    default_settings = load_default_settings()
    if save_default_settings(default_settings):
        st.success("✅ Настройки сброшены к значениям по умолчанию")
        return True
    return False


def export_settings():
    settings = load_default_settings()
    settings_json = json.dumps(settings, indent=2, ensure_ascii=False)
    return settings_json


def import_settings(settings_json):
    try:
        settings = json.loads(settings_json)
        if save_default_settings(settings):
            st.success("✅ Настройки импортированы успешно")
            return True
    except json.JSONDecodeError:
        st.error("❌ Неверный формат JSON")
    except Exception as e:
        st.error(f"❌ Ошибка импорта: {e}")
    return False


def show_default_settings_tab():
    st.header("⚙️ Настройки по умолчанию")
    st.markdown("Задайте значения по умолчанию для быстрого заполнения форм")

    settings = load_default_settings()

    # Основные настройки для загрузки видео
    st.subheader("📤 Настройки загрузки видео")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Основные параметры:**")

        default_description = st.text_area(
            "Описание по умолчанию",
            value=settings['video_upload']['description'],
            height=100,
            help="Это описание будет автоматически подставляться при загрузке видео"
        )

        default_tags = st.text_input(
            "Теги по умолчанию",
            value=settings['video_upload']['tags'],
            help="Теги через запятую"
        )

        default_category = st.selectbox(
            "Категория по умолчанию",
            ["Entertainment", "Gaming", "Comedy", "Music", "Sports", "Education", "Technology", "Lifestyle"],
            index=["Entertainment", "Gaming", "Comedy", "Music", "Sports", "Education", "Technology",
                   "Lifestyle"].index(settings['video_upload']['category'])
        )

    with col2:
        st.write("**Настройки публикации:**")

        default_privacy = st.selectbox(
            "Приватность по умолчанию",
            ["public", "unlisted", "private"],
            index=["public", "unlisted", "private"].index(settings['video_upload']['privacy'])
        )

        default_kids = st.selectbox(
            "Контент для детей по умолчанию",
            ["Нет, это видео не для детей", "Да, это видео для детей"],
            index=["Нет, это видео не для детей", "Да, это видео для детей"].index(
                settings['video_upload']['made_for_kids'])
        )

        # Настройки платформ
        st.write("**Настройки платформ:**")

        youtube_defaults = st.checkbox(
            "YouTube: уведомлять подписчиков",
            value=settings['youtube']['notification_subscribers']
        )

        tiktok_auto_hashtags = st.checkbox(
            "TikTok: добавлять автоматические хештеги",
            value=settings['tiktok']['auto_hashtags']
        )

    st.divider()

    # Настройки стрим-уведомлений
    st.subheader("📺 Настройки Stream Notifications")

    col3, col4 = st.columns(2)

    with col3:
        st.write("**Текст и стикеры:**")

        default_story_text = st.text_area(
            "Текст сторис по умолчанию",
            value=settings['stream_notification']['story_text'],
            height=80,
            help="Текст, который будет накладываться на сторис"
        )

        default_hashtags = st.text_input(
            "Хештеги для стримов",
            value=settings['stream_notification']['hashtags'],
            help="Хештеги для уведомлений о стримах"
        )

        default_mentions = st.text_input(
            "Упоминания по умолчанию",
            value=settings['stream_notification']['mentions'],
            help="Пользователи для упоминания в сторис"
        )

    with col4:
        st.write("**Ссылки и локация:**")

        default_stream_link = st.text_input(
            "Ссылка на стрим по умолчанию",
            value=settings['stream_notification']['stream_link'],
            help="Ваша стандартная ссылка на стрим"
        )

        default_location = st.text_input(
            "Геолокация по умолчанию",
            value=settings['stream_notification']['location'],
            help="Ваше местоположение"
        )

        default_time = st.text_input(
            "Время стрима по умолчанию",
            value=settings['stream_notification']['default_time'],
            help="Ваше обычное время начала стрима"
        )

    st.divider()

    # Расширенные настройки платформ
    st.subheader("🔧 Расширенные настройки платформ")

    col5, col6, col7 = st.columns(3)

    with col5:
        st.write("**YouTube:**")
        yt_thumbnail = st.checkbox("Автоматические превью", value=settings['youtube']['default_thumbnail'])
        yt_tags = st.checkbox("Автоматические теги", value=settings['youtube']['auto_tags'])

    with col6:
        st.write("**TikTok:**")
        tt_prefix = st.text_input("Префикс для описания", value=settings['tiktok']['default_caption_prefix'])
        tt_sounds = st.checkbox("Добавлять трендовые звуки", value=settings['tiktok']['add_trending_sounds'])

    with col7:
        st.write("**Instagram:**")
        ig_location = st.checkbox("Автоматическая геолокация", value=settings['instagram']['auto_location'])
        ig_duration = st.number_input("Длительность сторис (сек)", min_value=5, max_value=30,
                                      value=settings['instagram']['default_story_duration'])

    st.divider()

    # Кнопки управления
    st.subheader("💾 Управление настройками")

    col8, col9, col10, col11 = st.columns(4)

    with col8:
        if st.button("💾 Сохранить настройки", type="primary"):
            new_settings = {
                'video_upload': {
                    'description': default_description,
                    'tags': default_tags,
                    'category': default_category,
                    'privacy': default_privacy,
                    'made_for_kids': default_kids
                },
                'stream_notification': {
                    'story_text': default_story_text,
                    'hashtags': default_hashtags,
                    'mentions': default_mentions,
                    'stream_link': default_stream_link,
                    'location': default_location,
                    'default_time': default_time
                },
                'youtube': {
                    'default_thumbnail': yt_thumbnail,
                    'auto_tags': yt_tags,
                    'notification_subscribers': youtube_defaults
                },
                'tiktok': {
                    'auto_hashtags': tiktok_auto_hashtags,
                    'default_caption_prefix': tt_prefix,
                    'add_trending_sounds': tt_sounds
                },
                'instagram': {
                    'auto_location': ig_location,
                    'default_story_duration': ig_duration,
                    'add_music_sticker': False
                }
            }

            if save_default_settings(new_settings):
                st.success("✅ Настройки сохранены!")
                st.balloons()
                time.sleep(1)
                st.rerun()

    with col9:
        if st.button("🔄 Сбросить к умолчанию"):
            if reset_to_defaults():
                time.sleep(1)
                st.rerun()

    with col10:
        if st.button("📤 Экспортировать"):
            settings_json = export_settings()
            st.download_button(
                label="💾 Скачать настройки",
                data=settings_json,
                file_name=f"video_uploader_settings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

    with col11:
        with st.popover("📥 Импортировать"):
            st.write("Вставьте JSON с настройками:")
            import_json = st.text_area("JSON настройки", height=100)
            if st.button("📥 Импортировать настройки"):
                if import_json.strip():
                    if import_settings(import_json):
                        time.sleep(1)
                        st.rerun()

    # Информация о настройках
    if settings.get('last_updated'):
        st.info(
            f"📅 Последнее обновление: {datetime.fromisoformat(settings['last_updated']).strftime('%d.%m.%Y %H:%M')}")


def get_default_video_settings():
    """Возвращает настройки по умолчанию для загрузки видео"""
    settings = load_default_settings()
    return settings['video_upload']


def get_default_stream_settings():
    """Возвращает настройки по умолчанию для стрим-уведомлений"""
    settings = load_default_settings()
    return settings['stream_notification']


def get_platform_settings(platform):
    """Возвращает настройки для конкретной платформы"""
    settings = load_default_settings()
    return settings.get(platform.lower(), {})


def main_settings():
    st.set_page_config(
        page_title="Default Settings",
        page_icon="⚙️",
        layout="wide"
    )

    st.title("⚙️ Настройки по умолчанию")
    st.markdown("Управление значениями по умолчанию для всех форм")

    show_default_settings_tab()


if __name__ == "__main__":
    main_settings()