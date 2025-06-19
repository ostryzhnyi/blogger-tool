import streamlit as st
import os
import json
import uuid
import time
from datetime import datetime

try:
    from uploaders.instagram import InstagramUploader
    from utils.VideoProcessor import VideoProcessor
    from default_settings import get_default_stream_settings
except ImportError as e:
    st.error(f"Ошибка импорта модулей: {e}")

STORIES_DIR = "stories"
STORIES_FILE = "stories/stories.json"


def load_stories():
    try:
        if os.path.exists(STORIES_FILE):
            with open(STORIES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Ошибка загрузки сторис: {e}")
    return []


def save_stories(stories_data):
    try:
        os.makedirs(STORIES_DIR, exist_ok=True)
        with open(STORIES_FILE, 'w', encoding='utf-8') as f:
            json.dump(stories_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Ошибка сохранения сторис: {e}")


def add_to_stories(file, title, platforms=None, story_config=None):
    if platforms is None:
        platforms = ["Instagram"]

    story_id = str(uuid.uuid4())

    os.makedirs(STORIES_DIR, exist_ok=True)

    file_extension = file.name.split('.')[-1].lower()
    if file_extension in ['mp4', 'mov', 'avi']:
        story_path = os.path.join(STORIES_DIR, f"{story_id}.mp4")
        story_type = 'video'
    else:
        story_path = os.path.join(STORIES_DIR, f"{story_id}.jpg")
        story_type = 'image'

    with open(story_path, "wb") as f:
        f.write(file.read())

    story_item = {
        'id': story_id,
        'title': title,
        'type': story_type,
        'platforms': platforms,
        'file_path': story_path,
        'story_config': story_config or {},
        'created_at': datetime.now().isoformat(),
        'status': 'pending'
    }

    stories = load_stories()
    stories.append(story_item)
    save_stories(stories)

    return story_id


def remove_from_stories(story_id):
    stories = load_stories()
    item_to_remove = None

    for item in stories:
        if item['id'] == story_id:
            item_to_remove = item
            break

    if item_to_remove:
        try:
            if os.path.exists(item_to_remove['file_path']):
                os.remove(item_to_remove['file_path'])
        except Exception as e:
            st.error(f"Ошибка удаления файлов: {e}")

        stories = [item for item in stories if item['id'] != story_id]
        save_stories(stories)
        return True
    return False


def update_story_status(story_id, status):
    stories = load_stories()
    for item in stories:
        if item['id'] == story_id:
            item['status'] = status
            break
    save_stories(stories)


def publish_story(item):
    config = st.session_state.platforms_config

    if item['status'] == 'publishing':
        print("Сторис уже публикуется...")
        return False

    success_count = 0
    total_platforms = len(item['platforms'])

    update_story_status(item['id'], 'publishing')

    for platform in item['platforms']:
        try:
            if platform == "Instagram":
                uploader = InstagramUploader()
                login_success = uploader.login(config['instagram']['username'], config['instagram']['password'])

                if not login_success:
                    raise Exception("Не удалось войти в Instagram")

                story_config = item.get('story_config', {})

                if story_config:
                    result = uploader.upload_story_with_stickers(item['file_path'], story_config)
                else:
                    if item['type'] == 'video':
                        processor = VideoProcessor()
                        processed_file = processor.prepare_for_instagram_story(item['file_path'])
                        result = uploader.upload_story(processed_file)
                    else:
                        result = uploader.upload_story(item['file_path'])

                if result:
                    print(f"✅ {platform}: Сторис загружена! ID: {result}")
                    success_count += 1
                else:
                    print(f"❌ {platform}: Ошибка загрузки сторис")

        except Exception as e:
            print(f"❌ Ошибка загрузки в {platform}: {str(e)}")

        time.sleep(2)

    if success_count == total_platforms:
        update_story_status(item['id'], 'published')
        return True
    elif success_count > 0:
        update_story_status(item['id'], 'partial')
        return True
    else:
        update_story_status(item['id'], 'failed')
        return False


def show_stories_tab():
    st.header("📺 Stream Notifications")
    st.markdown("Отправка уведомлений о начале стрима в Instagram Stories")

    config = st.session_state.platforms_config

    if not config.get('instagram', {}).get('authenticated', False):
        st.error("❌ Instagram не подключен!")
        st.info("Перейдите в настройки и подключите Instagram аккаунт")
        return

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📤 Создать уведомление о стриме")

        uploaded_file = st.file_uploader(
            "Загрузите превью стрима",
            type=['mp4', 'mov', 'avi', 'jpg', 'jpeg', 'png'],
            help="Поддерживаемые форматы: видео (MP4, MOV, AVI) и изображения (JPG, PNG)"
        )

        if uploaded_file:
            col_preview1, col_preview2, col_preview3 = st.columns([1, 1, 2])
            with col_preview1:
                if uploaded_file.type.startswith('video'):
                    st.video(uploaded_file)
                else:
                    st.image(uploaded_file)

            # Получаем настройки по умолчанию
            default_stream_settings = get_default_stream_settings()

            stream_title = st.text_input("Название стрима", max_chars=100, placeholder="Сегодня играем в...")
            stream_time = st.text_input("Время начала",
                                        value=default_stream_settings.get('default_time', ''),
                                        placeholder="20:00",
                                        help="Укажите время начала стрима")

            with st.expander("🎨 Дополнительные стикеры и текст", expanded=False):
                story_text = st.text_area("Текст на сторис",
                                          value=default_stream_settings.get('story_text', ''),
                                          placeholder="Скоро стрим!\nНе пропустите!",
                                          help="Текст будет наложен на изображение/видео")

                col_sticker1, col_sticker2 = st.columns(2)

                with col_sticker1:
                    hashtags = st.text_input("Хештеги",
                                             value=default_stream_settings.get('hashtags', ''),
                                             placeholder="#стрим #игры #live",
                                             help="Добавьте хештеги через пробел или #")
                    mentions = st.text_input("Упоминания",
                                             value=default_stream_settings.get('mentions', ''),
                                             placeholder="@username1 @username2",
                                             help="Упомяните пользователей")

                with col_sticker2:
                    stream_link = st.text_input("Ссылка на стрим",
                                                value=default_stream_settings.get('stream_link', ''),
                                                placeholder="https://twitch.tv/username",
                                                help="Ссылка (только для бизнес/верифицированных аккаунтов)")
                    location = st.text_input("Геолокация",
                                             value=default_stream_settings.get('location', ''),
                                             placeholder="Moscow, Russia",
                                             help="Добавить местоположение")

            col_btn1, col_btn2 = st.columns(2)

            with col_btn1:
                if st.button("📺 Отправить уведомление", type="primary"):
                    if stream_title:
                        try:
                            story_title = f"🔴 СТРИМ: {stream_title}"
                            if stream_time:
                                story_title += f" в {stream_time}"

                            story_config = {}

                            if story_text:
                                story_config['text'] = story_text
                            if hashtags:
                                story_config['hashtags'] = hashtags
                            if mentions:
                                story_config['mentions'] = mentions
                            if stream_link:
                                story_config['links'] = stream_link
                            if location:
                                story_config['location'] = location

                            story_id = add_to_stories(uploaded_file, story_title, ["Instagram"], story_config)
                            story_item = {
                                'id': story_id,
                                'title': story_title,
                                'type': 'video' if uploaded_file.type.startswith('video') else 'image',
                                'platforms': ['Instagram'],
                                'file_path': os.path.join(STORIES_DIR,
                                                          f"{story_id}.{'mp4' if uploaded_file.type.startswith('video') else 'jpg'}"),
                                'story_config': story_config,
                                'created_at': datetime.now().isoformat(),
                                'status': 'pending'
                            }

                            with st.spinner("Отправляем уведомление о стриме..."):
                                if publish_story(story_item):
                                    st.success("✅ Уведомление о стриме отправлено!")
                                    if story_config:
                                        st.info(
                                            f"🎨 Добавлены стикеры: {', '.join([k for k in story_config.keys() if story_config[k]])}")
                                    st.balloons()
                                else:
                                    st.error("❌ Ошибка отправки уведомления")

                            time.sleep(2)
                            st.rerun()

                        except Exception as e:
                            st.error(f"Ошибка отправки: {str(e)}")
                    else:
                        st.error("Заполните название стрима")

            with col_btn2:
                if st.button("💾 Сохранить для позже", type="secondary"):
                    if stream_title:
                        try:
                            story_title = f"🔴 СТРИМ: {stream_title}"
                            if stream_time:
                                story_title += f" в {stream_time}"

                            story_config = {}
                            if story_text:
                                story_config['text'] = story_text
                            if hashtags:
                                story_config['hashtags'] = hashtags
                            if mentions:
                                story_config['mentions'] = mentions
                            if stream_link:
                                story_config['links'] = stream_link
                            if location:
                                story_config['location'] = location

                            story_id = add_to_stories(uploaded_file, story_title, ["Instagram"], story_config)
                            st.success(f"✅ Уведомление сохранено! ID: {story_id[:8]}")
                            if story_config:
                                st.info(
                                    f"🎨 Сохранены стикеры: {', '.join([k for k in story_config.keys() if story_config[k]])}")
                            st.info("📋 Найдите его в списке ниже для отправки")
                        except Exception as e:
                            st.error(f"Ошибка сохранения: {str(e)}")
                    else:
                        st.error("Заполните название стрима")

    with col2:
        st.subheader("📊 Статистика")

        stories = load_stories()

        if stories:
            stream_stories = [s for s in stories if "СТРИМ:" in s.get('title', '')]

            status_counts = {}
            for story in stream_stories:
                status = story['status']
                status_counts[status] = status_counts.get(status, 0) + 1

            st.metric("Всего уведомлений", len(stream_stories))
            st.metric("Отправлено", status_counts.get('published', 0))
            st.metric("В ожидании", status_counts.get('pending', 0))
            st.metric("Ошибки", status_counts.get('failed', 0))

            if stream_stories:
                st.write("**Последние стримы:**")
                for story in sorted(stream_stories, key=lambda x: x['created_at'], reverse=True)[:3]:
                    status_emoji = '✅' if story['status'] == 'published' else '⏳' if story[
                                                                                         'status'] == 'pending' else '❌'
                    date_str = datetime.fromisoformat(story['created_at']).strftime('%d.%m %H:%M')
                    title_clean = story['title'].replace('🔴 СТРИМ: ', '')
                    st.write(f"{status_emoji} {title_clean} ({date_str})")
        else:
            st.info("Уведомлений пока нет")

    st.divider()

    st.subheader("📋 Сохраненные уведомления")

    stories = load_stories()

    if not stories:
        st.info("Сохраненных уведомлений нет")
        return

    stream_stories = [s for s in stories if "СТРИМ:" in s.get('title', '')]

    if not stream_stories:
        st.info("Уведомлений о стримах нет")
        return

    status_filter = st.selectbox(
        "Фильтр по статусу:",
        ["Все", "pending", "publishing", "published", "failed"],
        index=0,
        key="stream_filter"
    )

    filtered_stories = stream_stories
    if status_filter != "Все":
        filtered_stories = [story for story in stream_stories if story['status'] == status_filter]

    if not filtered_stories:
        st.info(f"Нет уведомлений со статусом '{status_filter}'")
        return

    for story in filtered_stories:
        status_emoji = {
            'pending': '⏳',
            'publishing': '🔄',
            'published': '✅',
            'partial': '⚠️',
            'failed': '❌'
        }.get(story['status'], '❓')

        display_title = story['title'].replace('🔴 СТРИМ: ', '')

        with st.expander(f"{status_emoji} {display_title}", expanded=False):
            col1, col2 = st.columns([2, 1])

            with col1:
                if os.path.exists(story['file_path']):
                    col_preview1, col_preview2, col_preview3 = st.columns([1, 1, 2])
                    with col_preview1:
                        if story['type'] == 'video':
                            st.video(story['file_path'])
                        else:
                            st.image(story['file_path'])
                else:
                    st.error("❌ Файл не найден")

                st.write(f"**Полное название:** {story['title']}")
                st.write(f"**Тип:** {story['type'].title()}")
                st.write(f"**Создано:** {datetime.fromisoformat(story['created_at']).strftime('%d.%m.%Y %H:%M')}")

                story_config = story.get('story_config', {})
                if story_config:
                    st.write("**🎨 Стикеры и элементы:**")
                    stickers_info = []
                    if story_config.get('text'):
                        stickers_info.append(f"📝 Текст: {story_config['text'][:30]}...")
                    if story_config.get('hashtags'):
                        stickers_info.append(f"# Хештеги: {story_config['hashtags']}")
                    if story_config.get('mentions'):
                        stickers_info.append(f"@ Упоминания: {story_config['mentions']}")
                    if story_config.get('links'):
                        stickers_info.append(f"🔗 Ссылка: {story_config['links']}")
                    if story_config.get('location'):
                        stickers_info.append(f"📍 Локация: {story_config['location']}")

                    for info in stickers_info:
                        st.write(f"  - {info}")
                else:
                    st.write("**🎨 Стикеры:** Нет дополнительных элементов")

                status_colors = {
                    'pending': '🟡',
                    'publishing': '🔵',
                    'published': '🟢',
                    'partial': '🟠',
                    'failed': '🔴'
                }
                status_text = {
                    'pending': 'Готово к отправке',
                    'publishing': 'Отправляется...',
                    'published': 'Отправлено',
                    'partial': 'Частично отправлено',
                    'failed': 'Ошибка отправки'
                }

                st.write(
                    f"**Статус:** {status_colors.get(story['status'], '❓')} {status_text.get(story['status'], story['status'])}")

            with col2:
                st.write("### Действия")

                if story['status'] in ['pending', 'failed']:
                    if st.button("📺 Отправить уведомление", key=f"send_stream_{story['id']}"):
                        if os.path.exists(story['file_path']):
                            try:
                                with st.spinner("Отправляем уведомление о стриме..."):
                                    if publish_story(story):
                                        st.success("✅ Уведомление отправлено!")
                                        st.balloons()
                                    else:
                                        st.error("❌ Ошибка отправки")
                                time.sleep(2)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Ошибка отправки: {e}")
                        else:
                            st.error("Файл не найден")
                elif story['status'] == 'publishing':
                    st.info("🔄 Отправляется...")
                else:
                    st.success("✅ Уже отправлено")

                if st.button("🗑️ Удалить", key=f"delete_stream_{story['id']}", type="secondary"):
                    if st.session_state.get(f"confirm_delete_stream_{story['id']}", False):
                        if remove_from_stories(story['id']):
                            st.success("✅ Удалено")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Ошибка удаления")
                        st.session_state[f"confirm_delete_stream_{story['id']}"] = False
                    else:
                        st.session_state[f"confirm_delete_stream_{story['id']}"] = True
                        st.warning("Нажмите еще раз для подтверждения")
                        time.sleep(2)
                        st.rerun()


def show_stories_stats():
    stories = load_stories()

    if not stories:
        return

    st.subheader("📊 Подробная статистика сторис")

    status_counts = {}
    type_counts = {}

    for story in stories:
        status = story['status']
        story_type = story['type']

        status_counts[status] = status_counts.get(status, 0) + 1
        type_counts[story_type] = type_counts.get(story_type, 0) + 1

    col1, col2 = st.columns(2)

    with col1:
        st.write("**По статусу:**")
        for status, count in status_counts.items():
            emoji = {
                'pending': '⏳',
                'publishing': '🔄',
                'published': '✅',
                'partial': '⚠️',
                'failed': '❌'
            }.get(status, '❓')
            st.write(f"{emoji} {status}: {count}")

    with col2:
        st.write("**По типу:**")
        for story_type, count in type_counts.items():
            emoji = '🎥' if story_type == 'video' else '📸'
            st.write(f"{emoji} {story_type}: {count}")


def main_stories():
    st.set_page_config(
        page_title="Stories Manager",
        page_icon="📸",
        layout="wide"
    )

    st.title("📸 Менеджер сторис")
    st.markdown("Управление сторис для Instagram")

    if 'platforms_config' not in st.session_state:
        from main import load_platforms_config
        st.session_state.platforms_config = load_platforms_config()

    show_stories_stats()
    st.divider()
    show_stories_tab()


if __name__ == "__main__":
    main_stories()