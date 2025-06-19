import streamlit as st
import os
import json
import uuid
import time
from datetime import datetime

try:
    from uploaders.youtube import YouTubeUploader
    from uploaders.tiktok import TikTokUploader
    from uploaders.instagram import InstagramUploader
    from utils.VideoProcessor import VideoProcessor
except ImportError as e:
    st.error(f"Ошибка импорта модулей: {e}")

QUEUE_DIR = "queue"
QUEUE_FILE = "queue/queue.json"


def load_queue():
    try:
        if os.path.exists(QUEUE_FILE):
            with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Ошибка загрузки очереди: {e}")
    return []


def save_queue(queue_data):
    try:
        os.makedirs(QUEUE_DIR, exist_ok=True)
        with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
            json.dump(queue_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Ошибка сохранения очереди: {e}")


def add_to_queue(file, title, description, tags, category, privacy, thumbnail, platforms, made_for_kids):
    queue_item_id = str(uuid.uuid4())

    os.makedirs(QUEUE_DIR, exist_ok=True)
    video_path = os.path.join(QUEUE_DIR, f"{queue_item_id}.mp4")

    with open(video_path, "wb") as f:
        f.write(file.read())

    thumbnail_path = None
    if thumbnail:
        thumbnail_path = os.path.join(QUEUE_DIR, f"{queue_item_id}_thumb.jpg")
        with open(thumbnail_path, "wb") as f:
            f.write(thumbnail.read())

    queue_item = {
        'id': queue_item_id,
        'title': title,
        'description': description,
        'tags': tags,
        'category': category,
        'privacy': privacy,
        'platforms': platforms,
        'made_for_kids': made_for_kids,
        'video_path': video_path,
        'thumbnail_path': thumbnail_path,
        'created_at': datetime.now().isoformat(),
        'status': 'pending'
    }

    queue = load_queue()
    queue.append(queue_item)
    save_queue(queue)

    return queue_item_id


def remove_from_queue(queue_item_id):
    queue = load_queue()
    item_to_remove = None

    for item in queue:
        if item['id'] == queue_item_id:
            item_to_remove = item
            break

    if item_to_remove:
        try:
            if os.path.exists(item_to_remove['video_path']):
                os.remove(item_to_remove['video_path'])
            if item_to_remove.get('thumbnail_path') and os.path.exists(item_to_remove['thumbnail_path']):
                os.remove(item_to_remove['thumbnail_path'])
        except Exception as e:
            st.error(f"Ошибка удаления файлов: {e}")

        queue = [item for item in queue if item['id'] != queue_item_id]
        save_queue(queue)
        return True
    return False


def update_queue_item_status(queue_item_id, status):
    queue = load_queue()
    for item in queue:
        if item['id'] == queue_item_id:
            item['status'] = status
            break
    save_queue(queue)


def get_queue_item(queue_item_id):
    queue = load_queue()
    for item in queue:
        if item['id'] == queue_item_id:
            return item
    return None


def publish_from_queue(item):
    config = st.session_state.platforms_config

    video_id = f"queue_{item['id']}"

    st.session_state.upload_status[video_id] = {
        'title': item['title'],
        'timestamp': datetime.now().strftime("%H:%M:%S"),
        'platforms': {platform: "pending" for platform in item['platforms']}
    }

    processor = VideoProcessor()
    is_for_kids = item['made_for_kids'].startswith("Да")

    update_queue_item_status(item['id'], 'processing')

    success_count = 0
    total_platforms = len(item['platforms'])

    for platform in item['platforms']:
        st.session_state.upload_status[video_id]['platforms'][platform] = "uploading"

        with st.spinner(f"Загружаем на {platform}..."):
            try:
                if platform == "YouTube":
                    uploader = YouTubeUploader()
                    uploader.authenticate(
                        config['youtube']['client_id'],
                        config['youtube']['client_secret']
                    )
                    result = uploader.upload(item['video_path'], item['title'], item['description'],
                                             item['tags'], item['category'], item['privacy'], is_for_kids)

                elif platform == "TikTok":
                    processed_video = processor.prepare_for_tiktok(item['video_path'])
                    uploader = TikTokUploader()

                    if not uploader._check_logged_in():
                        st.warning("⚠️ Сессия TikTok истекла, выполняется повторный вход...")
                        login_success = uploader.login(config['tiktok']['username'], config['tiktok']['password'])
                        if not login_success:
                            raise Exception("Не удалось войти в TikTok повторно")

                    tiktok_caption = f"{item['title']}\n\n{item['description']}"
                    tiktok_hashtags = f"#{item['tags'].replace(', ', ' #').replace(',', ' #')}"

                    st.info("🎯 Подготавливаем TikTok к загрузке...")
                    st.warning("⚠️ После заполнения полей вам нужно будет ВРУЧНУЮ нажать кнопку 'Post' в браузере!")

                    result = uploader.prepare_for_upload(processed_video, tiktok_caption, tiktok_hashtags)

                    if result:
                        st.success("✅ TikTok: Все поля заполнены! Теперь нажмите кнопку 'Post' в браузере.")
                        st.info("👆 Кнопка публикации подсвечена красным в браузере")
                    else:
                        st.error("❌ TikTok: Ошибка подготовки к загрузке")

                elif platform == "Instagram":
                    processed_video = processor.prepare_for_instagram(item['video_path'])
                    uploader = InstagramUploader()
                    uploader.login(config['instagram']['username'], config['instagram']['password'])

                    instagram_caption = f"{item['title']}\n\n{item['description']}"
                    instagram_tags = f"#{item['tags'].replace(', ', ' #').replace(',', ' #')}"

                    result = uploader.upload(processed_video, instagram_caption, instagram_tags)

                if result:
                    st.session_state.upload_status[video_id]['platforms'][platform] = "success"
                    st.success(f"✅ {platform}: Загружено успешно!")
                    success_count += 1
                else:
                    st.session_state.upload_status[video_id]['platforms'][platform] = "error"
                    st.error(f"❌ {platform}: Ошибка загрузки")

            except Exception as e:
                st.session_state.upload_status[video_id]['platforms'][platform] = "error"
                st.error(f"❌ Ошибка загрузки на {platform}: {str(e)}")

            time.sleep(1)

    if success_count == total_platforms:
        update_queue_item_status(item['id'], 'completed')
    elif success_count > 0:
        update_queue_item_status(item['id'], 'partial')
    else:
        update_queue_item_status(item['id'], 'failed')


def show_queue_tab():
    st.header("📋 Очередь загрузки")

    queue = load_queue()

    if not queue:
        st.info("Очередь пуста")
        if st.button("🔄 Обновить"):
            st.rerun()
        return

    col_header1, col_header2 = st.columns([3, 1])
    with col_header1:
        st.write(f"**Всего элементов в очереди:** {len(queue)}")
    with col_header2:
        if st.button("🔄 Обновить очередь"):
            st.rerun()

    st.divider()

    status_filter = st.selectbox(
        "Фильтр по статусу:",
        ["Все", "pending", "processing", "completed", "partial", "failed"],
        index=0
    )

    filtered_queue = queue
    if status_filter != "Все":
        filtered_queue = [item for item in queue if item['status'] == status_filter]

    if not filtered_queue:
        st.info(f"Нет элементов со статусом '{status_filter}'")
        return

    for item in filtered_queue:
        status_emoji = {
            'pending': '⏳',
            'processing': '🔄',
            'completed': '✅',
            'partial': '⚠️',
            'failed': '❌'
        }.get(item['status'], '❓')

        with st.expander(f"{status_emoji} {item['title']}", expanded=False):
            col1, col2 = st.columns([2, 1])

            with col1:
                if os.path.exists(item['video_path']):
                    col_video1, col_video2, col_video3 = st.columns([1, 1, 2])
                    with col_video1:
                        st.video(item['video_path'])
                else:
                    st.error("❌ Видео файл не найден")

                with st.container():
                    st.write(
                        f"**Описание:** {item['description'][:200]}{'...' if len(item['description']) > 200 else ''}")
                    st.write(f"**Теги:** {item['tags']}")
                    st.write(f"**Категория:** {item['category']}")
                    st.write(f"**Приватность:** {item['privacy']}")
                    st.write(f"**Платформы:** {', '.join(item['platforms'])}")
                    st.write(f"**Создано:** {datetime.fromisoformat(item['created_at']).strftime('%d.%m.%Y %H:%M')}")

                    status_colors = {
                        'pending': '🟡',
                        'processing': '🔵',
                        'completed': '🟢',
                        'partial': '🟠',
                        'failed': '🔴'
                    }
                    status_text = {
                        'pending': 'Ожидает',
                        'processing': 'Обрабатывается',
                        'completed': 'Завершено',
                        'partial': 'Частично завершено',
                        'failed': 'Ошибка'
                    }

                    st.write(
                        f"**Статус:** {status_colors.get(item['status'], '❓')} {status_text.get(item['status'], item['status'])}")

            with col2:
                st.write("### Действия")

                if item['status'] in ['pending', 'failed', 'partial']:
                    if st.button("🚀 Публиковать", key=f"publish_{item['id']}"):
                        if os.path.exists(item['video_path']):
                            try:
                                publish_from_queue(item)
                                st.success("✅ Публикация запущена!")
                                time.sleep(2)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Ошибка публикации: {e}")
                        else:
                            st.error("Видео файл не найден")
                else:
                    st.info("Публикация завершена")

                if st.button("📋 Показать детали", key=f"details_{item['id']}"):
                    show_item_details(item)

                if st.button("🗑️ Удалить", key=f"delete_{item['id']}", type="secondary"):
                    if st.session_state.get(f"confirm_delete_{item['id']}", False):
                        if remove_from_queue(item['id']):
                            st.success("✅ Удалено из очереди")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Ошибка удаления")
                        st.session_state[f"confirm_delete_{item['id']}"] = False
                    else:
                        st.session_state[f"confirm_delete_{item['id']}"] = True
                        st.warning("Нажмите еще раз для подтверждения")
                        time.sleep(2)
                        st.rerun()


def show_item_details(item):
    st.subheader(f"📄 Детали: {item['title']}")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Основная информация:**")
        st.json({
            'ID': item['id'],
            'Название': item['title'],
            'Категория': item['category'],
            'Приватность': item['privacy'],
            'Для детей': item['made_for_kids'],
            'Платформы': item['platforms'],
            'Статус': item['status']
        })

    with col2:
        st.write("**Описание:**")
        st.text_area("", value=item['description'], height=150, disabled=True)

        st.write("**Теги:**")
        st.write(item['tags'])

        st.write("**Файлы:**")
        st.write(f"Видео: {item['video_path']}")
        if item.get('thumbnail_path'):
            st.write(f"Превью: {item['thumbnail_path']}")


def show_queue_stats():
    queue = load_queue()

    if not queue:
        return

    st.subheader("📊 Статистика очереди")

    status_counts = {}
    for item in queue:
        status = item['status']
        status_counts[status] = status_counts.get(status, 0) + 1

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Всего", len(queue))
    with col2:
        st.metric("Ожидают", status_counts.get('pending', 0))
    with col3:
        st.metric("Обрабатывается", status_counts.get('processing', 0))
    with col4:
        st.metric("Завершено", status_counts.get('completed', 0))
    with col5:
        st.metric("Ошибки", status_counts.get('failed', 0))


def main_queue():
    st.set_page_config(
        page_title="Queue Manager",
        page_icon="📋",
        layout="wide"
    )

    st.title("📋 Менеджер очереди загрузки")
    st.markdown("Управление очередью видео для публикации")

    if 'upload_status' not in st.session_state:
        st.session_state.upload_status = {}
    if 'platforms_config' not in st.session_state:
        from main import load_platforms_config
        st.session_state.platforms_config = load_platforms_config()

    show_queue_stats()
    st.divider()
    show_queue_tab()


if __name__ == "__main__":
    main_queue()