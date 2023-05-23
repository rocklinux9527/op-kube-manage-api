import json
from sql_app.models import ServiceK8sData
from sql_app.kube_cnfig_db_play import query_kube_db_env_cluster_all
from sql_app.ops_log_db_play import insert_ops_bot_log
from sql_app.database import engine
from sql_app.kub_svc_db_play import insert_db_svc, delete_db_svc, query_kube_svc, query_kube_svc_by_name, \
    updata_kube_svc, \
    query_kube_svc_by_id, query_kube_all_svc_name, query_kube_all_svc_port
from sqlalchemy.orm import sessionmaker
from kube.kube_service import K8sServiceManager
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

class kubeServiceService():
    def create_service(self, env_name, cluster_name, data, item_dict, user_request_data):
        with SessionLocal() as session:
            result_svc_name = session.query(ServiceK8sData).filter_by(svc_name=data.get("svc_name")).all()
        if result_svc_name:
            msg = f"Service_info  Service: {data.get('svc_name')} existing 提示: 已经存在,不允许覆盖操作!"
            return {"code": 1, "data": msg, "message": "Service_info Record already exists", "status": True}
        else:
            result_cluster_info = query_kube_db_env_cluster_all(env_name, cluster_name)
            if not (result_cluster_info.get("data")):
                return {"code": 50000, "message": f"环境:{env_name}  集群:{cluster_name}  不存在请提前配置集群和环境", "status": True}
            for client_path in result_cluster_info.get("data"):
                if not (client_path.get("client_key_path")):
                    return {"code": 50000, "message": "获取集群 client path  failure, 请检查问题", "status": True}
                insert_svc_instance = K8sServiceManager(client_path.get("client_key_path"))
                selector_labels = data.get("selector_labels")
                labels = {}
                try:
                    for sl in selector_labels.split(","):
                        k, v = sl.split("=")
                        labels[k] = v
                except Exception as e:
                    print(e)
                    return "Failed to create SVC because the label format is incorrect"
                namespace_name = data.get("namespace")
                svc_name = data.get('svc_name')
                svc_port = data.get('svc_port')
                target_port = data.get('target_port')
                svc_type = data.get('svc_type')

                insert_result_data = insert_svc_instance.create_kube_svc(namespace_name, svc_name, svc_port,
                                                                         target_port,
                                                                         svc_type, labels)
                if insert_result_data.get("code") == 0:
                    insert_db_result_data = insert_db_svc(item_dict.get("env"),
                                                          item_dict.get("cluster_name"),
                                                          item_dict.get("namespace"),
                                                          item_dict.get("svc_name"),
                                                          item_dict.get("selector_labels"),
                                                          item_dict.get("svc_port"),
                                                          item_dict.get("svc_type"),
                                                          item_dict.get("target_port")
                                                          )
                    insert_ops_bot_log("Insert kube service app ", json.dumps(user_request_data), "post",
                                       json.dumps(insert_db_result_data))
                return insert_db_result_data

    def update_service(self, ID, env_name, cluster_name, svc_name, namespace_name, selector_labels, svc_port,
                       target_port, service_type, user_request_data):
        svc_by_id = query_kube_svc_by_id(ID)
        if not (svc_by_id.get("data")):
            return {"code": 50000, "data": "", "message": "db is service  id not found", "status": True}
        service = query_kube_svc_by_name(env_name, cluster_name, svc_name, namespace_name)
        if not (service.get("data")):
            msg="service cluster {cl} info not found".format(cl=cluster_name)
            return {"code": 50000, "data": "", "message":msg, "status": True}
        result_cluster_info = query_kube_db_env_cluster_all(env_name, cluster_name)
        if not (result_cluster_info.get("data")):
            msg = f"环境:{env_name}  集群:{cluster_name}  不存在请提前配置集群和环境"
            return {"code": 50000, "data": "", "message": msg, "status": True}
        labels = {}
        try:
            for sl in selector_labels.split(","):
                k, v = sl.split("=")
                labels[k] = v
        except Exception as e:
            return "Failed to create SVC because the label format is incorrect"
        for client_path in result_cluster_info.get("data"):
            if not (client_path.get("client_key_path")):
                msg = "获取集群 client path  failure, 请检查问题"
                return {"code": 50000, "data": "", "message": msg, "status": True}
            update_svc_instance = K8sServiceManager(client_path.get("client_key_path"))
            data_result = update_svc_instance.replace_kube_svc(namespace_name, svc_name, svc_port, target_port, labels,
                                                               service_type)
            if data_result.get("code") == 0:
                updated_svc = updata_kube_svc(ID, env_name, cluster_name, namespace_name, svc_name, selector_labels,
                                              svc_port,
                                              service_type, target_port)
                if updated_svc:
                    insert_ops_bot_log("Update kube deploy app ", json.dumps(user_request_data), "post",
                                       json.dumps(updated_svc))
                    return updated_svc
            msg = "Failed to update kube service app"
            return {"code": 50000, "data": "", "message": msg, "status": True}

    def delete_service(self, app_id, env_name, cluster_name, namespace_name, svc_name, userRequestData):
        result_cluster_info = query_kube_db_env_cluster_all(env_name, cluster_name)
        for client_path in result_cluster_info.get("data"):
            if not (client_path.get("client_key_path")):
                msg = "获取集群 client path  failure, 请检查问题"
                return {"code": 50000, "data": "", "message": msg, "status": True}
            delete_svc_instance = K8sServiceManager(client_path.get("client_key_path"))
            result_data = delete_svc_instance.delete_kube_svc(namespace_name, svc_name)
            if result_data.get("code") == 0:
                delete_instance = delete_db_svc(app_id)
                insert_ops_bot_log("Delete kube Deploy App", json.dumps(userRequestData), "delete",
                                   json.dumps(delete_instance))
                return delete_instance
            else:
                msg = "Delete deploy App failure"
                return {"code": 50000, "data": "", "message": msg, "status": True}
