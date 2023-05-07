from fastapi import FastAPI, HTTPException
from fastapi import Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from passlib.hash import ldap_salted_sha1

security = HTTPBasic()

def authenticate_user(username: str, password: str):
    """
    认证用户
    :param username: 用户名
    :param password: 密码
    :return: 如果用户认证成功，返回 True，否则返回 False
    """
    # 这里假设用户的用户名和密码已经保存在一个 dict 对象中了
    users = {
        "alice": ldap_salted_sha1.hash("alice_password"),
        "bob": ldap_salted_sha1.hash("bob_password"),
    }
    if username in users:
        # 验证密码
        if ldap_salted_sha1.verify(password, users[username]):
            return True
    return False

def login(credentials: HTTPBasicCredentials = Depends(security)):
    """
    用户登录验证，如果成功返回用户 token，否则返回 HTTP 401 错误
    """
    if not authenticate_user(credentials.username, credentials.password):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    # 这里生成一个随机字符串作为用户 token
    # 真实情况下应该使用更安全的 token 生成方式
    token = "a_random_token"
    return {"token": token}
