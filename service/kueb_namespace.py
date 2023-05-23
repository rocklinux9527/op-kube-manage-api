import json

from kube.kube_namespace import K8sNamespaceManager
from sql_app.kube_cnfig_db_play import query_kube_db_env_cluster_all
from sql_app.kube_ns_db_play import insert_db_ns, query_ns_any
from sql_app.ops_log_db_play import insert_ops_bot_log


class kubeNameSpaceService():
    def re_message(self, data, msg):
        if msg:
            return {"code": 50000, "data": data, "message": msg, "status": True}
        else:
            return {"code": 50000, "data": "", "message": "没有msg,禁止使用", "status": False}

    def create_namespace(self, data, env_name, cluster_name, namespace_name, user_request_data):
        cluster_info = query_kube_db_env_cluster_all(env_name, cluster_name)
        if not (cluster_info.get("data")):
            msg = f"环境:{env_name}  集群:{cluster_name}  不存在请提前配置集群和环境"
            data = ""
            return self.re_message(data, msg)
        result_ns_name = query_ns_any(env_name, cluster_name, namespace_name)
        if result_ns_name.get("data"):
            data = f" env {env_name} cluster_name {cluster_name} Namespace_info namespace: {namespace_name} existing 提示: 已经存在,不允许覆盖操作!"
            message = "Namespace_info Record already exists"
            return self.re_message(data, message)
        else:
            for client_path in cluster_info.get("data"):
                if not (client_path.get("client_key_path")):
                    data = ""
                    message = "获取集群 client path  failure, 请检查问题"
                    return self.re_message(data, message)
                insert_ns_instance = K8sNamespaceManager(client_path.get("client_key_path"))
                insert_result_data = insert_ns_instance.create_kube_namespaces(namespace_name)
                if insert_result_data.get("code") != 20000:
                    return self.re_message(data="", msg=insert_result_data)
                result = insert_db_ns(env_name, cluster_name, data.get("ns_name"), data.get("used"))
                if result.get("code") != 20000:
                    message = "create kube namespace  failure"
                    return self.re_message(data="", msg=message)
                insert_ops_bot_log("Insert kube namespace ", json.dumps(user_request_data), "post", json.dumps(result))
                return result
