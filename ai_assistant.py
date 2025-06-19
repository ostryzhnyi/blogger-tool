import streamlit as st
import os
import json
import tempfile
import subprocess
from datetime import datetime
import warnings

warnings.filterwarnings("ignore")

AI_CONFIG_FILE = "config/ai_config.json"


def load_ai_config():
    """Загружает конфигурацию AI"""
    try:
        if os.path.exists(AI_CONFIG_FILE):
            with open(AI_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Ошибка загрузки AI конфигурации: {e}")

    return {
        'openai_api_key': '',
        'openai_model': 'gpt-4o-mini',
        'whisper_model': 'base',
        'max_tokens': 150,
        'temperature': 0.7,
        'authenticated': False,
        'last_updated': None
    }


def save_ai_config(config):
    """Сохраняет конфигурацию AI"""
    try:
        os.makedirs('config', exist_ok=True)
        config['last_updated'] = datetime.now().isoformat()
        with open(AI_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Ошибка сохранения AI конфигурации: {e}")
        return False


def get_ai_config():
    """Получает текущую конфигурацию AI"""
    if 'ai_config' not in st.session_state:
        st.session_state.ai_config = load_ai_config()
    return st.session_state.ai_config


def is_ai_configured():
    """Проверяет, настроен ли AI"""
    config = get_ai_config()
    return config.get('authenticated', False) and config.get('openai_api_key', '')


def test_openai_connection(api_key, model="gpt-4o-mini"):
    """Тестирует подключение к OpenAI"""
    try:
        import openai
        openai.api_key = api_key

        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": "Тест"}],
            max_tokens=10
        )

        return bool(response and response.choices)
    except Exception as e:
        print(f"Ошибка подключения к OpenAI: {e}")
        return False


def fix_common_transcription_errors(text):
    """Исправляет типичные ошибки транскрипции для смешанной речи"""
    import re

    # Словарь замен для частых ошибок
    replacements = {
        # Социальные сети
        'ютуб': 'YouTube',
        'ютьюб': 'YouTube',
        'ю-туб': 'YouTube',
        'тикток': 'TikTok',
        'тик-ток': 'TikTok',
        'инстаграм': 'Instagram',
        'инста': 'Instagram',

        # Технические термины
        'апи': 'API',
        'эйпиай': 'API',
        'юай': 'UI',
        'юикс': 'UX',
        'апдейт': 'update',
        'аплоад': 'upload',
        'даунлоад': 'download',
        'стрим': 'stream',
        'контент': 'content',
        'браузер': 'browser',
        'юзер': 'user',
        'юзеры': 'users',

        # Частые английские слова
        'окей': 'okay',
        'оке': 'OK',
        'плиз': 'please',
        'сори': 'sorry',
        'хай': 'hi',
        'бай': 'bye',

        # Исправление слитного написания
        'видеона': 'видео на',
        'этовидео': 'это видео',
        'навидео': 'на видео',

        'хардскилл': 'hardskill',
        'лид': 'lead',
        'дев': 'dev',
        'арты': 'arts',
        'юайка': 'UI',
    }

    # Применяем замены (с учетом регистра)
    for wrong, correct in replacements.items():
        # Заменяем с учетом границ слова
        pattern = r'\b' + re.escape(wrong) + r'\b'
        text = re.sub(pattern, correct, text, flags=re.IGNORECASE)

    # Дополнительные исправления
    # Убираем лишние пробелы
    text = re.sub(r'\s+', ' ', text)

    # Исправляем пунктуацию вокруг английских слов
    text = re.sub(r'\s+([.,!?])', r'\1', text)

    return text.strip()


def check_transcription_methods():
    """Проверяет доступные методы транскрипции"""
    methods = {}

    # Проверяем Whisper
    try:
        import whisper
        methods['whisper'] = True
    except ImportError:
        methods['whisper'] = False

    # Проверяем Speech Recognition
    try:
        import speech_recognition
        methods['speech_recognition'] = True
    except ImportError:
        methods['speech_recognition'] = False

    # Проверяем FFmpeg
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        methods['ffmpeg'] = True
    except:
        methods['ffmpeg'] = False

    # Проверяем MoviePy
    try:
        import moviepy
        methods['moviepy'] = True
    except ImportError:
        methods['moviepy'] = False

    # OpenAI API
    methods['openai_api'] = is_ai_configured()

    return methods


def extract_audio_with_ffmpeg(video_path):
    """Извлечение аудио через FFmpeg напрямую"""
    try:
        audio_path = video_path.replace('.mp4', '_audio.wav')

        # Команда FFmpeg для извлечения аудио
        cmd = [
            'ffmpeg',
            '-i', video_path,  # Входной файл
            '-vn',  # Без видео
            '-acodec', 'pcm_s16le',  # Кодек
            '-ar', '16000',  # Частота дискретизации 16kHz (оптимально для речи)
            '-ac', '1',  # Моно
            '-y',  # Перезаписывать без вопросов
            audio_path
        ]

        # Запускаем FFmpeg
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return audio_path
        else:
            st.error(f"FFmpeg ошибка: {result.stderr}")
            return None

    except FileNotFoundError:
        st.error("FFmpeg не найден в системе!")
        return None
    except Exception as e:
        st.error(f"Ошибка извлечения аудио: {e}")
        return None


def extract_audio_simple(video_path):
    """Простое извлечение аудио"""
    try:
        audio_path = video_path.replace('.mp4', '_audio.wav')

        # Пробуем FFmpeg
        try:
            subprocess.run([
                'ffmpeg', '-i', video_path,
                '-ac', '1', '-ar', '16000',
                '-y', audio_path
            ], capture_output=True, check=True)
            return audio_path
        except:
            pass

        # Пробуем MoviePy
        try:
            from moviepy.editor import VideoFileClip
            video = VideoFileClip(video_path)
            audio = video.audio
            audio.write_audiofile(audio_path, verbose=False, logger=None)
            audio.close()
            video.close()
            return audio_path
        except:
            pass

        return None

    except Exception as e:
        print(f"Ошибка извлечения аудио: {e}")
        return None


def transcribe_with_whisper(audio_path, model_name="medium"):
    """Транскрипция через Whisper с исправлениями для Windows"""
    try:
        import whisper

        st.info(f"🎤 Загружаем модель Whisper {model_name}...")

        # Загружаем модель (используем CPU для стабильности)
        model = whisper.load_model(model_name)

        st.info("📝 Начинаем транскрипцию...")

        # Транскрибируем с параметрами для лучшего качества
        result = model.transcribe(
            audio_path,
            language='ru',  # Явно указываем русский язык
            task='transcribe',  # transcribe, а не translate
            fp16=False,  # Отключаем FP16 для CPU
            verbose=False,  # Убираем verbose для получения всех сегментов
            # Дополнительные параметры для качества
            temperature=0.0,  # Меньше креативности, больше точности
            compression_ratio_threshold=2.4,
            logprob_threshold=-1.0,
            no_speech_threshold=0.6,
            condition_on_previous_text=True,  # Учитывать контекст
            # Подсказка для смешанной речи
            initial_prompt="Это видео на русском языке с английскими техническими терминами. English words: YouTube, TikTok, Instagram, upload, video, stream, content, API, browser, UI, UX, hardskill."
        )

        # Получаем все сегменты для проверки
        if 'segments' in result:
            st.info(f"Обработано сегментов: {len(result['segments'])}")

            # Проверяем на пропуски
            full_text = []
            last_end = 0

            for segment in result['segments']:
                start = segment['start']
                end = segment['end']
                text = segment['text'].strip()

                # Если есть пропуск более 3 секунд
                if start - last_end > 3:
                    st.warning(f"⚠️ Возможен пропуск между {last_end:.1f}s и {start:.1f}s")

                if text:
                    full_text.append(f"[{start:.3f} --> {end:.3f}] {text}")

                last_end = end

            # Объединяем текст
            text_with_timestamps = "\n".join(full_text)

            # Также сохраняем простой текст
            simple_text = result['text'].strip()

            # Постобработка для исправления частых ошибок
            simple_text = fix_common_transcription_errors(simple_text)

            # Сохраняем в session_state для отладки
            st.session_state['last_transcription_segments'] = text_with_timestamps

            # Показываем опцию просмотра с таймкодами
            with st.expander("📝 Транскрипция с таймкодами", expanded=False):
                st.text_area("Сегменты:", value=text_with_timestamps, height=200, disabled=True)

            return simple_text
        else:
            # Если нет сегментов, возвращаем просто текст
            text = result['text'].strip()
            text = fix_common_transcription_errors(text)
            return text
    except Exception as e:
        print(f"error: {e}")


def transcribe_with_whisper_segments(audio_path, model_name="medium"):
    """Альтернативный метод транскрипции Whisper по сегментам для избежания пропусков"""
    try:
        import whisper
        from pydub import AudioSegment

        st.info(f"🎤 Загружаем модель Whisper {model_name}...")
        model = whisper.load_model(model_name)

        # Загружаем аудио
        audio = AudioSegment.from_wav(audio_path)

        # Разбиваем на сегменты по 30 секунд с перекрытием
        segment_length_ms = 20000    # 20 секунд
        overlap_ms = 10000   # 10 секунд перекрытия

        segments = []
        for start_ms in range(0, len(audio), segment_length_ms - overlap_ms):
            end_ms = min(start_ms + segment_length_ms, len(audio))
            segment = audio[start_ms:end_ms]
            segments.append((start_ms, end_ms, segment))

        st.info(f"📝 Обрабатываем {len(segments)} сегментов...")
        progress_bar = st.progress(0)

        all_transcriptions = []

        for i, (start_ms, end_ms, segment) in enumerate(segments):
            progress_bar.progress((i + 1) / len(segments))

            # Сохраняем временный файл
            temp_path = f"temp_segment_{i}.wav"
            segment.export(temp_path, format="wav")

            try:
                # Транскрибируем сегмент
                result = model.transcribe(
                    temp_path,
                    language='ru',
                    task='transcribe',
                    fp16=False,
                    temperature=0.0,
                    initial_prompt="Это продолжение видео на русском языке с техническими терминами."
                )

                if result and result['text'].strip():
                    all_transcriptions.append({
                        'start': start_ms / 1000,
                        'end': end_ms / 1000,
                        'text': result['text'].strip()
                    })

            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        progress_bar.empty()

        # Объединяем транскрипции, убирая дубликаты из перекрытий
        final_text = []
        for i, trans in enumerate(all_transcriptions):
            text = trans['text']

            # Если это не первый сегмент, пытаемся убрать дубликаты
            if i > 0 and final_text:
                # Берем последние слова предыдущего сегмента
                prev_words = final_text[-1].split()[-10:]
                curr_words = text.split()[:10]

                # Ищем перекрытие
                overlap_idx = 0
                for j in range(min(len(prev_words), len(curr_words))):
                    if prev_words[-j - 1:] == curr_words[:j + 1]:
                        overlap_idx = j + 1

                # Убираем перекрывающуюся часть
                if overlap_idx > 0:
                    text = ' '.join(text.split()[overlap_idx:])

            final_text.append(text)

        # Объединяем весь текст
        full_text = ' '.join(final_text)
        full_text = fix_common_transcription_errors(full_text)

        return full_text

    except Exception as e:
        st.error(f"Ошибка сегментной транскрипции: {e}")
        return None
        st.error("❌ FFmpeg не найден!")
        st.info("""
        **Установите FFmpeg:**

        1. Скачайте FFmpeg: https://www.gyan.dev/ffmpeg/builds/
        2. Выберите "release essentials" 
        3. Распакуйте в C:\\ffmpeg
        4. Добавьте C:\\ffmpeg\\bin в PATH:
           - Откройте "Переменные среды"
           - Найдите PATH
           - Добавьте C:\\ffmpeg\\bin
        5. Перезапустите терминал/IDE

        Или установите через Chocolatey:
        ```
        choco install ffmpeg
        ```
        """)
        return None

    except Exception as e:
        st.error(f"Ошибка Whisper: {e}")
        return None


def transcribe_with_whisper_multilingual(audio_path, model_name="base"):
    """Альтернативный метод - мультиязычная транскрипция"""
    try:
        import whisper

        model = whisper.load_model(model_name)

        # Транскрибируем БЕЗ указания языка - пусть модель сама определит
        result = model.transcribe(
            audio_path,
            task='transcribe',
            fp16=False,
            temperature=0.0,
            # Не указываем язык!
            # language='ru',
        )

        # Модель сама определит язык для каждого сегмента
        text = result['text'].strip()

        # Применяем постобработку
        text = fix_common_transcription_errors(text)

        return text

    except Exception as e:
        st.error(f"Ошибка мультиязычной транскрипции: {e}")
        return None


def transcribe_with_speech_recognition(audio_path):
    """Транскрипция через Speech Recognition с поддержкой длинных аудио"""
    try:
        import speech_recognition as sr
        from pydub import AudioSegment

        recognizer = sr.Recognizer()

        # Загружаем аудио файл
        audio = AudioSegment.from_wav(audio_path)

        # Длина чанка в миллисекундах (15 секунд для надежности)
        chunk_length_ms = 15000
        chunks = []

        # Разбиваем аудио на части
        for i in range(0, len(audio), chunk_length_ms):
            chunk = audio[i:i + chunk_length_ms]
            chunks.append(chunk)

        # Прогресс бар для пользователя
        progress_text = st.empty()
        progress_bar = st.progress(0)

        full_transcript = []

        for i, chunk in enumerate(chunks):
            progress_text.text(f"Обработка части {i + 1} из {len(chunks)}...")
            progress_bar.progress((i + 1) / len(chunks))

            # Экспортируем чанк во временный файл
            chunk_filename = f"temp_chunk_{i}.wav"
            chunk.export(chunk_filename, format="wav")

            try:
                with sr.AudioFile(chunk_filename) as source:
                    audio_data = recognizer.record(source)

                    try:
                        # Пробуем распознать на русском
                        text = recognizer.recognize_google(audio_data, language='ru-RU')
                        full_transcript.append(text)
                    except sr.UnknownValueError:
                        # Если не удалось на русском, пробуем английский
                        try:
                            text = recognizer.recognize_google(audio_data, language='en-US')
                            full_transcript.append(text)
                        except sr.UnknownValueError:
                            # Пропускаем непонятные части
                            st.warning(f"Не удалось распознать часть {i + 1}")
                    except sr.RequestError as e:
                        st.error(f"Ошибка API: {e}")

            finally:
                # Удаляем временный файл
                if os.path.exists(chunk_filename):
                    os.remove(chunk_filename)

        # Очищаем прогресс
        progress_text.empty()
        progress_bar.empty()

        # Объединяем все части
        return " ".join(full_transcript)

    except ImportError:
        st.error("Установите pydub: pip install pydub")
        return None
    except Exception as e:
        print(f"Ошибка Speech Recognition: {e}")
        return None


def transcribe_with_openai_api(audio_path):
    """Транскрипция через OpenAI API"""
    try:
        if not is_ai_configured():
            return None

        config = get_ai_config()
        api_key = config.get('openai_api_key')

        import openai
        openai.api_key = api_key

        # Проверяем размер файла
        if os.path.getsize(audio_path) > 25 * 1024 * 1024:
            print("Файл слишком большой для OpenAI API")
            return None

        with open(audio_path, 'rb') as audio_file:
            transcript = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file,
                language="ru"
            )

        return transcript.text if hasattr(transcript, 'text') else str(transcript)

    except Exception as e:
        print(f"Ошибка OpenAI API: {e}")
        return None


