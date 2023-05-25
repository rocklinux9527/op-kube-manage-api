from sql_app.db_play import model_create, model_update, model_updateId, model_delete
from sql_app.models import KubeK8sConfig
from sqlalchemy.orm import sessionmaker
from sql_app.database import engine
from sqlalchemy import and_
from typing import Optional
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from tools.config import setup_logging
import os
HERE = os.path.abspath(__file__)
HOME_DIR = os.path.split(os.path.split(HERE)[0])[0]
LOG_DIR = os.path.join(HOME_DIR, "logs")


def insert_kube_config(env, cluster_name, server_address, ca_data, client_crt_data, client_key_data, client_key_path):
    """
    1.新增入库参数
    :param env:
    :param cluster_name:
    :param server_address:
    :param ca_data:
    :param client_crt_data:
    :param client_key_data:
    :return:
    """
    fildes = {
        "env": "env",
        "cluster_name": "cluster_name",
        "server_address": "server_address",
        "ca_data": "ca_data",
        "client_crt_data": "client_crt_data",
        "client_key_data": "client_key_data",
        "client_key_path": "client_key_path"
    }

    request_data = {
        "env": env,
        "cluster_name": cluster_name,
        "server_address": server_address,
        "ca_data": ca_data,
        "client_crt_data": client_crt_data,
        "client_key_data": client_key_data,
        "client_key_path": client_key_path
    }
    return model_create(KubeK8sConfig, request_data, fildes)


def updata_kube_config(Id, env, cluster_name, server_address, ca_data, client_crt_data, client_key_data,
                       client_key_path):
    """
    1.修改kube config 配置入库
    :param Id:
    :param group:
    :param username:
    :param nickname:
    :param iphone:
    :param is_leader:
    :return:
    """
    fildes = {
        "env": "env",
        "cluster_name": "cluster_name",
        "server_address": "server_address",
        "ca_data": "ca_data",
        "client_crt_data": "client_crt_data",
        "client_key_data": "client_key_data",
        "client_key_path": "client_key_path"
    }

    request_data = {
        "env": env,
        "cluster_name": cluster_name,
        "server_address": server_address,
        "ca_data": ca_data,
        "client_crt_data": client_crt_data,
        "client_key_data": client_key_data,
        "client_key_path": client_key_path
    }
    return model_updateId(KubeK8sConfig, Id, request_data, fildes)


def delete_kube_config(Id):
    """
    1.删除kube config 配置入库
    :param Id:
    :return:
    """
    return model_delete(KubeK8sConfig, Id)


def query_kube_config_id(id):
    """
    1.id query data
    :param id:
    :return:
    """
    session = SessionLocal()
    data = session.query(KubeK8sConfig)
    try:
        if id:
            return {"code": 0, "data": data.filter_by(id=id).all(), "messages": "query success", "status": True}
    except Exception as e:
        session.commit()
        session.close()
        return {"code": 1, "data": str(e), "messages": "query failed ", "status": False}


def query_kube_config(page: int = 1, page_size: int = 10, env: Optional[str] = None, cluster_name: Optional[str] = None, server_address: Optional[str] = None, client_key_path: Optional[str] = None):
    """
    1.根据不同条件查询配置信息
    """
    from tools.config import k8sClusterHeader
    session = SessionLocal()
    query = session.query(KubeK8sConfig)
    try:
        if env:
            query = query.filter(KubeK8sConfig.env.ilike(f"%{env}%"))
        if cluster_name:
            query = query.filter(KubeK8sConfig.cluster_name == cluster_name)
        if server_address:
            query = query.filter(KubeK8sConfig.server_address == server_address)
        if client_key_path:
            query = query.filter(KubeK8sConfig.client_key_path == client_key_path)
        data = query.limit(page_size).offset((page-1)*page_size).all()
        total = query.count()
        return {"code": 20000, "total": total, "data": jsonable_encoder(data), "messages": "query data success", "status": True, "columns": k8sClusterHeader}
    except Exception as e:
        setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=str(e))
        return {"code": 50000, "total": 0, "data": "query data failure ", "messages": str(e), "status": True, "columns": k8sClusterHeader}

def query_kube_db_env_cluster_all(env, cluster_name):
    """
    1.查询数据库环境和集群信息
    """
    session = SessionLocal()
    data = session.query(KubeK8sConfig)
    try:
        if env and cluster_name:
            results = data.filter(and_(KubeK8sConfig.env == env, KubeK8sConfig.cluster_name == cluster_name)).all()
            return {"code": 0, "data": [i.to_dict for i in results], "status": True}
        else:
            return {"code": 1, "data": "", "status": False}
    except Exception as e:
        print(e)
        session.commit()
        session.close()

def query_kube_db_env_all():
    try:
        session = SessionLocal()
        query = session.query(KubeK8sConfig.env).distinct().all()
        envList = [row[0] for row in query]
        return {"code": 20000, "total": len(envList), "data": envList, "messages": "query data success", "status": True}
    except Exception as e:
        setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=str(e))
        return {"code": 50000, "total": 0, "data": [], "messages": f"Error occured: {str(e)}", "status": False}

def query_kube_db_cluster_all():
    try:
        session = SessionLocal()
        query = session.query(KubeK8sConfig.cluster_name).distinct().all()
        clusterList = [row[0] for row in query]
        return {"code": 20000, "total": len(clusterList), "data": clusterList, "messages": "query data success", "status": True}
    except Exception as e:
        setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=str(e))
        return {"code": 50000, "total": 0, "data": [], "messages": f"Error occured: {str(e)}", "status": False}

def query_kube_db_env_cluster_wrapper():
    def decorator(func):
        def wrapped(env, cluster_name):
            """
            1.查询数据库环境和集群信息
            """
            session = SessionLocal()
            data = session.query(KubeK8sConfig)
            try:
                if env and cluster_name:
                    results = data.filter(and_(KubeK8sConfig.env == env, KubeK8sConfig.cluster_name == cluster_name)).all()
                    if not (results):
                        return {"code": 1, "data": "环境{env}或者{cluster}集群信息不存在,请检查配置信息".format(env=env, cluster=cluster_name), "status": False}
                    results_format = {"code": 0, "data": [i.to_dict for i in results], "status": True}
                    for client_path in results_format.get("data"):
                        if not (client_path.get("client_key_path")):
                           return {"code": 1, "data": "获取集群 client path  failure, 请集群配置是否存在,请检查配置问题", "status": False}
                        k8s_instance = client_path.get("client_key_path")
                        return func(k8s_instance)
                else:
                    return {"code": 1, "data": "缺少环境或者集群关键参数", "status": False}
            except Exception as e:
                print(e)
                session.commit()
                session.close()
        return wrapped
    return decorator

