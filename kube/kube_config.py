import os

HERE = os.path.abspath(__file__)
HOME_DIR = os.path.split(os.path.split(HERE)[0])[0]
script_path = os.path.join(HOME_DIR, "tools")
conf_path = os.path.join(HOME_DIR, "conf")
os.sys.path.append(script_path)
os.sys.path.append(conf_path)

from tools.nacosGet import getNacosInfo


def getNacos_key(cluster, keyName):
    """
    1.集群名称 对比list 存在key是否存在
    2.获取nacos配置key内容
    :param cluster:
    :param keyName:
    :return:
    """
    if cluster and keyName:
        cluster_name = cluster + ".json"
        return getNacosInfo(cluster_name, keyName)
    else:
        return {"code": "1", "messages": "集群名称错误或者Nacos定义对不上", "status": False, "data": ""}


def add_kube_config(env, cluster_name, server_address, ca_data, client_crt_data, client_key_data):
    """
    1.获取模版文件内容写入kube conf配置nacos配置集群信息
    :param env:
    :param cluster:
    :return:
    """
    import time
    sf = open(conf_path + "/kube_config.template", "r")
    template_data = "".join(sf.readlines())
    sf.close()
    f = open(conf_path + "/kubeconf/{env}_{cluster}.conf".format(env=env, cluster=cluster_name), "w+")

    if env and cluster_name and server_address and ca_data and client_crt_data and client_key_data:
        conf_data = template_data.format(CaCert=ca_data,
                                         Server=server_address,
                                         K8sCaCert=client_crt_data,
                                         K8sKey=client_key_data
                                         )
        f.write(conf_data)
        f.close()
        filename = "./conf/kubeconf/{env}{cluster}.conf".format(env=env, cluster=cluster_name)
        return {"code": 0, "data": filename, "status": True, "messages": "add kubeconfig success"}

    else:
        return {"code": 1,  "data": "", "status": True, "messages": "If the parameter is empty, check it" }


def get_kube_config_dir_file():
    """
    :return:
    """
    file_path = conf_path + "/kubeconf/"
    try:
        file_name_list = os.listdir(file_path)
        file_sting = []
        for list in file_name_list:
            source = file_path + list
            file_sting.append(source)
        return {"code": 0, "data": file_sting, "messages": "search kube config file list success", "status": True}
    except Exception as e:
        return {"code": 1, "data": "", "messages": "search kube config file list failure" + str(e), "status": True}


def get_key_file_path(env, cluster):
    """
    1.传递环境env 和集群名称 返回kubeconfig-本地文件路径
    """
    return conf_path + "/kubeconf/{env}_{cluster}.conf".format(env=env, cluster=cluster)



def get_kube_config_content(env, cluster_name):
    """
    :param env:
    :param cluster_name:
    :return:
    """
    try:
        sf = open(conf_path + "/kubeconf/{env}_{cluster}.conf".format(env=env, cluster=cluster_name), "r")
        content_data = "".join(sf.readlines())
        sf.close()
        return {"code": 0, "data": content_data, "messages": "search kubeconfig file success", "status": True}
    except Exception as e:
        return {"code": 1, "data": "", "messages": "search kubeconfig file failure" + str(e), "status": True}


def delete_kubeconfig_file(filename):
    """
    1.
    :return:
    """
    file_full_file = conf_path + "/kubeconf/" + filename
    if os.path.isfile(file_full_file):
        os.remove(file_full_file)
        return {"code": 0, "data": file_full_file, "messages": "delete kubeconfig file success", "status": True}
    else:
        return {"code": 1, "data": "", "messages": "file not found  delete kubeconfig failure", "status": True}


def get_kube_namespace(env, cluster):
    """
    1.获取 namespace 环境名称和 集群名称 默认情况给default
    :param env:
    :param cluster:
    :return:
    """
    namespace = "{env}-{cluster}".format(env=env, cluster=cluster)
    if cluster == "default":
        namespace = env
    return namespace


if __name__ == "__main__":
    # add_kube_config("dev", "hdd-yunxiaobao-pre")
    # a = get_kube_config_content("dev","yunxiaobao-pre")
    # a = get_kube_config_dir_file()
    a = delete_kubeconfig_file("test_hdd_k8s.conf")
    print(a)
