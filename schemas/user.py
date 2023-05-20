from pydantic import BaseModel

class UserManager(BaseModel):
    """系统用户信息管理"""
    username: str
    password: str


class updateUserManager(BaseModel):
    """系统用户更新管理"""
    id: str
    username: str
    password: str

class deleteUser(BaseModel):
    id: int
    username: str
