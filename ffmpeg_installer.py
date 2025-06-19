import streamlit as st
import subprocess
import requests
import zipfile
import os
import shutil


def check_ffmpeg_installation():
    """Проверяет, установлен ли FFmpeg"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        return True, result.stdout.split('\n')[0]
    except FileNotFoundError:
        return False, "FFmpeg не найден"


def download_ffmpeg_windows():
    """Скачивает FFmpeg для Windows"""
    try:
        st.info("🔄 Скачиваем FFmpeg...")

        # URL для скачивания FFmpeg (можно использовать другой источник)
        url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"

        response = requests.get(url, stream=True)
        response.raise_for_status()

        zip_path = "ffmpeg.zip"
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        st.info("📦 Распаковываем FFmpeg...")

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(".")

        # Находим папку с FFmpeg
        ffmpeg_folder = None
        for item in os.listdir("."):
            if item.startswith("ffmpeg-") and os.path.isdir(item):
                ffmpeg_folder = item
                break

        if ffmpeg_folder:
            # Перемещаем ffmpeg.exe в корневую папку
            ffmpeg_exe = os.path.join(ffmpeg_folder, "bin", "ffmpeg.exe")
            if os.path.exists(ffmpeg_exe):
                shutil.copy2(ffmpeg_exe, "ffmpeg.exe")
                st.success("✅ FFmpeg установлен успешно!")

                # Очищаем временные файлы
                os.remove(zip_path)
                shutil.rmtree(ffmpeg_folder)

                return True

        st.error("❌ Ошибка установки FFmpeg")
        return False

    except Exception as e:
        st.error(f"❌ Ошибка скачивания FFmpeg: {e}")
        return False


def show_ffmpeg_status():
    """Показывает статус FFmpeg и кнопки установки"""

    is_installed, version_info = check_ffmpeg_installation()

    if is_installed:
        st.success(f"✅ FFmpeg установлен: {version_info}")
        return True
    else:
        st.error("❌ FFmpeg не найден")
        st.warning("Для работы транскрипции необходим FFmpeg")

        with st.expander("📋 Инструкция по установке FFmpeg", expanded=True):
            st.markdown("""
            **Вариант 1: Автоматическая установка (рекомендуется)**

            Нажмите кнопку ниже для автоматического скачивания:
            """)

            if st.button("🚀 Скачать FFmpeg автоматически"):
                if download_ffmpeg_windows():
                    st.rerun()

            st.markdown("""
            **Вариант 2: Ручная установка**

            1. Скачайте FFmpeg с [официального сайта](https://ffmpeg.org/download.html)
            2. Распакуйте архив
            3. Добавьте папку bin в PATH системы
            4. Перезапустите приложение

            **Вариант 3: Через пакетный менеджер**

            Windows (Chocolatey):
            ```
            choco install ffmpeg
            ```

            Windows (Scoop):
            ```
            scoop install ffmpeg
            ```

            **Вариант 4: Альтернативная установка**

            Установите MoviePy как альтернативу:
            ```
            pip install moviepy
            ```
            """)

        return False


if __name__ == "__main__":
    st.title("🔧 FFmpeg Installation Helper")
    show_ffmpeg_status()