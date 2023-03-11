from sql_app.db_play import model_create, model_update, model_updateId, model_delete
from sql_app.models import KubeK8sConfig
from sqlalchemy.orm import sessionmaker
from sql_app.database import engine
from sqlalchemy import and_
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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


def query_kube_config(env, cluster_name, server_address, client_key_path):
    print("参数", env)
    """
    1.跟进不同条件查询配置信息
    """
    session = SessionLocal()
    data = session.query(KubeK8sConfig)
    try:
        if env and cluster_name:
            results = data.filter(and_(KubeK8sConfig.env == env, KubeK8sConfig.cluster_name == cluster_name)).all()
            return {"code": 0, "data": results}
        if env:
            return {"code": 0, "data": data.filter_by(env=env).all()}

        if cluster_name:
            return {"code": 0, "data": data.filter_by(cluster_name=cluster_name).all()}

        if server_address:
            return {"code": 0, "data": data.filter_by(server_address=server_address).first()}

        if client_key_path:
            return {"code": 0, "data": data.filter_by(client_key_path=client_key_path).first()}
    except Exception as e:
        session.commit()
        session.close()
    print("走全局了")
    return {"code": 0, "data": [i.to_dict for i in data], "messages": "query success", "status": True}


def query_kube_env_cluster_all():
    """
    1.查询集群配置接口
    2.处理返回后数据重组数据结构.
    3.处理后数据结构示例如下:
    {'env': ['dev'], 'cluster': [{'dev': 'c1'}, {'dev': 'c2'}], 'client_key_path':
    [{'dev': '/dev_c1.conf'}, {'dev': '/dev_c2.conf'}]}
    """
    import requests
    from tools.config import queryClusterURL
    sp = requests.get(queryClusterURL)
    try:
        data = dict()
        envs = list(set([i.get("env") for i in sp.json().get("data")]))
        data["env"] = envs
        clusterList = []
        for i in sp.json().get("data"):
            clusterList.append({i.get("env"): i.get("cluster_name")})
        data["cluster"] = clusterList
        keyPathList = []
        for i in sp.json().get("data"):
            keyPathList.append({i.get("env"): i.get("client_key_path")})
        data["client_key_path"] = keyPathList
        return data
    except Exception as e:
        return str(e), False
    finally:
        sp.close()

