import json

from kube.kube_ingress import k8sIngressManager
from sql_app.kube_cnfig_db_play import query_kube_db_env_cluster_all
from sql_app.kube_ingress_db_play import insert_db_ingress
from sql_app.ops_log_db_play import insert_ops_bot_log
from sql_app.kube_ingress_db_play import delete_db_ingress, query_kube_ingres, \
    query_kube_ingress_by_name, query_kube_ingress_by_id, updata_db_ingress


class kubeIngressService():
    def create_ingress(self, env_name, cluster_name,
                       namespace_name,
                       ingress_name, host_name, svc_name,
                       svc_port, path_name, path_type,
                       ingress_class_name, tls_name, tls_secret, used, user_request_data):
        result_cluster_info = query_kube_db_env_cluster_all(env_name, cluster_name)
        for client_path in result_cluster_info.get("data"):
            if not (client_path.get("client_key_path")):
                msg = "获取集群 client path  failure, 请检查问题"
                return {"code": 50000, "message": msg, "status": True}
            kube_ingress_instance = k8sIngressManager(client_path.get("client_key_path"), namespace_name)
            ingres_result = kube_ingress_instance.create_kube_ingress(ingress_name, host_name, svc_name, svc_port,
                                                                      path_name,
                                                                      path_type, ingress_class_name, tls_name, tls_secret)

            if ingres_result.get("code") == 0:
                created_ingress = insert_db_ingress(
                    env=env_name,
                    cluster_name=cluster_name,
                    namespace=namespace_name,
                    ingress_name=ingress_name,
                    host=host_name,
                    svc_name=svc_name,
                    svc_port=svc_port,
                    path=path_name,
                    path_type=path_type,
                    ingress_class_name=ingress_class_name,
                    tls=tls_name,
                    tls_secret=tls_secret,
                    used=used
                )
                insert_ops_bot_log("Insert kube ingress app ", json.dumps(user_request_data), "post",
                                   json.dumps(created_ingress))
                return created_ingress
            else:
                msg = "Create ingress App failure"
                return {"code": 50000, "message": msg, "status": True}

    def update_ingress(self, ID, env_name, cluster_name, data, item_dict,user_request_data):
        query_ingres_id = query_kube_ingress_by_id(ID)
        if not query_ingres_id.get("data"):
            return {'code': 50000, 'message': "ingress Id not exist , check it", "data": "", "status": False}
        result_cluster_info = query_kube_db_env_cluster_all(env_name, cluster_name)
        for client_path in result_cluster_info.get("data"):
            if not (client_path.get("client_key_path")):
               return {'code': 50000, 'message': "获取集群 client path  failure, 请检查问题", "data": "", "status": False}
            update_ingress_instance = k8sIngressManager(client_path.get("client_key_path"), data.namespace)
            data_result = update_ingress_instance.replace_kube_ingress(
                data.ingress_name,
                data.host,
                data.svc_name,
                data.svc_port,
                data.path,
                data.path_type,
                data.ingress_class_name,
                data.tls,
                data.tls_secret
            )
            if data_result.get("code") == 0:
                result = updata_db_ingress(
                    item_dict.get("id"),
                    item_dict.get("env"),
                    item_dict.get("cluster_name"),
                    item_dict.get("namespace"),
                    item_dict.get("ingress_name"),
                    item_dict.get("host"),
                    item_dict.get("svc_name"),
                    item_dict.get("path"),
                    item_dict.get("path_type"),
                    item_dict.get("ingress_class_name"),
                    item_dict.get("tls"),
                    item_dict.get("tls_secret"),
                    item_dict.get("svc_port"),
                    item_dict.get("used")
                )
                if result.get("code") == 0:
                    insert_ops_bot_log("Update kube ingress app", json.dumps(user_request_data), "post", json.dumps(result))
                return result
            return {"code": 50000, "message": "update kube deploy app failure", "status": True, "data": "failure"}

    def delete_ingress(self,env_name, cluster_name, data, user_request_data):
        result_cluster_info = query_kube_db_env_cluster_all(env_name, cluster_name)
        for client_path in result_cluster_info.get("data"):
            if not (client_path.get("client_key_path")):
                return {"code": 50000, "message": "获取集群 client path  failure, 请检查问题", "status": True, "data": "failure"}
            ingress_manager = k8sIngressManager(client_path.get("client_key_path"), data["namespace"])
            result_data = ingress_manager.delete_kube_ingress(data["namespace"], data["ingress_name"])
            if result_data["code"] == 0:
                delete_instance = delete_db_ingress(data["id"])
                insert_ops_bot_log("Delete kube Ingress App", json.dumps(user_request_data), "delete",
                                   json.dumps(delete_instance))
                return delete_instance
            else:
                return {"code": 50000, "message": "delete Ingress App failure", "status": True, "data": "failure"}
