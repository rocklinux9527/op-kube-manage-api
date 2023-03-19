from sql_app.db_play import model_create, model_update, model_updateId, model_delete
from sql_app.models import IngressK8sData
from sqlalchemy.orm import sessionmaker
from sql_app.database import engine
from sqlalchemy import and_
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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


def query_kube_ingres(env, cluster_name,namespace, ingress_name, host, svc_name, svc_port, tls, tls_secret):
    """
    1.跟进不同条件查询配置信息
    """
    session = SessionLocal()
    data = session.query(IngressK8sData)
    try:
        if env:
            return {"code": 0, "data": data.filter_by(env=env).first()}
        if cluster_name:
            return {"code": 0, "data": data.filter_by(cluster_name=cluster_name).first()}
        if namespace:
            return {"code": 0, "data": data.filter_by(namespace=namespace).first()}

        if ingress_name:
            return {"code": 0, "data": data.filter_by(ingress_name=ingress_name).first()}

        if host:
            return {"code": 0, "data": data.filter_by(host=host).first()}

        if svc_name:
            return {"code": 0, "data": data.filter_by(svc_name=svc_name).first()}
        if svc_port:
            return {"code": 0, "data": data.filter_by(svc_port=svc_port).first()}
        if ingress_name:
            return {"code": 0, "data": data.filter_by(ingress_class_name=ingress_name).first()}

        if tls:
            return {"code": 0, "data": data.filter_by(tls=tls).first()}
        if tls_secret:
            return {"code": 0, "data": data.filter_by(tls_secret=tls_secret).first()}

    except Exception as e:
        print(e)
    session.commit()
    session.close()
    return {"code": 0, "data": [i.to_dict for i in data], "messages": "query success", "status": True}

def query_kube_ingress_by_name(env_name, cluster_name, ingress_name, namespace_name):
    session = SessionLocal()
    data = session.query(IngressK8sData)
    if env_name and cluster_name:
        results = data.filter(and_(IngressK8sData.env == env_name, IngressK8sData.cluster_name == cluster_name, IngressK8sData.ingress_name == ingress_name, IngressK8sData.namespace == namespace_name)).all()
        return {"code": 0, "data": [i.to_dict for i in results], "status": True}
    else:
        return {"code": 1, "data": "", "status": False}
