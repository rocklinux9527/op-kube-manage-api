import nacos
import yaml
import config
def getNacosInfo(clusterId, getKey=None):
    """
    1.nacos data-id 和集群名称一致
    :param data_id:
    :param group:
    :return:
    """
    client = nacos.NacosClient(config.nacos_config.get("nacos_server_address", "http://localhost:8848"),
                               namespace=config.nacos_config.get("namespace", "default"),
                               username=config.nacos_config.get("username", "nacos"),
                               password=config.nacos_config.get("password", "nacos")
                               )
    nacos_config = client.get_config(clusterId, config.nacos_config.get("group", "DEFAULT_GROUP"))
    nacosKeyList = ["envs", "clusters", "ack_api_server",
                    "ack_kubectl-version", "ack_crt", "ack_token", "ack_client_certificate_data",
                    "ack_client_key_data"]

    if getKey in nacosKeyList:
        dict_nacos_config = yaml.load(nacos_config, Loader=yaml.FullLoader)
        return {"code": 0, "messages": "nacos get success",
                "status": True, "keyName": getKey,
                "data": dict_nacos_config.get(getKey)
                }
    elif getKey == "all" or getKey == "*":
        nacos_config = client.get_config(clusterId, config.nacos_config.get("group", "DEFAULT_GROUP"))
        return {"code": 0, "messages": "nacos all data get success",
                "status": True, "keyName": getKey,
                "data": nacos_config
                }
    else:
        return {"code": 1, "messages": "参数不正确,没有获取到数据,请进行入参数检查",
                "status": False, "keyName": getKey,
                "data": "no data"
                }


if __name__ == "__main__":
    print(getNacosInfo("hdd-pre.json", ""))