def transcribe_video_enhanced(video_path, model_name="medium"):
    """Улучшенная транскрипция видео"""
    try:
        st.info("🎵 Извлекаем аудио из видео...")

        # Сначала пробуем FFmpeg напрямую
        audio_path = extract_audio_with_ffmpeg(video_path)

        if not audio_path:
            # Если не получилось, используем старый метод
            audio_path = extract_audio_simple(video_path)

        if not audio_path:
            st.error("Не удалось извлечь аудио")
            return None

        # Проверяем размер файла
        file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        st.info(f"Размер аудио: {file_size_mb:.1f} МБ")

        # Выбираем метод транскрипции
        transcript = None

        # Проверяем настройки
        config = get_ai_config()
        use_segments = st.checkbox("Использовать посегментную транскрипцию",
                                   value=True,
                                   help="Более надежно, но медленнее. Рекомендуется для длинных видео.")

        # 1. Пробуем Whisper (лучшее качество)
        if file_size_mb < 100:  # Whisper может обработать файлы до 100МБ
            #if use_segments and file_size_mb > 5:  # Для файлов больше 5МБ используем сегменты
             #  st.info("🎤 Используем Whisper с сегментацией...")
              #  transcript = transcribe_with_whisper_segments(audio_path, model_name)
            #else:
                st.info("🎤 Используем Whisper для высокого качества...")
                transcript = transcribe_with_whisper_segments(audio_path, model_name)

        # 2. Если Whisper не сработал, пробуем Speech Recognition
        if not transcript:
            st.info("🎤 Используем Speech Recognition...")
            transcript = transcribe_with_speech_recognition(audio_path)

        # 3. Если есть OpenAI API и файл небольшой
        if not transcript and is_ai_configured() and file_size_mb < 25:
            st.info("🎤 Используем OpenAI API...")
            transcript = transcribe_with_openai_api(audio_path)

        # Удаляем временный файл
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except:
                pass

        return transcript or "Не удалось создать транскрипцию"

    except Exception as e:
        st.error(f"Ошибка транскрипции: {e}")
        return None


