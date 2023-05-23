import datetime
import random
import json
from sql_app.database import engine
from sqlalchemy.orm import sessionmaker
from sql_app.models import DeployK8sData
from sql_app.ops_log_db_play import insert_ops_bot_log
from sql_app.kube_cnfig_db_play import query_kube_db_env_cluster_all
from sql_app.kube_deploy_db_play import insert_kube_deployment, updata_kube_deployment, delete_kube_deployment, \
    query_kube_deployment, query_kube_deployment_by_name
from kube.kube_deployment import k8sDeploymentManager
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()


class kubeDeploymentService():
    def generate_deployment_id(self):
        current_date = datetime.datetime.now().strftime("%Y%m%d")
        random_string = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=4))
        deployment_id = f"{current_date}-{random_string}"
        return deployment_id

    def create_deployment(self, env_name, cluster_name, data, user_request_data, health_liven_ess_path, health_readiness_path,item_dict):
        result_deploy_name = query_kube_deployment_by_name(env_name, cluster_name, data.get("app_name"),
                                                           data.get("namespace"))
        if result_deploy_name.get("data"):
            msg = f'''App_info 环境:{env_name} 集群:{cluster_name} APP应用: {data.get("app_name")} existing 提示: 已经存在,不允许覆盖操作!'''
            return {"code": 50000, "message": msg, "status": True}
        result_cluster_info = query_kube_db_env_cluster_all(env_name, cluster_name)
        if not (result_cluster_info.get("data")):
            msg = f"环境:{env_name}  集群:{cluster_name}  不存在请提前配置集群和环境"
            return {"code": 50000, "message": msg, "status": True}
        for client_path in result_cluster_info.get("data"):
            if not (client_path.get("client_key_path")):
                msg = "获取集群 client path  failure, 请检查问题"
                return {"code": 50000, "message": msg, "status": True}
            deploy_env = data.get("deploy_env")
            if isinstance(deploy_env, str):
                try:
                    deploy_env_dict = dict(kv.split('=') for kv in deploy_env.split(','))
                except ValueError:
                    deploy_env_dict = {deploy_env.split('=')[0]: deploy_env.split('=')[1]}
            elif isinstance(deploy_env, dict):
                deploy_env_dict = deploy_env
            else:
                msg = "deploy_env must be a string or dictionary"
                return {"code": 50000, "message": msg, "status": True}
            insert_deploy_instance = k8sDeploymentManager(client_path.get("client_key_path"), data.get('namespace'))
            insert_result_data = insert_deploy_instance.create_kube_deployment(
                data.get('namespace'), data.get("app_name"), data.get("resources"), data.get("replicas"),
                data.get("image"), deploy_env_dict, data.get("ports"), health_liven_ess_path, health_readiness_path)
            if insert_result_data.get("code") != 20000:
                return {"code": 50000, "message": insert_result_data.get("message"), "status": True}
            deploy_id = self.generate_deployment_id()
            result = insert_kube_deployment(item_dict.get("app_name"), item_dict.get("env"),
                                            item_dict.get("cluster"),
                                            item_dict.get("namespace"), item_dict.get("resources"),
                                            item_dict.get("replicas"), item_dict.get("image"),
                                            item_dict.get("affinity"),
                                            item_dict.get("ant_affinity"), item_dict.get("deploy_env"),
                                            item_dict.get("ports"), item_dict.get("volumeMounts"),
                                            item_dict.get("volume"),
                                            item_dict.get("image_pull_secrets"), item_dict.get("health_liven_ess"),
                                            item_dict.get("health_readiness"), deploy_id)
            insert_ops_bot_log("Insert kube deploy app ", json.dumps(user_request_data), "post", json.dumps(result))
            return result

    def update_deployment(self, env_name, cluster_name, data, user_request_data, item_dict, container_port_name, resources_name, health_liven_ess_path, health_readiness_path):
        deployment = session.query(DeployK8sData).filter(DeployK8sData.id == data.get('id')).first()
        if not deployment:
            return {"code": 50000, "message": "Deployment not found", "status": True}
        deploy_env = data.get("deploy_env")
        if isinstance(deploy_env, str):
            try:
                deploy_env_dict = dict(kv.split('=') for kv in deploy_env.split(','))
            except ValueError:
                deploy_env_dict = {deploy_env.split('=')[0]: deploy_env.split('=')[1]}
        elif isinstance(deploy_env, dict):
            deploy_env_dict = deploy_env
        else:
            msg = "deploy_env must be a string or dictionary"
            return {"code": 50000, "message": msg, "status": True}
        result_cluster_info = query_kube_db_env_cluster_all(env_name, cluster_name)
        for client_path in result_cluster_info.get("data"):
            if not (client_path.get("client_key_path")):
                return {"code": 50000, "message": "获取集群 client path  failure, 请检查问题", "status": True}
            update_deploy_instance = k8sDeploymentManager(client_path.get("client_key_path"), data.get('namespace'))
            data_result = update_deploy_instance.replace_kube_deployment(data.get('deployment_name'),
                                                                         item_dict.get("replicas"), data.get("image"),
                                                                         data.get('namespace'), resources_name,
                                                                         deploy_env_dict,
                                                                         container_port_name, health_liven_ess_path,
                                                                         health_readiness_path)
            if data_result.get("code") != 0:
                return {"code": 50000, "message": "Failed to update kubernetes deployment", "status": True}
            update_id = self.generate_deployment_id()
            result = updata_kube_deployment(data.get('id'), item_dict.get("app_name"), item_dict.get("env"),
                                            item_dict.get("cluster"), item_dict.get("namespace"),
                                            item_dict.get("resources"), item_dict.get("replicas"),
                                            item_dict.get("image"), item_dict.get("affinity"),
                                            item_dict.get("ant_affinity"), item_dict.get("deploy_env"),
                                            item_dict.get("ports"), item_dict.get("volumeMounts"),
                                            item_dict.get("volume"), item_dict.get("image_pull_secrets"),
                                            item_dict.get("health_liven_ess")
                                            , item_dict.get("health_readiness"), update_id)
            insert_ops_bot_log("Update kube deploy app", json.dumps(user_request_data), "post", json.dumps(result))
            session.close()
            return result

    def delete_deployment(self, env_name, cluster_name, data, namespace_name, app_name,user_request_data):
        result_cluster_info = query_kube_db_env_cluster_all(env_name, cluster_name)
        if not (result_cluster_info.get("data")):
            msg = f"环境:{env_name}  集群:{cluster_name}  不存在请提前配置集群和环境"
            return {"code": 50000, "message": msg, "status": True}
        for client_path in result_cluster_info.get("data"):
            if not (client_path.get("client_key_path")):
                msg = "获取集群 client path  failure, 请检查问题"
                return {"code": 50000, "message": msg, "status": True}
            delete_deploy_instance = k8sDeploymentManager(client_path.get("client_key_path"), namespace_name)
            result_data = delete_deploy_instance.delete_kube_deployment(namespace_name, app_name)
            if result_data.get("code") == 0:
                delete_instance = delete_kube_deployment(data.get("id"))
                insert_ops_bot_log(
                    "Delete kube Deploy App",
                    json.dumps(user_request_data),
                    "delete",
                    json.dumps(delete_instance),
                )
                return delete_instance
            else:
                return {
                    "code": 50000,
                    "messages": "delete deploy App  failure ",
                    "status": True,
                    "data": "failure",
                }
