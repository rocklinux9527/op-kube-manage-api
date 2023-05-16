from sql_app.db_play import model_create, model_update, model_updateId, model_delete
from sql_app.models import Users
from sqlalchemy.orm import sessionmaker
from sql_app.database import engine
from sqlalchemy import and_

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
from fastapi.encoders import jsonable_encoder
from tools.config import usersHeader
# 日志配置
from tools.config import setup_logging
import os
HERE = os.path.abspath(__file__)
HOME_DIR = os.path.split(os.path.split(HERE)[0])[0]
LOG_DIR = os.path.join(HOME_DIR, "logs")
def insert_db_users(username, password_hash):
    """
    1.新增入库参数
    :param ns_name:
    :param used:
    :return:
    """
    fildes = {
        "username": "username",
        "password_hash": "password_hash"
    }

    request_data = {
        "username": username,
        "password_hash": password_hash
    }
    return model_create(Users, request_data, fildes)

def delete_db_users(Id):

    """
    1.删除kube config 配置入库
    :param Id:
    :return:
    """
    return model_delete(Users, Id)


def updata_users(Id, username, password_hash):

    fildes = {
        "username": "username",
        "password_hash": "password_hash",

    }

    request_data = {
        "username": username,
        "password_hash": password_hash,
    }
    return model_updateId(Users, Id, request_data, fildes)



def query_users(page: int = 1, page_size: int = 10):


    """
    1.查询查询配置信息
    """
    session = SessionLocal()
    query = session.query(Users)
    try:
        data = query.limit(page_size).offset((page - 1) * page_size).all()
        total = query.count()
        return {"code": 20000, "total": total, "data": jsonable_encoder(data), "messages": "query success", "status": True,
                "columns": usersHeader}
    except Exception as e:
        setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=str(e))
        return {"code": 50000, "total": 0, "data": "query data failure", "messages": str(e), "status": True,
                "columns": usersHeader}
    finally:
        session.commit()
        session.close()

def query_users_name(username):
    session = SessionLocal()
    data = session.query(Users)
    if username:
        data = data.filter_by(username=username)
    try:
        return {"code": 20000, "total": len([i.to_dict for i in data]), "data": jsonable_encoder(data.all()),
                "messages": "query data success", "status": True, "columns": usersHeader}
    except Exception as e:
        print(e)
        session.commit()
        session.close()
        return {"code": 50000, "total": 0, "data": "", "messages": "query fail", "status": True, "columns": usersHeader}

