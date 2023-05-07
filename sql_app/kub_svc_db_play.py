from sql_app.db_play import model_create, model_update, model_updateId, model_delete
from sql_app.models import ServiceK8sData
from sqlalchemy.orm import sessionmaker
from sql_app.database import engine
from sqlalchemy import and_
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
from tools.config import setup_logging
from fastapi.encoders import jsonable_encoder
import os
HERE = os.path.abspath(__file__)
HOME_DIR = os.path.split(os.path.split(HERE)[0])[0]
LOG_DIR = os.path.join(HOME_DIR, "logs")

def insert_db_svc(env, cluster_name, namespace, svc_name, selector_labels, svc_port, svc_type, target_port):
    """
    1.新增入库参数
    :env
    :cluster_name
    :param namespace:
    :param svc_name:
    :param svc_port:
    :param svc_type:
    :param target_port:
    :return:
    """
    fildes = {
        "env": "env",
        "cluster_name":"cluster_name",
        "namespace": "namespace",
        "svc_name": "svc_name",
        "selector_labels": "selector_labels",
        "svc_port": "svc_port",
        "svc_type": "svc_type",
        "target_port": "target_port"
    }

    request_data = {
        "env": env,
        "cluster_name": cluster_name,
        "namespace": namespace,
        "svc_name": svc_name,
        "selector_labels": selector_labels,
        "svc_port": svc_port,
        "svc_type": svc_type,
        "target_port": target_port
    }
    return model_create(ServiceK8sData, request_data, fildes)


def updata_kube_svc(Id, env, cluster_name, namespace, svc_name, selector_labels, svc_port, svc_type, target_port):
    """

    :param Id:
    :param namespace:
    :param svc_name:
    :param selector_labels:
    :param svc_port:
    :param svc_type:
    :param target_port:
    :return:
    """
    fildes = {
        "env": "env",
        "cluster_name": "cluster_name",
        "namespace": "namespace",
        "svc_name": "svc_name",
        "selector_labels": "selector_labels",
        "svc_port": "svc_port",
        "svc_type": "svc_type",
        "target_port": "target_port"
    }

    request_data = {
        "env": env,
        "cluster_name": cluster_name,
        "namespace": namespace,
        "svc_name": svc_name,
        "selector_labels": selector_labels,
        "svc_port": svc_port,
        "svc_type": svc_type,
        "target_port": target_port
    }
    return model_updateId(ServiceK8sData, Id, request_data, fildes)

def delete_db_svc(Id):
    """
    1.删除kube config 配置入库
    :param Id:
    :return:
    """
    return model_delete(ServiceK8sData, Id)


from tools.config import k8sServiceHeader

def query_kube_svc(page, page_size, env=None, cluster_name=None, namespace=None, svc_name=None, selector_labels=None, svc_port=None, svc_type=None, target_port=None):
    """
    根据不同条件查询 Kubernetes 服务的配置信息

    Args:
        page (int): 分页页码
        page_size (int): 分页大小
        env (str): 环境名
        cluster_name (str): 集群名
        namespace (str): 命名空间
        svc_name (str): 服务名
        selector_labels (str): 选择器标签
        svc_port (int): 服务端口
        svc_type (str): 服务类型
        target_port (int): 目标端口

    Returns:
        dict: 查询结果
    """
    session = SessionLocal()
    data = session.query(ServiceK8sData)

    # 根据参数进行查询
    if env:
        data = data.filter_by(env=env)
    if cluster_name:
        data = data.filter_by(env=env)  # 原代码中 env 应为 cluster_name
    if namespace:
        data = data.filter_by(namespace=namespace)
    if svc_name:
        data = data.filter_by(svc_name=svc_name)
    if selector_labels:
        data = data.filter_by(selector_labels=selector_labels)
    if svc_port:
        data = data.filter_by(svc_port=svc_port)
    if svc_type:
        data = data.filter_by(svc_type=svc_type)
    if target_port:
        data = data.filter_by(target_port=target_port)

    try:
        # 如果有分页参数，则进行分页查询并返回结果
        if page and page_size:
            total_count = data.count()
            result_data = data.limit(page_size).offset((page - 1) * page_size).all()
            return {"code": 0, "total": total_count, "data": jsonable_encoder(result_data),
                    "messages": "query data success", "status": True, "columns": k8sServiceHeader}
        # 否则返回所有数据
        else:
            return {"code": 0, "total": len([i.to_dict for i in data]), "data": jsonable_encoder(data.all()),
                    "messages": "query data success", "status": True, "columns": k8sServiceHeader}
    except Exception as e:
        print(e)
        session.commit()
        session.close()
        return {"code": 0, "total": 0,"data": [i.to_dict for i in data], "messages": "query success", "status": True, "columns": k8sServiceHeader}

def query_kube_svc_by_name(env_name, cluster_name, svc_name, namespace_name):
    session = SessionLocal()
    data = session.query(ServiceK8sData)
    results = data.filter(and_(ServiceK8sData.env == env_name, ServiceK8sData.cluster_name == cluster_name, ServiceK8sData.svc_name == svc_name, ServiceK8sData.namespace == namespace_name)).all()
    print(results)
    if env_name and cluster_name and results:
        return {"code": 0, "data": [i.to_dict for i in results], "status": True}
    else:
        return {"code": 1, "data": "", "status": False}

def query_kube_svc_by_id(ID):
    """
    1.跟进id条件查询配置信息
    """
    session = SessionLocal()
    data = session.query(ServiceK8sData)
    results = data.filter_by(id=ID).first()
    if not (ID and results):
        return {"code": 1, "data": "", "status": False}
    else:
        return {"code": 0, "data": results, "status": True}

def query_kube_all_svc_name(env_name:str, cluster_name:str, namespace_name:str) -> dict:
    """
    查询环境env和集群和命名空间
    Args:
        env_name: str, 环境名称
        cluster_name: str, 集群名称
        namespace_name: str, 命名空间名称

    Returns:
        dict, {"code": 0/1, "data": list/str, "status": True/False}
    # 使用distinct去重，并仅查询svc_name列
    # 通过上下文管理器使用SessionLocal
    # 使用列表推导式取出结果中的svc_name
     # 检查所有参数是否存在并且查询结果不为空
    """
    with SessionLocal() as session:
        results = session.query(ServiceK8sData.svc_name).filter_by(
            env=env_name,
            cluster_name=cluster_name,
            namespace=namespace_name
        ).distinct().all()
        svc_list = [result[0] for result in results]

    if env_name and cluster_name and svc_list:
        return {"code": 0, "data": svc_list, "status": True, "messages": "query svc-name all success"}
    else:
        return {"code": 1, "data": "", "status": False,  "messages": "query svc-name all failed"}


def query_kube_all_svc_port(env_name:str, cluster_name:str, namespace_name:str, svc_name:str ) -> dict:
    """
    查询环境env和集群和命名空间
    Args:
        env_name: str, 环境名称
        cluster_name: str, 集群名称
        namespace_name: str, 命名空间名称

    Returns:
        dict, {"code": 0/1, "data": list/str, "status": True/False}
    """
    with SessionLocal() as session:
        results = session.query(ServiceK8sData.svc_port).filter_by(
            env=env_name,
            cluster_name=cluster_name,
            namespace=namespace_name,
            svc_name=svc_name
        ).distinct().all()
        port_list = [result[0] for result in results]

    if env_name and cluster_name and port_list:
        return {"code": 0, "data": port_list, "status": True, "messages": "query svc-port all success"}
    else:
        return {"code": 1, "data": "", "status": False,  "messages": "query svc-port all failed"}
