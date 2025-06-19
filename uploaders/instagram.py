import time
import os
from instagrapi import Client
from instagrapi.exceptions import LoginRequired
from instagrapi.types import StoryMention, StoryMedia, StoryLink, StoryHashtag


class InstagramUploader:
    def __init__(self):
        self.client = Client()
        self.session_file = 'credentials/instagram_session.json'
        os.makedirs('credentials', exist_ok=True)

    def login(self, username, password):
        try:
            try:
                if os.path.exists(self.session_file):
                    self.client.load_settings(self.session_file)
                    self.client.login(username, password)
                    print("Instagram: Using saved session")
                else:
                    self.client.login(username, password)
                    self.client.dump_settings(self.session_file)
                    print("Instagram: New login successful")
            except:
                self.client.login(username, password)
                self.client.dump_settings(self.session_file)
                print("Instagram: Fresh login successful")

            return True

        except Exception as e:
            print(f"Instagram login error: {e}")
            return False

    def upload(self, video_path, caption, hashtags=""):
        try:
            full_caption = f"{caption}\n\n{hashtags}" if hashtags else caption

            media = self.client.clip_upload(
                video_path,
                caption=full_caption
            )

            return media.pk if media else None

        except LoginRequired:
            print("Instagram: Login required")
            return None
        except Exception as e:
            print(f"Instagram upload error: {e}")
            return None

    def upload_story(self, file_path, text=None, hashtags=None, mentions=None, links=None):
        try:
            extra_data = {}

            # Добавляем текст если указан
            if text:
                extra_data['text'] = text

            # Добавляем хештеги
            if hashtags:
                story_hashtags = []
                hashtag_list = [tag.strip().replace('#', '') for tag in hashtags.split('#') if tag.strip()]

                for i, hashtag in enumerate(hashtag_list[:5]):  # Максимум 5 хештегов
                    story_hashtag = StoryHashtag(
                        hashtag=hashtag,
                        x=0.5,  # Центр по горизонтали
                        y=0.8 + (i * 0.03),  # Снизу, с отступом
                        width=0.3,
                        height=0.05
                    )
                    story_hashtags.append(story_hashtag)

                if story_hashtags:
                    extra_data['hashtags'] = story_hashtags

            # Добавляем упоминания
            if mentions:
                story_mentions = []
                mention_list = [mention.strip().replace('@', '') for mention in mentions.split('@') if mention.strip()]

                for i, mention in enumerate(mention_list[:3]):  # Максимум 3 упоминания
                    try:
                        user = self.client.user_info_by_username(mention)
                        story_mention = StoryMention(
                            user=user,
                            x=0.5,
                            y=0.1 + (i * 0.05),  # Сверху
                            width=0.4,
                            height=0.06
                        )
                        story_mentions.append(story_mention)
                    except:
                        print(f"Пользователь @{mention} не найден")

                if story_mentions:
                    extra_data['mentions'] = story_mentions

            # Добавляем ссылки (только для верифицированных аккаунтов или бизнес-аккаунтов)
            if links:
                link_list = [link.strip() for link in links.split('\n') if link.strip()]
                if link_list:
                    try:
                        story_link = StoryLink(
                            webUri=link_list[0],  # Только одна ссылка
                            x=0.5,
                            y=0.9,
                            width=0.8,
                            height=0.08
                        )
                        extra_data['links'] = [story_link]
                    except:
                        print("Не удалось добавить ссылку (возможно, аккаунт не верифицирован)")

            # Загружаем в зависимости от типа файла
            if file_path.lower().endswith(('.mp4', '.mov', '.avi')):
                media = self.client.video_upload_to_story(file_path, **extra_data)
            else:
                media = self.client.photo_upload_to_story(file_path, **extra_data)

            return media.pk if media else None

        except Exception as e:
            print(f"Instagram story upload error: {e}")
            return None

    def upload_story_with_stickers(self, file_path, story_config=None):
        """
        Загрузка сторис с расширенными настройками
        story_config = {
            'text': 'Текст на сторис',
            'hashtags': '#стрим #игры #live',
            'mentions': '@username1 @username2',
            'links': 'https://twitch.tv/username',
            'location': 'Moscow, Russia',  # Геолокация
            'music': 'track_id',  # ID трека (сложно получить)
            'poll': {'question': 'Вопрос?', 'options': ['Да', 'Нет']},  # Опрос
            'quiz': {'question': 'Вопрос?', 'options': ['A', 'B', 'C'], 'correct': 0}  # Викторина
        }
        """
        try:
            if not story_config:
                return self.upload_story(file_path)

            extra_data = {}

            # Базовые элементы
            if story_config.get('text'):
                extra_data['text'] = story_config['text']

            # Хештеги
            if story_config.get('hashtags'):
                hashtags = story_config['hashtags']
                story_hashtags = []
                hashtag_list = [tag.strip().replace('#', '') for tag in hashtags.split('#') if tag.strip()]

                for i, hashtag in enumerate(hashtag_list[:5]):
                    story_hashtag = StoryHashtag(
                        hashtag=hashtag,
                        x=0.5,
                        y=0.8 + (i * 0.03),
                        width=0.3,
                        height=0.05
                    )
                    story_hashtags.append(story_hashtag)

                if story_hashtags:
                    extra_data['hashtags'] = story_hashtags

            # Упоминания
            if story_config.get('mentions'):
                mentions = story_config['mentions']
                story_mentions = []
                mention_list = [mention.strip().replace('@', '') for mention in mentions.split('@') if mention.strip()]

                for i, mention in enumerate(mention_list[:3]):
                    try:
                        user = self.client.user_info_by_username(mention)
                        story_mention = StoryMention(
                            user=user,
                            x=0.5,
                            y=0.1 + (i * 0.05),
                            width=0.4,
                            height=0.06
                        )
                        story_mentions.append(story_mention)
                    except:
                        print(f"Пользователь @{mention} не найден")

                if story_mentions:
                    extra_data['mentions'] = story_mentions

            # Ссылки
            if story_config.get('links'):
                links = story_config['links']
                try:
                    story_link = StoryLink(
                        webUri=links,
                        x=0.5,
                        y=0.9,
                        width=0.8,
                        height=0.08
                    )
                    extra_data['links'] = [story_link]
                except:
                    print("Не удалось добавить ссылку")

            # Геолокация
            if story_config.get('location'):
                try:
                    locations = self.client.location_search(story_config['location'])
                    if locations:
                        extra_data['location'] = locations[0]
                except:
                    print("Не удалось найти локацию")

            # Загружаем файл
            if file_path.lower().endswith(('.mp4', '.mov', '.avi')):
                media = self.client.video_upload_to_story(file_path, **extra_data)
            else:
                media = self.client.photo_upload_to_story(file_path, **extra_data)

            return media.pk if media else None

        except Exception as e:
            print(f"Instagram story with stickers upload error: {e}")
            return None

    def upload_photo_story(self, image_path, text=None):
        try:
            if text:
                media = self.client.photo_upload_to_story(
                    image_path,
                    text=text
                )
            else:
                media = self.client.photo_upload_to_story(image_path)

            return media.pk if media else None

        except Exception as e:
            print(f"Instagram photo story upload error: {e}")
            return None

    def upload_video_story(self, video_path):
        try:
            media = self.client.video_upload_to_story(video_path)
            return media.pk if media else None

        except Exception as e:
            print(f"Instagram video story upload error: {e}")
            return None