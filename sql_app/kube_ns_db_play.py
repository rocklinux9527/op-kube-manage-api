from sql_app.db_play import model_create, model_update, model_updateId, model_delete
from sql_app.models import DeployNsData
from sqlalchemy.orm import sessionmaker
from sql_app.database import engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def insert_db_ns(ns_name, used):
    """
    1.新增入库参数
    :param ns_name:
    :param used:
    :return:
    """
    fildes = {
        "ns_name": "ns_name",
        "used": "used"
    }

    request_data = {
        "ns_name": ns_name,
        "used": used
    }
    return model_create(DeployNsData, request_data, fildes)


def delete_db_ns(Id):
    """
    1.删除kube config 配置入库
    :param Id:
    :return:
    """
    return model_delete(DeployNsData, Id)


def query_ns():
    """
    1.查询查询配置信息
    """
    session = SessionLocal()
    data = session.query(DeployNsData)
    session.commit()
    session.close()
    return {"code": 0, "data": [i.to_dict for i in data], "messages": "query success", "status": True}