def transcribe_video_safe(video_path, model_name="base"):
    """Безопасная транскрипция видео (для обратной совместимости)"""
    return transcribe_video_enhanced(video_path, model_name)


def generate_with_openai(prompt, content_type="both"):
    """Генерация контента через OpenAI"""
    try:
        if not is_ai_configured():
            return None, None

        config = get_ai_config()
        api_key = config.get('openai_api_key')
        model = config.get('openai_model', 'gpt-4o-mini')

        import openai
        openai.api_key = api_key

        if content_type == "title":
            system_prompt = """Создай привлекательное название для видео на основе описания.

ТРЕБОВАНИЯ:
- Максимум 60 символов
- Кликабельное и интригующее
- На русском языке
- Можно использовать эмодзи

Ответь ТОЛЬКО названием."""

        elif content_type == "description":
            system_prompt = """Создай краткое описание для видео на основе содержания.

ТРЕБОВАНИЯ:
- 2-3 предложения
- Максимум 200 символов
- На русском языке
- Можно использовать эмодзи

Ответь ТОЛЬКО описанием."""

        else:  # both
            system_prompt = """Создай название и описание для видео на основе содержания.

ТРЕБОВАНИЯ:
- Название: максимум 60 символов, кликабельное
- Описание: 2-3 предложения, максимум 200 символов
- На русском языке
- Можно использовать эмодзи

ФОРМАТ:
НАЗВАНИЕ: [название]
ОПИСАНИЕ: [описание]"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Содержание видео: {prompt}"}
        ]

        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            max_tokens=config.get('max_tokens', 150),
            temperature=config.get('temperature', 0.7)
        )

        if not response or not response.choices:
            return None, None

        content = response.choices[0].message.content.strip()

        if content_type == "title":
            return content, None
        elif content_type == "description":
            return None, content
        else:  # both
            lines = content.split('\n')
            title = ""
            description = ""

            for line in lines:
                if line.startswith('НАЗВАНИЕ:'):
                    title = line.replace('НАЗВАНИЕ:', '').strip()
                elif line.startswith('ОПИСАНИЕ:'):
                    description = line.replace('ОПИСАНИЕ:', '').strip()

            return title or None, description or None

    except Exception as e:
        print(f"Ошибка генерации OpenAI: {e}")
        return None, None


def process_video_with_ai(video_path):
    """Обрабатывает видео и создает транскрипцию"""
    try:
        config = get_ai_config()
        model_name = config.get('whisper_model', 'base')

        transcript = transcribe_video_enhanced(video_path, model_name)
        return transcript, None, None

    except Exception as e:
        st.error(f"Ошибка обработки видео: {e}")
        return None, None, None


def generate_content_from_transcript(transcript, content_type="both"):
    """Генерирует контент на основе транскрипции"""
    try:
        return generate_with_openai(transcript, content_type)
    except Exception as e:
        st.error(f"Ошибка генерации: {e}")
        return None, None


def show_ai_config():
    """Показывает настройки AI"""
    config = get_ai_config()

    st.markdown("### 🤖 Настройка ChatGPT")

    # Статус методов транскрипции
    st.subheader("🎵 Методы транскрипции")
    methods = check_transcription_methods()

    col1, col2 = st.columns(2)
    with col1:
        st.write("✅ Whisper" if methods['whisper'] else "❌ Whisper")
        st.write("✅ Speech Recognition" if methods['speech_recognition'] else "❌ Speech Recognition")
        st.write("✅ OpenAI API" if methods['openai_api'] else "❌ OpenAI API")

    with col2:
        st.write("✅ FFmpeg" if methods['ffmpeg'] else "❌ FFmpeg")
        st.write("✅ MoviePy" if methods['moviepy'] else "❌ MoviePy")

    if not any([methods['whisper'], methods['speech_recognition'], methods['openai_api']]):
        st.warning("⚠️ Нет доступных методов транскрипции")

        with st.expander("📦 Установка зависимостей", expanded=True):
            st.code("""
