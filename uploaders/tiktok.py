import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import random
import atexit


class TikTokDriverManager:
    _instance = None
    _driver = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_driver(self):
        if self._driver is None:
            self._driver = self._create_driver()
            if self._driver:
                atexit.register(self.close_driver)
        return self._driver

    def _create_driver(self):
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option("detach", True)

        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        ]
        options.add_argument(f'--user-agent={random.choice(user_agents)}')

        user_data_dir = os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data")
        tiktok_profile = os.path.join(os.getcwd(), "tiktok_profile")

        if os.path.exists(user_data_dir):
            try:
                options.add_argument(f'--user-data-dir={user_data_dir}')
                options.add_argument('--profile-directory=Default')
                print(f"Попытка использовать основной профиль: {user_data_dir}")
            except:
                options.add_argument(f'--user-data-dir={tiktok_profile}')
                print(f"Переключение на отдельный профиль: {tiktok_profile}")
        else:
            options.add_argument(f'--user-data-dir={tiktok_profile}')
            print(f"Создание нового профиля: {tiktok_profile}")

        try:
            driver = webdriver.Chrome(options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.execute_script("window.navigator.chrome = {runtime: {}};")
            driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});")
            print("TikTok драйвер создан успешно")
            return driver
        except WebDriverException as e:
            if "user data directory is already in use" in str(e):
                print("Основной профиль занят, создаем отдельный...")
                options = Options()
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option('useAutomationExtension', False)
                options.add_experimental_option("detach", True)
                options.add_argument(f'--user-agent={random.choice(user_agents)}')
                options.add_argument(f'--user-data-dir={tiktok_profile}')

                try:
                    driver = webdriver.Chrome(options=options)
                    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                    print("TikTok драйвер создан с отдельным профилем")
                    return driver
                except Exception as e2:
                    print(f"Ошибка создания драйвера с отдельным профилем: {e2}")
                    return None
            else:
                print(f"Ошибка создания драйвера: {e}")
                return None

    def close_driver(self):
        if self._driver:
            try:
                self._driver.quit()
                print("TikTok драйвер закрыт")
            except:
                pass
            self._driver = None

    def restart_driver(self):
        self.close_driver()
        self._driver = self._create_driver()
        return self._driver


