from sqlalchemy.orm import sessionmaker
from sql_app.models import KubeK8sConfig
import json
from kube.kube_config import add_kube_config, get_kube_config_content, get_key_file_path, get_kube_config_dir_file, \
    delete_kubeconfig_file
from sql_app.ops_log_db_play import query_operate_ops_log, insert_ops_bot_log
from sql_app.database import engine
from sql_app.kube_cnfig_db_play import insert_kube_config, updata_kube_config, delete_kube_config, query_kube_config, \
    query_kube_db_env_cluster_all, query_kube_config_id
import asyncio

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

class kubeConfigService():
    def create_kube_config(self, data, user_request_data):
        result_app_name = session.query(KubeK8sConfig).filter_by(env=data.get("env"),cluster_name=data.get('cluster_name')).first()
        if result_app_name:
            msg = f'cluster_info 环境:{data["env"]} 集群名称:{data["cluster_name"]} existing 提示: 已经存在,不允许覆盖操作!'
            return {"code": 20000, "data": msg, "message": "cluster_info Record already exists", "status": True}
        result = add_kube_config(*data.values())
        if result.get("code") != 0:
            return {"code": 50000, "messages": "create kube config failure ", "status": True, "data": "failure"}

        result_key_path = get_key_file_path(data['env'], data['cluster_name'])
        if not result_key_path:
            return {"code": 50000, "messages": "create kube config file path failure ", "status": True, "data": "failure"}

        insertInstance = insert_kube_config(*data.values(), result_key_path)
        insert_ops_bot_log("Insert kube config", json.dumps(user_request_data), "post", json.dumps(insertInstance))
        return insertInstance

    def update_kube_config(self, request_data, item_dict, userRequestData):
        result = add_kube_config(request_data['env'], request_data['cluster_name'], request_data['server_address'],
                                 request_data['ca_data'], request_data['client_crt_data'], request_data['client_key_data'])
        if result.get("code") == 0:
            db_kube_config = updata_kube_config(item_dict.get("id"), item_dict.get("env"), item_dict.get("cluster_name"),
                                                item_dict.get("server_address"),
                                                item_dict.get("ca_data"), item_dict.get("client_crt_data"),
                                                item_dict.get("client_key_data"), item_dict.get("client_key_path"))
            insert_ops_bot_log("Update kube config", json.dumps(userRequestData), "put", json.dumps(db_kube_config))
            return db_kube_config
        else:
            return {"code": 50000, "messages": "update kube config failure ", "status": True, "data": "failure"}

    async def delete_kube_config(self, item_dict, userRequestData):
        db_kube_config = query_kube_config_id(item_dict.get('id'))
        if not (db_kube_config.get("data")):
            return {"code": 50000, "messages": "KubeConfig not found", "status": True,
                    "data": "failure"}
        env = item_dict.get("env")
        cluster_name = item_dict.get('cluster_name')
        if not env or not cluster_name:
            return {"code": 50000, "messages": "Delete kube config failure, incorrect parameters", "status": True,
                    "data": "failure"}
        file_name = f"{env}_{cluster_name}.conf"
        try:
            result_data = await asyncio.gather(delete_kubeconfig_file(file_name))
            for result in result_data:
                if result["code"] != 0:
                    return {"code": 50000, "messages": "Delete kube config failure 集群配置文件不存在", "status": True,
                            "data": "failure"}
                delete_instance = delete_kube_config(item_dict.get('id'))
                insert_ops_bot_log("Delete kube config", json.dumps(userRequestData), "delete", json.dumps(delete_instance))
                return delete_instance
        except Exception as e:
            print(str(e))
            return {"code": 50000, "messages": str(e), "status": True, "data": "failure"}