# Основной пакет для транскрипции
pip install openai-whisper

# Альтернативный метод
pip install SpeechRecognition pydub

# Для извлечения аудио
pip install moviepy

# Если проблемы с PyTorch
pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cpu
            """)

    st.divider()

    # Настройки OpenAI
    st.subheader("🔑 Настройки OpenAI")

    api_key = st.text_input(
        "API Key",
        value=config.get('openai_api_key', ''),
        type="password"
    )

    col1, col2 = st.columns(2)

    with col1:
        model = st.selectbox(
            "Модель GPT",
            ["gpt-4o-mini", "gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
            index=0 if config.get('openai_model') == 'gpt-4o-mini' else 1
        )

        max_tokens = st.number_input(
            "Максимум токенов",
            min_value=50, max_value=500,
            value=config.get('max_tokens', 150)
        )

    with col2:
        whisper_model = st.selectbox(
            "Модель Whisper",
            ["tiny", "base", "small", "medium", "large"],
            index=1
        )

        temperature = st.slider(
            "Креативность",
            min_value=0.0, max_value=1.0,
            value=config.get('temperature', 0.7)
        )

    # Кнопки управления
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔍 Тест подключения"):
            if api_key:
                with st.spinner("Проверяем..."):
                    if test_openai_connection(api_key, model):
                        st.success("✅ Подключение успешно!")

                        # Сохраняем настройки
                        config.update({
                            'openai_api_key': api_key,
                            'openai_model': model,
                            'whisper_model': whisper_model,
                            'max_tokens': max_tokens,
                            'temperature': temperature,
                            'authenticated': True
                        })

                        st.session_state.ai_config = config
                        save_ai_config(config)

                        st.session_state.show_openai_config = False
                        st.rerun()
                    else:
                        st.error("❌ Ошибка подключения")
            else:
                st.error("Введите API ключ")

    with col2:
        if st.button("💾 Сохранить"):
            config.update({
                'openai_api_key': api_key,
                'openai_model': model,
                'whisper_model': whisper_model,
                'max_tokens': max_tokens,
                'temperature': temperature
            })

            st.session_state.ai_config = config
            save_ai_config(config)
            st.success("Настройки сохранены")

    with col3:
        if st.button("❌ Закрыть"):
            st.session_state.show_openai_config = False
            st.rerun()


if __name__ == "__main__":
    # Тест функций
    config = load_ai_config()
    print("AI Assistant загружен успешно")