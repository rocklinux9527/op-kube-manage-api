from sql_app.db_play import model_create, model_update, model_updateId, model_delete
from sql_app.models import Template
from sqlalchemy.orm import sessionmaker
from sql_app.database import engine
from sqlalchemy import and_

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
from fastapi.encoders import jsonable_encoder
from tools.config import templateHeader
# 日志配置
from tools.config import setup_logging
import os
HERE = os.path.abspath(__file__)
HOME_DIR = os.path.split(os.path.split(HERE)[0])[0]
LOG_DIR = os.path.join(HOME_DIR, "logs")

def insert_db_template(name, t_type, content, language, remark):
    """
    1.新增入库参数
    :param ns_name:
    :param used:
    :return:
    """
    fildes = {
        "name": "name",
        "t_type": "t_type",
        "content": "content",
        "language": "language",
        "remark": "remark"
    }

    request_data = {
        "name": name,
        "t_type": t_type,
        "content": content,
        "language": language,
        "remark": remark
    }
    return model_create(Template, request_data, fildes)

def delete_db_template(Id):

    """
    1.删除kube config 配置入库
    :param Id:
    :return:
    """
    return model_delete(Template, Id)


def updata_template(Id, name, t_type, content, language, remark):
    fildes = {
        "name": "name",
        "t_type": "t_type",
        "content": "content",
        "language": "language",
        "remark": "remark"
    }

    request_data = {
        "name": name,
        "t_type": t_type,
        "content": content,
        "language": language,
        "remark": remark
    }
    return model_updateId(Template, Id, request_data, fildes)

def query_template(page: int = 1, page_size: int = 10):
    """
    1.查询查询配置信息
    """
    session = SessionLocal()
    query = session.query(Template)
    try:
        data = query.limit(page_size).offset((page - 1) * page_size).all()
        total = query.count()
        return {"code": 20000, "total": total, "data": jsonable_encoder(data), "messages": "query success", "status": True,
                "columns": templateHeader}
    except Exception as e:
        setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=str(e))
        return {"code": 50000, "total": 0, "data": "query data failure", "messages": str(e), "status": True,
                "columns": templateHeader}
    finally:
        session.commit()
        session.close()

def query_Template_name(name):
    session = SessionLocal()
    data = session.query(Template)
    if name:
        data = data.filter_by(name=name)
    try:
        return {"code": 20000, "total": len([i.to_dict for i in data]), "data": jsonable_encoder(data.all()),
                "messages": "query data success", "status": True, "columns": templateHeader}
    except Exception as e:
        print(e)
        session.commit()
        session.close()
        return {"code": 50000, "total": 0, "data": "", "messages": "query fail", "status": True, "columns": templateHeader}

