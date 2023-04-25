from sql_app.db_play import model_create, model_update, model_updateId, model_delete
from sql_app.models import DeployK8sData
from sqlalchemy.orm import sessionmaker
from sql_app.database import engine
from sqlalchemy import and_
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
from fastapi.encoders import jsonable_encoder

from tools.config import setup_logging
import os
HERE = os.path.abspath(__file__)
HOME_DIR = os.path.split(os.path.split(HERE)[0])[0]
LOG_DIR = os.path.join(HOME_DIR, "logs")
def insert_kube_deployment(app_name, env, cluster, namespace, resources,
                           replicas, image, affinity, ant_affinity,
                           deploy_env, ports, volumeMounts,
                           volume, image_pull_secrets, health_liven_ess,
                           health_readiness, deploy_id):
    """
    1.新增入库参数
    :param app_name:
    :param env:
    :param cluster:
    :param namespace:
    :param resources:
    :param replicas:
    :param image:
    :param affinity:
    :param ant_affinity:
    :param deploy_env:
    :param ports:
    :param volumeMounts:
    :param volume:
    :param image_pull_secrets:
    :param health_liven_ess:
    :param health_readiness:
    :param deploy_id:
    :return:
    """
    fildes = {
        "app_name": "app_name",
        "env": "env",
        "cluster": "cluster",
        "namespace": "namespace",
        "resources": "resources",
        "replicas": "replicas",
        "image": "image",
        "affinity": "affinity",
        "ant_affinity": "ant_affinity",
        "deploy_env": "deploy_env",
        "ports": "ports",
        "volumeMounts": "volumeMounts",
        "volume": "volume",
        "image_pull_secrets": "image_pull_secrets",
        "health_liven_ess": "health_liven_ess",
        "health_readiness": "health_readiness",
        "deploy_id": "deploy_id"
    }

    request_data = {
        "app_name": app_name,
        "env": env,
        "cluster": cluster,
        "namespace": namespace,
        "resources": resources,
        "replicas": replicas,
        "image": image,
        "affinity": affinity,
        "ant_affinity": ant_affinity,
        "deploy_env": deploy_env,
        "ports": ports,
        "volumeMounts": volumeMounts,
        "volume": volume,
        "image_pull_secrets": image_pull_secrets,
        "health_liven_ess": health_liven_ess,
        "health_readiness": health_readiness,
        "deploy_id": deploy_id
    }
    return model_create(DeployK8sData, request_data, fildes)


def updata_kube_deployment(Id, app_name, env, cluster, namespace, resources,
                           replicas, image, affinity, ant_affinity,
                           deploy_env, ports, volumeMounts,
                           volume, image_pull_secrets, health_liven_ess,
                           health_readiness, deploy_id):
    """
    1.部署参数修改
    :param Id:
    :param app_name:
    :param env:
    :param cluster:
    :param namespace:
    :param resources:
    :param replicas:
    :param image:
    :param affinity:
    :param ant_affinity:
    :param deploy_env:
    :param ports:
    :param volumeMounts:
    :param volume:
    :param image_pull_secrets:
    :param health_liven_ess:
    :param health_readiness:
    :param deploy_id:
    :return:
    """
    fildes = {
        "app_name": "app_name",
        "env": "env",
        "cluster": "cluster",
        "namespace": "namespace",
        "resources": "resources",
        "replicas": "replicas",
        "image": "image",
        "affinity": "affinity",
        "ant_affinity": "ant_affinity",
        "deploy_env": "deploy_env",
        "ports": "ports",
        "volumeMounts": "volumeMounts",
        "volume": "volume",
        "image_pull_secrets": "image_pull_secrets",
        "health_liven_ess": "health_liven_ess",
        "health_readiness": "health_readiness",
        "deploy_id": "deploy_id"
    }

    request_data = {
        "app_name": app_name,
        "env": env,
        "cluster": cluster,
        "namespace": namespace,
        "resources": resources,
        "replicas": replicas,
        "image": image,
        "affinity": affinity,
        "ant_affinity": ant_affinity,
        "deploy_env": deploy_env,
        "ports": ports,
        "volumeMounts": volumeMounts,
        "volume": volume,
        "image_pull_secrets": image_pull_secrets,
        "health_liven_ess": health_liven_ess,
        "health_readiness": health_readiness,
        "deploy_id": deploy_id
    }
    return model_updateId(DeployK8sData, Id, request_data, fildes)


def delete_kube_deployment(Id):
    """
    1.删除kube config 配置入库
    :param Id:
    :return:
    """
    return model_delete(DeployK8sData, Id)

def query_kube_deployment(page, page_size, env, cluster, app_name, image, ports, image_pull_secrets, deploy_id):
    from tools.config import k8sDeployHeader
    """
    1.使用条件列表替换原本的if语句，将重复的代码合并。这样可以减少代码量，提高可读性，方便后期维护。
    2.对于查询条件返回的结果，可以使用类型检查来判断是否是一个列表。如果是列表，就进行分页操作并返回结果。
    如果不是，就直接返回结果。这样可以避免在查询条件为列表时，出现错误的返回结果。
    3.优化异常处理，使用session的rollback()方法，避免出现错误时session不能正常关闭。
    4.最后使用finally块，确保session能够被正确地关闭，释放资源.
    """
    session = SessionLocal()
    data = session.query(DeployK8sData)
    conditions = [
        (env, data.filter_by(env=env).first()),
        (cluster, data.filter_by(cluster=cluster).all()),
        (app_name, data.filter_by(app_name=app_name).first()),
        (image, data.filter_by(image=image).first()),
        (ports, data.filter_by(ports=ports).first()),
        (image_pull_secrets, data.filter_by(image_pull_secrets=image_pull_secrets).first()),
        (deploy_id, data.filter_by(deploy_id=deploy_id).first())
    ]
    try:
        for condition in conditions:
            if condition[0]:
                if isinstance(condition[1], list):
                    result_data = condition[1][(page - 1) * page_size:page * page_size]
                    return {"code": 0, "total": len(condition[1]), "data": jsonable_encoder(result_data),
                            "messages": "query data success", "status": True, "columns": k8sDeployHeader}
                else:
                    return {"code": 0, "data": condition[1]}
        result_data = data.limit(page_size).offset((page - 1) * page_size).all()
        return {"code": 0, "total": len(data.all()), "data": jsonable_encoder(result_data),
                "messages": "query data success", "status": True, "columns": k8sDeployHeader}
    except Exception as e:
        session.rollback()
        setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=str(e))
        return {"code": 1, "total": 0, "data": "query data failure ", "messages": str(e), "status": False,"columns": k8sDeployHeader}
    finally:
        session.close()

def query_kube_deployment_by_name(env_name, cluster_name, app_name, namespace_name):
    session = SessionLocal()
    data = session.query(DeployK8sData)
    results = data.filter(and_(DeployK8sData.env == env_name, DeployK8sData.cluster == cluster_name, DeployK8sData.app_name == app_name, DeployK8sData.namespace == namespace_name)).all()
    if not env_name and cluster_name and results:
        return {"code": 1, "data": "", "status": False}
    else:
        return {"code": 0, "data": [i.to_dict for i in results], "status": True}