class TikTokUploader:
    def __init__(self):
        self.driver_manager = TikTokDriverManager()
        self.logged_in = False

    @property
    def driver(self):
        return self.driver_manager.get_driver()

    def login(self, username="", password=""):
        driver = self.driver
        if not driver:
            print("Не удалось создать драйвер")
            return False

        try:
            print("Переходим на TikTok...")
            driver.get('https://www.tiktok.com/')
            time.sleep(5)

            if self._check_logged_in():
                print("Уже залогинены в TikTok!")
                self.logged_in = True
                return True

            print("Не залогинены, начинаем процесс входа...")

            try:
                driver.get('https://www.tiktok.com/login')
                time.sleep(3)
                print("Перешли на страницу входа")
            except Exception as e:
                print(f"Ошибка перехода на страницу входа: {e}")
                return False

            print("📱 Пожалуйста, войдите в аккаунт в открывшемся браузере")
            print("Можете использовать QR код, email/пароль или любой другой способ")

            for i in range(60):
                time.sleep(2)

                if self._check_logged_in():
                    print(f"✅ Успешный вход через {i * 2 + 2} секунд!")
                    self.logged_in = True

                    time.sleep(3)
                    return True

                if i % 10 == 0:
                    print(f"⏳ Ожидание входа... {i * 2}/120 секунд")

                if i == 20 and username and password:
                    print("Пробуем автоматический ввод логина/пароля...")
                    try:
                        self._try_email_login(username, password)
                        time.sleep(5)
                    except Exception as e:
                        print(f"Ошибка автоввода: {e}")

            print("❌ Время ожидания входа истекло (2 минуты)")
            return False

        except Exception as e:
            print(f"Ошибка при входе в TikTok: {e}")
            return False

    def _check_logged_in(self):
        try:
            driver = self.driver
            if not driver:
                return False

            current_url = driver.current_url
            print(f"Текущий URL: {current_url}")

            if any(path in current_url for path in ['/login', '/signup']):
                print("Находимся на странице входа - не залогинены")
                return False

            try:
                avatar_selectors = [
                    "//img[contains(@class, 'avatar')]",
                    "//div[contains(@class, 'avatar')]",
                    "//span[contains(@class, 'avatar')]",
                    "//*[@data-e2e='nav-profile']",
                    "//a[contains(@href, '/@')]",
                    "//div[contains(@class, 'DivHeaderRight')]//img"
                ]

                for selector in avatar_selectors:
                    try:
                        elements = driver.find_elements(By.XPATH, selector)
                        if elements:
                            print(f"Найден элемент аватара: {selector}")
                            return True
                    except:
                        continue

                upload_selectors = [
                    "//a[contains(@href, '/upload')]",
                    "//*[contains(text(), 'Upload')]",
                    "//button[contains(@class, 'upload')]",
                    "//*[@data-e2e='nav-upload']"
                ]

                for selector in upload_selectors:
                    try:
                        elements = driver.find_elements(By.XPATH, selector)
                        if elements:
                            print(f"Найдена кнопка загрузки: {selector}")
                            return True
                    except:
                        continue

                profile_selectors = [
                    "//a[contains(text(), 'Profile')]",
                    "//*[contains(text(), 'Профиль')]",
                    "//*[@data-e2e='profile-icon']"
                ]

                for selector in profile_selectors:
                    try:
                        elements = driver.find_elements(By.XPATH, selector)
                        if elements:
                            print(f"Найден элемент профиля: {selector}")
                            return True
                    except:
                        continue

                try:
                    page_source = driver.page_source.lower()

                    login_indicators = ['log in', 'sign up', 'create account', 'войти', 'регистрация']
                    logout_indicators = ['log out', 'logout', 'выйти']

                    has_login = any(indicator in page_source for indicator in login_indicators)
                    has_logout = any(indicator in page_source for indicator in logout_indicators)

                    if has_logout and not has_login:
                        print("Найден индикатор выхода - залогинены")
                        return True
                    elif has_login and not has_logout:
                        print("Найден только индикатор входа - не залогинены")
                        return False

                except:
                    pass

            except Exception as e:
                print(f"Ошибка при поиске элементов авторизации: {e}")

            print("Не удалось определить статус авторизации")
            return False

        except Exception as e:
            print(f"Ошибка проверки входа: {e}")
            return False

    def _try_email_login(self, username, password):
        driver = self.driver

        try:
            email_options = driver.find_elements(By.XPATH,
                                                 "//div[contains(text(), 'phone') or contains(text(), 'email')] | " +
                                                 "//a[contains(text(), 'email') or contains(text(), 'Email')]")

            if email_options:
                email_options[0].click()
                time.sleep(2)

            email_tabs = driver.find_elements(By.XPATH,
                                              "//a[contains(text(), 'Email')] | //div[contains(text(), 'Email')]")

            if email_tabs:
                email_tabs[0].click()
                time.sleep(2)

            username_fields = driver.find_elements(By.XPATH, "//input[@type='text' or @type='email']")
            password_fields = driver.find_elements(By.XPATH, "//input[@type='password']")

            if username_fields and password_fields:
                self._human_type(username_fields[0], username)
                time.sleep(1)
                self._human_type(password_fields[0], password)
                time.sleep(1)

                submit_buttons = driver.find_elements(By.XPATH,
                                                      "//button[@type='submit'] | //button[contains(text(), 'Log in')]")

                if submit_buttons:
                    submit_buttons[0].click()
                else:
                    password_fields[0].send_keys(Keys.ENTER)

                print("Отправлены данные для входа")
        except Exception as e:
            print(f"Ошибка автоматического ввода: {e}")

    def _clean_text_for_chrome(self, text):
        import re
        emoji_pattern = re.compile("["
                                   u"\U0001F600-\U0001F64F"
                                   u"\U0001F300-\U0001F5FF"
                                   u"\U0001F680-\U0001F6FF"
                                   u"\U0001F1E0-\U0001F1FF"
                                   u"\U00002702-\U000027B0"
                                   u"\U000024C2-\U0001F251"
                                   "]+", flags=re.UNICODE)
        clean_text = emoji_pattern.sub(r'', text)

        clean_text = clean_text.replace('🔥', '').replace('👍', '').replace('📱', '')
        clean_text = clean_text.replace('💡', '').replace('🎉', '').replace('⚠️', '')

        clean_text = re.sub(r'\s+', ' ', clean_text)
        clean_text = clean_text.strip()

        return clean_text

    def _human_type_advanced(self, element, text):
        try:
            element.send_keys("")
            time.sleep(0.2)

            driver = self.driver
            driver.execute_script("arguments[0].focus();", element)
            time.sleep(0.3)

            lines = text.split('\n')
            for i, line in enumerate(lines):
                if i > 0:
                    element.send_keys(Keys.ENTER)
                    time.sleep(0.1)

                for char in line:
                    element.send_keys(char)
                    time.sleep(random.uniform(0.03, 0.08))

            driver.execute_script("arguments[0].blur();", element)
            time.sleep(0.2)
            driver.execute_script("arguments[0].focus();", element)

        except Exception as e:
            print(f"Ошибка продвинутого ввода: {e}")
            try:
                element.send_keys(text)
            except:
                driver = self.driver
                driver.execute_script("arguments[0].value = arguments[1];", element, text)

    def _human_type(self, element, text):
        element.clear()
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))

    def prepare_for_upload(self, video_path, caption, hashtags=""):
        print(f"🎬 TikTok Upload подготовка:")
        print(f"   Video: {video_path}")
        print(f"   Caption: {caption}")
        print(f"   Hashtags: {hashtags}")
        driver = self.driver
        if not driver:
            raise Exception("Драйвер не инициализирован")

        if not self._check_logged_in():
            raise Exception("Не залогинены в TikTok. Выполните авторизацию заново.")

        try:
            print("📤 Переходим на TikTok Studio...")
            driver.get('https://www.tiktok.com/tiktokstudio/upload')
            time.sleep(5)

            if 'login' in driver.current_url.lower():
                print("Перенаправлены на страницу входа, пробуем альтернативный URL...")
                driver.get('https://www.tiktok.com/creator-center/upload')
                time.sleep(5)

            print("🔍 Ищем поле загрузки файла...")

            file_input_selectors = [
                "//input[@type='file']",
                "//input[@accept*='video']",
                "//input[contains(@accept, 'mp4')]",
                "//input[contains(@class, 'upload')]"
            ]

            file_input = None
            for selector in file_input_selectors:
                try:
                    file_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    print(f"Найдено поле загрузки: {selector}")
                    break
                except:
                    continue

            if not file_input:
                print("Ищем область для загрузки...")
                upload_areas = driver.find_elements(By.XPATH,
                                                    "//div[contains(text(), 'Select file') or contains(text(), 'Выберите') or contains(text(), 'Upload')] | " +
                                                    "//button[contains(text(), 'Select file') or contains(text(), 'Upload')]")

                if upload_areas:
                    upload_areas[0].click()
                    time.sleep(3)
                    file_input = driver.find_element(By.XPATH, "//input[@type='file']")

            if file_input:
                abs_path = os.path.abspath(video_path)
                print(f"Загружаем файл: {abs_path}")
                file_input.send_keys(abs_path)
                print("✅ Файл отправлен на загрузку")

                print("⏳ Ждем завершения загрузки и обработки видео...")
                time.sleep(20)

                print("📝 Ищем поле для описания...")
                try:
                    caption_selectors = [
                        "//div[@contenteditable='true' and @data-placeholder]",
                        "//div[@contenteditable='true']",
                        "//textarea[contains(@placeholder, 'describe') or contains(@placeholder, 'Describe')]",
                        "//div[@role='textbox']",
                        "//textarea[@aria-label='Description']",
                        "//div[contains(@class, 'DraftEditor-editorContainer')]//div[@contenteditable='true']",
                        "//div[contains(@class, 'editor')]//div[@contenteditable='true']"
                    ]

                    caption_area = None
                    for selector in caption_selectors:
                        try:
                            elements = driver.find_elements(By.XPATH, selector)
                            for element in elements:
                                if element.is_displayed():
                                    caption_area = element
                                    print(f"Найдено поле описания: {selector}")
                                    break
                            if caption_area:
                                break
                        except:
                            continue

                    if caption_area:
                        full_caption = f"{caption}"

                        print(f"📝 Вводим полный текст: {full_caption}")

                        driver.execute_script("arguments[0].focus();", caption_area)
                        time.sleep(1)

                        driver.execute_script("arguments[0].click();", caption_area)
                        time.sleep(1)

                        try:
                            caption_area.clear()
                        except:
                            pass

                        driver.execute_script("""
                            arguments[0].innerHTML = '';
                            arguments[0].innerText = '';
                            arguments[0].textContent = '';
                        """, caption_area)
                        time.sleep(1)

                        driver.execute_script("arguments[0].click();", caption_area)
                        time.sleep(0.5)

                        self._human_type_advanced(caption_area, full_caption)
                        print("✅ Описание введено")
                        time.sleep(3)

                        print("🔓 Поле описания разблокировано для редактирования")
                        driver.execute_script("""
                            arguments[0].style.border = '2px solid green';
                            arguments[0].style.backgroundColor = '#f0fff0';
                        """, caption_area)

                    else:
                        print("⚠️ Поле описания не найдено")

                except Exception as e:
                    print(f"⚠️ Ошибка ввода описания: {e}")

                print("🎯 Все поля заполнены! Кнопка публикации готова для ручного нажатия.")
                print("👆 Теперь вы можете нажать кнопку 'Post' самостоятельно в браузере.")
                print("✏️ Поле описания также доступно для редактирования.")
                print("🔍 Ищем кнопку публикации для подсветки...")

                try:
                    all_text_areas = driver.find_elements(By.XPATH, "//div[@contenteditable='true'] | //textarea")
                    for area in all_text_areas:
                        if area.is_displayed():
                            driver.execute_script("""
                                arguments[0].removeAttribute('readonly');
                                arguments[0].removeAttribute('disabled');
                                arguments[0].style.pointerEvents = 'auto';
                                arguments[0].contentEditable = 'true';
                            """, area)
                    print("🔓 Все текстовые поля разблокированы для редактирования")
                except Exception as e:
                    print(f"Предупреждение при разблокировке полей: {e}")

                time.sleep(1)

                publish_selectors = [
                    "//button[text()='Post']",
                    "//button[contains(text(), 'Post')]",
                    "//button[text()='Publish']",
                    "//button[contains(text(), 'Publish')]",
                    "//button[contains(text(), 'Опубликовать')]",
                    "//div[contains(@class, 'post-btn')]//button",
                    "//button[@data-e2e='post-btn']",
                    "//button[contains(@class, 'btn-post')]",
                    "//*[@role='button' and contains(text(), 'Post')]"
                ]

                publish_button = None
                for selector in publish_selectors:
                    try:
                        elements = driver.find_elements(By.XPATH, selector)
                        for element in elements:
                            if element.is_displayed() and element.is_enabled():
                                publish_button = element
                                print(f"✅ Найдена кнопка публикации: {selector}")

                                driver.execute_script("arguments[0].scrollIntoView(true);", publish_button)
                                driver.execute_script("""
                                    arguments[0].style.border = '3px solid red';
                                    arguments[0].style.backgroundColor = '#ffcccc';
                                """, publish_button)
                                print("🔴 Кнопка публикации подсвечена красным!")
                                break
                        if publish_button:
                            break
                    except Exception as e:
                        continue

                if not publish_button:
                    print("⚠️ Кнопка публикации не найдена для подсветки")
                    print("Попробуйте найти и нажать кнопку 'Post' вручную")

                return True
            else:
                print("❌ Не найдено поле загрузки файла")
                return False

        except TimeoutException as e:
            print(f"⏰ Таймаут при загрузке в TikTok: {e}")
            return False
        except Exception as e:
            print(f"❌ Ошибка загрузки в TikTok: {e}")
            return False

    def upload(self, video_path, caption, hashtags=""):
        return self.prepare_for_upload(video_path, caption, hashtags)

    def close(self):
        self.logged_in = False
        print("TikTok uploader завершен (браузер остается открытым)")

    def restart_browser(self):
        print("🔄 Перезапуск браузера TikTok...")
        return self.driver_manager.restart_driver()

    @staticmethod
    def close_browser():
        manager = TikTokDriverManager()
        manager.close_driver()
        print("🚪 Браузер TikTok закрыт")