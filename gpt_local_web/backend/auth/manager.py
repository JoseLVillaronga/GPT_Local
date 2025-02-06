import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
from .models import TestUser

class TestUserManager:
    def __init__(self):
        self.users: Dict[str, TestUser] = {}
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        self.users_file = os.path.join(self.data_dir, 'test_users.json')
        os.makedirs(self.data_dir, exist_ok=True)
        self.load_users()

    def load_users(self):
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    users_data = json.load(f)
                    for api_key, user_data in users_data.items():
                        # Convertir las fechas de string a datetime
                        if isinstance(user_data.get('created_at'), str):
                            user_data['created_at'] = datetime.fromisoformat(user_data['created_at'])
                        if isinstance(user_data.get('last_active'), str):
                            user_data['last_active'] = datetime.fromisoformat(user_data['last_active'])
                        self.users[api_key] = TestUser(**user_data)
            except Exception as e:
                print(f"Error loading users: {e}")
                self.users = {}

    def save_users(self):
        try:
            users_data = {}
            for api_key, user in self.users.items():
                user_dict = user.dict()
                user_dict['config'] = user.config.dict()
                user_dict['created_at'] = user_dict['created_at'].isoformat()
                if user_dict.get('last_active'):
                    user_dict['last_active'] = user_dict['last_active'].isoformat()
                users_data[api_key] = user_dict

            with open(self.users_file, 'w') as f:
                json.dump(users_data, f, indent=2)
        except Exception as e:
            print(f"Error saving users: {e}")

    def create_test_user(self) -> TestUser:
        user = TestUser.create_test_user()
        self.users[user.api_key] = user
        self.save_users()
        return user

    def get_user(self, api_key: str) -> Optional[TestUser]:
        return self.users.get(api_key)

    def is_user_valid(self, api_key: str) -> bool:
        user = self.get_user(api_key)
        if not user:
            return False
        valid_until = user.created_at + timedelta(days=user.config.valid_days)
        return datetime.now(timezone.utc) < valid_until

    def update_user_activity(self, api_key: str):
        user = self.get_user(api_key)
        if user:
            user.last_active = datetime.now(timezone.utc)
            user.request_count += 1
            self.save_users()

    def get_requests_today(self, api_key: str) -> int:
        user = self.get_user(api_key)
        if not user:
            return 0
        return user.request_count

    def get_max_requests_per_day(self, api_key: str) -> int:
        user = self.get_user(api_key)
        if not user:
            return 0
        return user.config.max_requests_per_day
