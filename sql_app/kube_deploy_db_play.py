from sql_app.db_play import model_create, model_update, model_updateId, model_delete
from sql_app.models import DeployK8sData
from sqlalchemy.orm import sessionmaker
from sql_app.database import engine
from sqlalchemy import and_
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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


def query_kube_deployment(env, cluster, app_name, image, ports, image_pull_secrets, deploy_id):
    """
    1.跟进不同条件查询配置信息
    """
    session = SessionLocal()
    data = session.query(DeployK8sData)
    try:
        if env:
            return {"code": 0, "data": data.filter_by(env=env).first()}

        if cluster:
            return {"code": 0, "data": data.filter_by(cluster=cluster).first()}

        if app_name:
            return {"code": 0, "data": data.filter_by(app_name=app_name).first()}

        if image:
            return {"code": 0, "data": data.filter_by(image=image).first()}
        if ports:
            return {"code": 0, "data": data.filter_by(ports=ports).first()}

        if image_pull_secrets:
            return {"code": 0, "data": data.filter_by(image_pull_secrets=image_pull_secrets).first()}
        if deploy_id:
            return {"code": 0, "data": data.filter_by(deploy_id=deploy_id).first()}

    except Exception as e:
        print(e)
    session.commit()
    session.close()
    return {"code": 0, "data": [i.to_dict for i in data], "messages": "query success", "status": True}


def query_kube_deployment_by_name(env_name, cluster_name, app_name, namespace_name):
    session = SessionLocal()
    data = session.query(DeployK8sData)
    if env_name and cluster_name:
        results = data.filter(and_(DeployK8sData.env == env_name, DeployK8sData.cluster == cluster_name, DeployK8sData.app_name == app_name, DeployK8sData.namespace == namespace_name)).all()
        return {"code": 0, "data": [i.to_dict for i in results], "status": True}
    else:
        return {"code": 1, "data": "", "status": False}
