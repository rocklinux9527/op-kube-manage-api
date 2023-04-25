from sql_app.db_play import model_create, model_update, model_updateId, model_delete
from sql_app.models import IngressK8sData
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
def insert_db_ingress(env, cluster_name, namespace, ingress_name, host, svc_name, path,
                      path_type, ingress_class_name, tls, tls_secret,
                      svc_port, used):
    """
    1.新增入库参数
    :param ns_name:
    :param used:
    :return:
    """
    fildes = {
        "env": "env",
        "cluster_name": "cluster_name",
        "namespace": "namespace",
        "ingress_name": "ingress_name",
        "host": "host",
        "svc_name": "svc_name",
        "path": "path",
        "path_type": "path_type",
        "ingress_class_name": "ingress_class_name",
        "tls": "tls",
        "tls_secret": "tls_secret",
        "svc_port": "svc_port",
        "used": "used"
    }

    request_data = {
        "env": env,
        "cluster_name": cluster_name,
        "namespace": namespace,
        "ingress_name": ingress_name,
        "host": host,
        "svc_name": svc_name,
        "path": path,
        "path_type": path_type,
        "ingress_class_name": ingress_class_name,
        "tls": tls,
        "tls_secret": tls_secret,
        "svc_port": svc_port,
        "used": used
    }
    return model_create(IngressK8sData, request_data, fildes)


def updata_db_ingress(Id, env, cluster_name, namespace, ingress_name,
                      host, svc_name, path,
                      path_type, ingress_class_name,
                      tls, tls_secret, svc_port, used):
    """
    1.修改数据
    :param Id:
    :param namespace:
    :param ingress_name:
    :param host:
    :param svc_name:
    :param path:
    :param path_type:
    :param ingress_class_name:
    :param tls:
    :param svc_port:
    :param used:
    :return:
    """
    fildes = {
        "env": "env",
        "cluster_name": "cluster_name",
        "namespace": "namespace",
        "ingress_name": "ingress_name",
        "host": "host",
        "svc_name": "svc_name",
        "path": "path",
        "path_type": "path_type",
        "ingress_class_name": "ingress_class_name",
        "tls": "tls",
        "tls_secret": "tls_secret",
        "svc_port": "svc_port",
        "used": "used"
    }
    request_data = {
        "env": env,
        "cluster_name": cluster_name,
        "namespace": namespace,
        "ingress_name": ingress_name,
        "host": host,
        "svc_name": svc_name,
        "path": path,
        "path_type": path_type,
        "ingress_class_name": ingress_class_name,
        "tls": tls,
        "tls_secret": tls_secret,
        "svc_port": svc_port,
        "used": used
    }
    return model_updateId(IngressK8sData, Id, request_data, fildes)


def delete_db_ingress(Id):
    """
    1.删除kube config 配置入库
    :param Id:
    :return:
    """
    return model_delete(IngressK8sData, Id)


def query_kube_ingres(page, page_size, env, cluster_name, namespace, ingress_name, host, svc_name, svc_port, tls, tls_secret):
    session = SessionLocal()
    data = session.query(IngressK8sData)
    conditions = [
        (env, data.filter_by(env=env).first()),
        (cluster_name, data.filter_by(cluster_name=cluster_name).all()),
        (namespace, data.filter_by(namespace=namespace).all()),
        (ingress_name, data.filter_by(ingress_name=ingress_name).first()),
        (host, data.filter_by(host=host).first()),
        (svc_name, data.filter_by(svc_name=svc_name).first()),
        (svc_port, data.filter_by(svc_port=svc_port).all()),
        (tls, data.filter_by(tls=tls).first()),
        (tls_secret, data.filter_by(tls_secret=tls_secret).first())
    ]
    try:
        for condition in conditions:
            if condition[0]:
                if isinstance(condition[1], list):
                    result_data = condition[1][(page - 1) * page_size:page * page_size]
                    return {"code": 0, "total": len(condition[1]), "data": jsonable_encoder(result_data),
                            "messages": "query data success", "status": True}
                else:
                    return {"code": 0, "data": condition[1]}
        result_data = data.limit(page_size).offset((page - 1) * page_size).all()
        return {"code": 0, "total": len(data.all()), "data": jsonable_encoder(result_data),
                "messages": "query data success", "status": True}
    except Exception as e:
        session.rollback()
        setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=str(e))
        return {"code": 1, "total": 0, "data": "query data failure ", "messages": str(e), "status": True}
    finally:
        session.close()

def query_kube_ingress_by_id(ID):
    """
    1.跟进id条件查询配置信息
    """
    session = SessionLocal()
    data = session.query(IngressK8sData)
    results = data.filter_by(id=ID).first()
    if not (ID and results):
        return {"code": 1, "data": "", "status": False}
    else:
        return {"code": 0, "data": results, "status": True}

def query_kube_ingress_by_name(env_name, cluster_name, ingress_name, namespace_name):
    session = SessionLocal()
    data = session.query(IngressK8sData)
    results = data.filter(and_(IngressK8sData.env == env_name, IngressK8sData.cluster_name == cluster_name, IngressK8sData.ingress_name == ingress_name, IngressK8sData.namespace == namespace_name)).all()
    if env_name and cluster_name and results:
        return {"code": 0, "data": [i.to_dict for i in results], "status": True}
    else:
        return {"code": 1, "data": "", "status": False}
