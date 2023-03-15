from sql_app.db_play import model_create, model_update, model_updateId, model_delete
from sql_app.models import ServiceK8sData
from sqlalchemy.orm import sessionmaker
from sql_app.database import engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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


def updata_kube_deployment(Id, env, cluster_name, namespace, svc_name, selector_labels, svc_port, svc_type, target_port):
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
    return model_create(ServiceK8sData, Id, request_data, fildes)

def delete_db_svc(Id):
    """
    1.删除kube config 配置入库
    :param Id:
    :return:
    """
    return model_delete(ServiceK8sData, Id)


def query_kube_svc(env, cluster_name, namespace, svc_name, selector_labels, svc_port, svc_type, target_port):
    """
    1.跟进不同条件查询配置信息
    """
    session = SessionLocal()
    data = session.query(ServiceK8sData)
    try:
        if env:
            return {"code": 0, "data": data.filter_by(env=env).first()}
        if cluster_name:
            return {"code": 0, "data": data.filter_by(env=env).first()}
        if namespace:
            return {"code": 0, "data": data.filter_by(namespace=namespace).first()}
        if svc_name:
            return {"code": 0, "data": data.filter_by(svc_name=svc_name).first()}

        if selector_labels:
            return {"code": 0, "data": data.filter_by(selector_labels=selector_labels).first()}

        if svc_port:
            return {"code": 0, "data": data.filter_by(svc_port=svc_port).first()}

        if svc_type:
            return {"code": 0, "data": data.filter_by(svc_type=svc_type).first()}
        if target_port:
            return {"code": 0, "data": data.filter_by(target_port=target_port).first()}
    except Exception as e:
        print(e)
    session.commit()
    session.close()
    return {"code": 0, "data": [i.to_dict for i in data], "messages": "query success", "status": True}
