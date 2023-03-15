import requests
from tools.config import queryClusterURL
from sql_app.kube_cnfig_db_play import query_kube_env_cluster_all,query_cluster_client_path_v2
import json


def clusterConfigCheck(my_dict):
    """
    1.k8s 集群环境验证修饰器,解决多个接口依赖验证问题.
    """

    def wrapper(func):
        def inner():
            result_Cluster_Info = query_kube_env_cluster_all()
            envListData = set(result_Cluster_Info.get("env"))
            clusterListData = result_Cluster_Info.get("cluster")
            client_key_path = result_Cluster_Info.get("client_key_path")
            cluster_name = my_dict.get("cluster")
            env_name = my_dict.get("env")
            cluster_list = [i[env_name] for i in clusterListData if env_name in i]
            return {"code": 0, "status": True,
                    "data": client_key_path, "message": "Success"} if env_name in envListData and cluster_name in cluster_list else {
                "code": 1,
                "status": False, "data": [], "messages": "Cluster configuration does not exist"}
        return inner
    return wrapper


my_dict = {'cluster': 'c3', "env": "dev"}


@clusterConfigCheck(my_dict=my_dict)
def my_func():
    print("1111")


if __name__ == "__main__":
    #a = my_func()
    result = query_cluster_client_path_v2("test", "c1")
    print(result)
