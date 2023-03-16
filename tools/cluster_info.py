import requests
from sql_app.kube_cnfig_db_play import query_kube_env_cluster_all, query_cluster_client_path_v2
from functools import wraps, partial
from sql_app.kube_cnfig_db_play import query_kube_env_cluster_all,query_kube_db_env_cluster_all


def clusterConfigCheck(func=None, **my_dict):
    """
    1.k8s 集群环境验证修饰器,解决多个接口依赖验证问题.
    """
    if func is None:
        return partial(clusterConfigCheck, **my_dict)
    result_Cluster_Info = query_kube_db_env_cluster_all(my_dict.get.get("env"), my_dict.get("cluster"))
    result_data = result_Cluster_Info.get("data")
    # envListData = set(result_Cluster_Info.get("data"))
    # clusterListData = result_Cluster_Info.get("cluster")
    # cluster_name = my_dict.get("cluster")
    # env_name = my_dict.get("env")
    # cluster_list = [i[env_name] for i in clusterListData if env_name in i]
    @wraps(func)
    def inner(*args, **kwargs):
        if result_data:
            return func(*args, **kwargs)
        else:
            return {"code": 1, "status": False, "data": [], "messages": "Cluster configuration does not exist"}
    return inner


my_dict = {'cluster_name': 'c3', "env": "dev"}

# @clusterConfigCheck(my_dict=my_dict)
# def my_func():
#     print("1111")

# if __name__ == "__main__":
#     #a = my_func()
#     result = query_cluster_client_path_v2("test", "c1")
#     print(result)
