from sql_app.db_play import model_create, model_update, model_updateId, model_delete
from sql_app.models import DeployNsData
from sqlalchemy.orm import sessionmaker
from sql_app.database import engine
from sqlalchemy import and_

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
from fastapi.encoders import jsonable_encoder

# 日志配置
from tools.config import setup_logging
import os
HERE = os.path.abspath(__file__)
HOME_DIR = os.path.split(os.path.split(HERE)[0])[0]
LOG_DIR = os.path.join(HOME_DIR, "logs")
def insert_db_ns(env, cluster_name, ns_name, used):
    """
    1.新增入库参数
    :param ns_name:
    :param used:
    :return:
    """
    fildes = {
        "env": "env",
        "cluster_name": "cluster_name",
        "ns_name": "ns_name",
        "used": "used"
    }

    request_data = {
        "env": env,
        "cluster_name": cluster_name,
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


def query_ns(page: int = 1, page_size: int = 10):
    from tools.config import k8sNameSpaceHeader
    """
    1.查询查询配置信息
    """
    session = SessionLocal()
    query = session.query(DeployNsData)
    try:
        data = query.limit(page_size).offset((page - 1) * page_size).all()
        total = query.count()
        session.commit()
        session.close()
        return {"code": 0, "total": total, "data": jsonable_encoder(data), "messages": "query success", "status": True,
                "columns": k8sNameSpaceHeader}
    except Exception as e:
        setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=str(e))
        return {"code": 0, "total": 0, "data": "query data failure", "messages": str(e), "status": True,
                "columns": k8sNameSpaceHeader}


def query_ns_any(env_name, cluster_name, namespace_name):
    from tools.config import k8sNameSpaceHeader
    """
    1.查询查询配置信息
    """
    session = SessionLocal()
    data = session.query(DeployNsData)
    results = data.filter(and_(DeployNsData.env == env_name, DeployNsData.cluster_name == cluster_name,
                               DeployNsData.ns_name == namespace_name)).all()
    if not env_name and cluster_name and results:
        session.close()
        return {"code": 1, "data": "", "status": False}
    else:
        session.close()
        return {"code": 0, "data": [i.to_dict for i in results], "status": True, "columns": k8sNameSpaceHeader}
