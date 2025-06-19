import json
import os
from typing import Dict, Any


class Config:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.data = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                return self.default_config()
        else:
            return self.default_config()

    def save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")

    def default_config(self) -> Dict[str, Any]:
        return {
            'youtube': {
                'enabled': False,
                'client_id': '',
                'client_secret': '',
                'default_category': 'Entertainment',
                'default_privacy': 'public'
            },
            'tiktok': {
                'enabled': False,
                'username': '',
                'password': '',
                'default_hashtags': '#fyp #viral'
            },
            'instagram': {
                'enabled': False,
                'username': '',
                'password': '',
                'default_hashtags': '#reels #viral'
            },
            'video_processing': {
                'auto_resize': True,
                'max_duration_tiktok': 60,
                'max_duration_instagram': 90,
                'target_quality': 'high'
            },
            'upload_settings': {
                'retry_attempts': 3,
                'delay_between_uploads': 5,
                'auto_cleanup': True
            }
        }

    def get(self, key: str, default=None):
        keys = key.split('.')
        data = self.data
        for k in keys:
            if isinstance(data, dict) and k in data:
                data = data[k]
            else:
                return default
        return data

    def set(self, key: str, value: Any):
        keys = key.split('.')
        data = self.data
        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]
        data[keys[-1]] = value
        self.save_config()

    def get_platform_config(self, platform: str) -> Dict[str, Any]:
        return self.data.get(platform, {})

    def is_platform_enabled(self, platform: str) -> bool:
        return self.get(f'{platform}.enabled', False)

    def get_credentials(self, platform: str) -> Dict[str, str]:
        platform_config = self.get_platform_config(platform)
        if platform == 'youtube':
            return {
                'client_id': platform_config.get('client_id', ''),
                'client_secret': platform_config.get('client_secret', '')
            }
        elif platform in ['tiktok', 'instagram']:
            return {
                'username': platform_config.get('username', ''),
                'password': platform_config.get('password', '')
            }
        return {}