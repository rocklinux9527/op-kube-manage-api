from sql_app.db_play import model_create, model_update, model_updateId, model_delete
from sql_app.models import KubeK8sConfig
from sqlalchemy.orm import sessionmaker
from sql_app.database import engine
import requests
from tools.config import queryClusterURL
from functools import lru_cache

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
    return {"code": 0, "data": [i.to_dict for i in data], "messages": "query success", "status": True}


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


def query_kube_env_cluster_all():
    """
    1.查询集群配置接口
    2.处理返回后数据重组数据结构.
    3.处理后数据结构示例如下:
    {'env': ['dev'], 'cluster': [{'dev': 'c1'}, {'dev': 'c2'}]}
    """
    sp = requests.get(queryClusterURL)
    try:
        data = dict()
        envs = list(set([i.get("env") for i in sp.json().get("data")]))
        data["env"] = envs
        clusterList = []
        for i in sp.json().get("data"):
            clusterList.append({i.get("env"): i.get("cluster_name")})
        data["cluster"] = clusterList
        return data
    except Exception as e:
        return str(e), False
    finally:
        sp.close()


def query_cluster_client_path_v1(env, cluster_name):
    """
    原始版本
    1.根据env环境和集群精确查询环境client_key_path
    """
    import requests
    from tools.config import queryClusterURL
    if not (env and cluster_name):
        return {"code": 1, "status": False, "data": "", "messages": "cluster_name and Env Not Null"}
    payload = {'env=': env, 'cluster_name': cluster_name}
    try:
        sp = requests.get(queryClusterURL, params=payload, timeout=3)
        data = sp.json().get("data")
        if data:
            for client_path in data:
                client_key_path = client_path.get("client_key_path")
                return {"code": 1, "status": False, "data": client_key_path, "messages": "Cluster Client Path Success"}
        else:
            return {"code": 1, "status": False, "data": "", "messages": "cluster config not found"}

    except Exception as e:
        return str(e), False


@lru_cache(maxsize=None)
def query_cluster_client_path_v2(env, cluster_name):
    """
    优化版本
    1.减少网络请求的次数，可以使用缓存来提高效率。
    2.减少循环的次数，可以直接使用列表推导式或者生成器来代替for循环。
    3.减少异常捕获的次数，尽可能避免使用`try...except`语句，在代码中添加判断语句来规避异常情况。
    4.减少不必要的代码，例如 `if not (env and cluster_name)` 可以写成 `if not env or not cluster_name`，代码更加简洁。
    5.这个函数使用了Python的`lru_cache`装饰器，可以在函数运行时缓存结果，以减少网络请求的次数。
    同时，使用列表推导式和`next`函数来避免循环过程，减少循环的次数。
    优化后，代码更加简洁清晰，而且运行效率也会更高.
    """
    if not env or not cluster_name:
        return {"code": 1, "status": False, "data": "", "messages": "cluster_name and Env Not Null"}
    payload = {'env': env, 'cluster_name': cluster_name}
    try:
        sp = requests.get(queryClusterURL, params=payload, timeout=3)
        data = sp.json().get("data")
        if data:
            client_key_path = next((client_path.get("client_key_path") for client_path in data), "")
            print(client_key_path)
            return {"code": 0, "status": False, "data": client_key_path, "messages": "Cluster Client Path Success"}
        else:
            return {"code": 1, "status": False, "data": "", "messages": "cluster config not found"}
    except Exception as e:
        return str(e), False
