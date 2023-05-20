import datetime
import json

import jwt
from passlib.hash import ldap_salted_sha1
from sqlalchemy.orm import sessionmaker

from sql_app.database import engine
from sql_app.login_users import insert_db_users, delete_db_users, query_users_name, updata_users
from sql_app.models import Users
from sql_app.ops_log_db_play import insert_ops_bot_log

# JWT 密钥  # JWT 加密算法
JWT_SECRET_KEY = 'op-kube-manager-api-jwt'
JWT_ALGORITHM = 'HS256'

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class UserService():
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    def authenticate_user_test(self):
        """
        认证用户
        :param username: 用户名
        :param password: 密码
        :return: 如果用户认证成功，返回 True，否则返回 False
        """
        users = {
            "admin": ldap_salted_sha1.hash("111111"),
            "alice": ldap_salted_sha1.hash("alice_password"),
            "bob": ldap_salted_sha1.hash("bob_password"),
        }
        if self.username in users:
            if ldap_salted_sha1.verify(self, password, users[self.username]):
                return True
        return False

    def authenticate_db_user(self):
        """
        数据库认证用户
        :param username: 用户名
        :param password: 密码
        :return: 如果用户认证成功，返回 True，否则返回 False
        """
        session = SessionLocal()
        user = session.query(Users).filter(Users.username == self.username).first()
        if user:
            if ldap_salted_sha1.verify(self.password, user.password_hash):
                return True
        return False

    def login_auth(self):
        """
        1.验证用户名称
        2.定制 token 返回结构信息
        3.返回成功信息及 token
        Returns:

        """
        try:
            expires = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
            payload = {'username': self.username, 'exp': expires}
            header = {
                "alg": "HS256",
                "typ": "JWT"
            }
            token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM, headers=header)

            data = {
                'username': self.username,
                'code': 20000,
                'message': 'Login {uid} User Success'.format(uid=self.username),
                'data': {
                    'token': token,
                    'token_type': 'Bearer'
                }
            }
        except Exception as e:
            data = {
                'username': self.username,
                'code': 50000,
                'message': str(e),
                'data': {
                    'token': "",
                    'token_type': 'Bearer'
                }
            }
        return data

    @staticmethod
    def logout_msg():
        """
        1.定义需要模拟数据结构
        Returns:

        """
        data = {
            'code': 20000,
            'message': 'Logged out successfully!',
            'data': {},
        }
        return data

    @staticmethod
    def protected_token(token):
        """
         1.验证 JWT token，如果验证成功，返回用户名
         2.token 过期 和 token失败
        """
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            username = payload.get('username')
            if username:
                data = {
                    'code': 20000,
                    'message': 'Login User Success',
                    'data': {
                        "roles": ["admin"],
                        "name": "Super Admin",
                        'avatar': 'https://wpimg.wallstcn.com/f778738c-e4f8-4870-b634-56703b4acafe.gif',
                        "introduction": "I am a super administrator",
                    }
                }
                return data
            else:
                data = {
                    'code': 50000,
                    'message': 'Invalid token',
                    'data': {
                        "roles": "",
                        "name": "",
                        'avatar': "",
                        "introduction": "",
                    }
                }
            return data
        except jwt.ExpiredSignatureError:

            data = {
                'code': 50000,
                'message': 'Token expired',
                'data': {
                    "roles": "",
                    "name": "",
                    'avatar': "",
                    "introduction": "",
                }
            }
        except Exception as e:
            data = {
                'code': 50000,
                'message': str(e),
                'data': {
                    "roles": "",
                    "name": "",
                    'avatar': "",
                    "introduction": "",
                }
            }
        return data

    def add_user(self, user_request_data):
        """1.查询用户在添加用户"""
        result_username = query_users_name(self.username)
        if result_username.get("code") == 20000 and result_username.get("data"):
            data = {
                'code': 50000,
                'message': f"User {self.username} already exists,禁止重复用户",
                'data': ""
            }
            return data
        password_hash = ldap_salted_sha1.hash(self.password)
        created_user = insert_db_users(
            username=self.username,
            password_hash=password_hash
        )
        if created_user.get("code") == 20000:
            insert_ops_bot_log("Insert db user success ", json.dumps(user_request_data), "post",
                               json.dumps(created_user))
            return created_user
        else:
            return created_user

    def delete_user(self, Id, user_request_data):
        """1.查询用户存在即可删除 不存在不需要删除"""
        result_username = query_users_name(self.username)
        if not result_username.get("data"):
            data = {
                'code': 50000,
                'message': f"User {self.username} not exists already,删除失败",
                'data': ""
            }
            return data
        delete_instance = delete_db_users(Id)
        if delete_instance.get("code") == 20000:
            insert_ops_bot_log("Delete Users App", json.dumps(user_request_data), "delete",
                               json.dumps(delete_instance))
            return delete_instance
        else:
            return delete_instance

    def update_user(self, Id, user_request_data):
        """1.用户存在在更新不存在就返回 """
        result_username = query_users_name(self.username)
        if not result_username.get("data"):
            data = {
                'code': 50000,
                'message': f"User {self.username} not exists already, 更新失败",
                'data': ""
            }
            return data
        new_password = self.password
        password_hash = ldap_salted_sha1.hash(new_password)
        result = updata_users(Id, self.username, password_hash)
        if result.get("code") == 20000:
            insert_ops_bot_log("Update user success", json.dumps(user_request_data), "post", json.dumps(result))
            return result
        else:
            return {"code": 1, "messages": "update users failure", "status": True, "data": "failure"}
