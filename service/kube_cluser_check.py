from sql_app.kube_cnfig_db_play import query_kube_db_env_cluster_all
from kube.kube_cluster_check import check_k8s_cluster
import asyncio

class kubeClusterCheckService():
    async def kube_cluster_status_check(self, env_name, cluster_name):
        result_cluster_info = query_kube_db_env_cluster_all(env_name, cluster_name)
        if not (result_cluster_info.get("data")):
            msg = f"环境:{env_name}  集群:{cluster_name}  不存在请提前配置集群和环境"
            return {"code": 50000, "message": msg, "status": True}
        for client_path in result_cluster_info.get("data"):
            if not (client_path.get("client_key_path")):
                msg = "获取集群 client path  failure, 请检查问题"
                return {"code": 50000, "message": msg, "status": True}
            insert_cluster_instance = await asyncio.gather(check_k8s_cluster(client_config_file=client_path.get("client_key_path")))
            return insert_cluster_instance
