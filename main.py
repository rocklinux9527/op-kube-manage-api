# https://github.com/kubernetes-client/python/tree/master/kubernetes/docs

from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Optional, Set
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
import uvicorn
import json

# ops kube func method
from kube.kube_config import add_kube_config, get_kube_config_content, get_key_file_path, get_kube_config_dir_file, delete_kubeconfig_file
from kube.kube_deployment import k8sDeploymentManager
from kube.kube_namespace import k8sNameSpaceManager
from kube.kube_service import k8sServiceManger


from sqlalchemy.orm import sessionmaker
from sql_app.database import engine


# db ops deploy and kube config
from sql_app.ops_log_db_play import query_operate_ops_log, insert_ops_bot_log
from sql_app.kube_cnfig_db_play import insert_kube_config, updata_kube_config, delete_kube_config, query_kube_config, query_kube_env_cluster_all
from sql_app.kube_deploy_db_play import insert_kube_deployment, updata_kube_deployment, delete_kube_deployment, \
    query_kube_deployment

# db ops kube namespace
from sql_app.kube_ns_db_play import insert_db_ns, delete_db_ns, query_ns

# db ops kube service
from sql_app.kub_svc_db_play import insert_db_svc, delete_db_svc, query_kube_svc

from kube.kube_ingress import k8sIngressManager
# db ops kube ingress
from sql_app.kube_ingress_db_play import insert_db_ingress, updata_db_ingress, delete_db_ingress, query_kube_ingres

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app_name = "op-kube-manage-api"
app = FastAPI(
    title="op-kube-manage-api",
    description="kubernetes管理工具",
    version="0.0.1",
)

origins = [
    "http://0.0.0.0:8888",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class KubeConfig(BaseModel):
    env: str
    cluster_name: str
    server_address: str
    ca_data: str
    client_crt_data: str
    client_key_data: str


class updateKubeConfig(BaseModel):
    id: int
    env: str
    cluster_name: str
    server_address: str
    ca_data: str
    client_crt_data: str
    client_key_data: str
    client_key_path: str


class deleteKubeConfig(BaseModel):
    id: int
    env: str
    cluster_name: str


@app.get("/sys/ops/log/v1", summary="排查问题请求日志", tags=["sre_ops_list"])
def get_sys_ops_log(descname: Optional[str] = None, request: Optional[str] = None):
    return query_operate_ops_log(descname, request)


@app.get("/v1/kube/config/", summary="get KubeConfig k8s Plan", tags=["ConfigKubernetes"])
def get_kube_config(env: Optional[str] = None, cluster_name: Optional[str] = None, server_address: Optional[str] = None, client_key_path: Optional[str] = None):
    result_data = query_kube_config(env, cluster_name, server_address, client_key_path)
    return result_data


@app.get("/v1/kube/config/content/", summary="get KubeConfig k8s content Plan", tags=["ConfigKubernetes"])
def get_kube_config_content_v1(env: str, cluster_name: str):
    result_data = get_kube_config_content(env, cluster_name)
    return result_data


@app.get("/v1/kube/kube/file/list", summary="get KubeConfig file list", tags=["ConfigKubernetes"])
def get_kube_config_file_list():
    result_data = get_kube_config_dir_file()
    return result_data


@app.post("/v1/kube/config/", summary="Add KubeConfig K8S Plan", tags=["ConfigKubernetes"])
async def post_kube_config(ReQuest: Request, request_data: KubeConfig):
    item_dict = request_data.dict()
    from sql_app.models import KubeK8sConfig
    userRequestData = await ReQuest.json()
    from sqlalchemy.orm import sessionmaker, query
    from sql_app.database import engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    data = request_data.dict()
    result_app_name = session.query(KubeK8sConfig).filter_by(env=data.get("env"), cluster_name=data.get('cluster_name')).first()
    if data.get("env") and data.get('cluster_name') and data.get('server_address') and data.get("ca_data") and data.get(
            'client_crt_data') and data.get("client_key_data"):
        # print("表中集群字段信息result_app_name", result_app_name.env)
        if result_app_name:
            msg = '''cluster_info 环境:{env} 集群名称:{cluster} existing 提示: 已经存在,不允许覆盖操作!'''.format(env=data.get("env"),
                                                                                               cluster=data.get("cluster_name"))
            return {"code": 1, "data": msg, "message": "cluster_info Record already exists", "status": True}
        else:
            result = add_kube_config(item_dict.get("env"), item_dict.get("cluster_name"),
                                     item_dict.get("server_address"),
                                     item_dict.get("ca_data"), item_dict.get("client_crt_data"),
                                     item_dict.get("client_key_data"))
            if result.get("code") == 0:
                result_key_path = get_key_file_path(data.get("env"), data.get('cluster_name'))
                if result_key_path:
                    insertInstance = insert_kube_config(
                        data.get("env"),
                        data.get('cluster_name'),
                        data.get('server_address'),
                        data.get('ca_data'),
                        data.get("client_crt_data"),
                        data.get("client_key_data"),
                        result_key_path
                    )
                    insert_ops_bot_log("Insert kube config", json.dumps(userRequestData), "post", json.dumps(insertInstance))
                    return insertInstance
                else:
                    return {"code": 1, "messages": "create kube config file path failure ", "status": True, "data": "failure"}
            else:
                return {"code": 1, "messages": "create kube config failure ", "status": True, "data": "failure"}
    else:
        return {'code': 1, 'messages': "If the parameter is insufficient, check it", "data": "", "status": False}


@app.put("/v1/kube/config/", summary="Put KubeConfig K8S Plan", tags=["ConfigKubernetes"])
async def put_kube_config(ReQuest: Request, request_data: updateKubeConfig):
    item_dict = request_data.dict()
    userRequestData = await ReQuest.json()
    from sqlalchemy.orm import sessionmaker, query
    from sql_app.database import engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    data = request_data.dict()

    if data.get("env") and data.get('cluster_name') and data.get('server_address') and data.get("ca_data") and data.get(
            'client_crt_data') and data.get("client_key_data"):
        result = add_kube_config(item_dict.get("env"), item_dict.get("cluster_name"),
                                 item_dict.get("server_address"),
                                 item_dict.get("ca_data"), item_dict.get("client_crt_data"),
                                 item_dict.get("client_key_data"))
        if result.get("code") == 0:
            updateInstance = updata_kube_config(
                data.get("id"),
                data.get("env"),
                data.get('cluster_name'),
                data.get('server_address'),
                data.get('ca_data'),
                data.get("client_crt_data"),
                data.get("client_key_data"),
                data.get("client_key_path")
            )
            insert_ops_bot_log("Update kube config", json.dumps(userRequestData), "put", json.dumps(updateInstance))
            return updateInstance
        else:
            return {"code": 1, "messages": "update kube config failure ", "status": True, "data": "failure"}
    else:
        return {"code": 1, "messages": "Update kube config failure ", "status": True, "data": "failure"}


@app.delete("/v1/kube/config/", summary="Delete KubeConfig K8S Plan", tags=["ConfigKubernetes"])
async def delete_kube_config_v1(ReQuest: Request, request_data: deleteKubeConfig):
    item_dict = request_data.dict()
    userRequestData = await ReQuest.json()
    data = request_data.dict()
    if data.get("env") and data.get('cluster_name'):
        env, cluster_name = data.get("env"), data.get('cluster_name')
        file_name = env + "_" + cluster_name + ".conf"
        result_data = delete_kubeconfig_file(file_name)
        if result_data.get("code") == 0:
            deleteInstance = delete_kube_config(data.get("id"))
            insert_ops_bot_log("Delete kube config", json.dumps(userRequestData), "delete", json.dumps(deleteInstance))
            return deleteInstance
        else:
            return {"code": 1, "messages": "delete kube config failure ", "status": True, "data": "failure"}
    else:
        return {"code": 1, "messages": "Delete kube config failure, Incorrect parameters", "status": True, "data": "failure"}


class createNameSpace(BaseModel):
    client_config_path: str
    ns_name: str
    used: str


@app.get("/v1/sys/k8s/ns/plan/", summary="Get namespace App Plan", tags=["NamespaceKubernetes"])
def get_namespace_plan(client_config_path: Optional[str]):
    if client_config_path:
        ns_k8s_instance = k8sNameSpaceManager(client_config_path)
        ns_result = ns_k8s_instance.get_kube_all_namespaces()
        return ns_result
    else:
        data = {"code": 1, "messages": "Check the K8S configuration file  exists", "status": True, "data": "failure"}
    return data


@app.get("/v1/db/k8s/ns/plan/", summary="Get namespace App Plan", tags=["NamespaceKubernetes"])
def get_db_namespace_plan():
    db_result = query_ns()
    return {"code": 0, "messages": "query success", "data": db_result, "status": True}


@app.post("/v1/db/k8s/ns/plan/", summary="Add namespace App Plan", tags=["NamespaceKubernetes"])
async def post_namespace_plan(ReQuest: Request, request_data: createNameSpace):
    item_dict = request_data.dict()
    from sql_app.models import DeployNsData
    userRequestData = await ReQuest.json()
    from sqlalchemy.orm import sessionmaker, query
    from sql_app.database import engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    data = request_data.dict()
    result_ns_name = session.query(DeployNsData).filter_by(ns_name=data.get("ns_name")).all()
    if data.get("ns_name") and data.get('used'):
        if result_ns_name:
            msg = '''Namespace_info namespace: {ns_name} existing 提示: 已经存在,不允许覆盖操作!'''.format(ns_name=data.get("ns_name"))
            return {"code": 1, "data": msg, "message": "Namespace_info Record already exists", "status": True}
        else:
            insert_ns_instance = k8sNameSpaceManager(data.get('client_config_path'))
            insert_result_data = insert_ns_instance.create_kube_namespaces(data.get("ns_name"))
            if insert_result_data.get("code") == 0:
                result = insert_db_ns(item_dict.get("ns_name"), item_dict.get("used"))
                if result.get("code") == 0:
                    insert_ops_bot_log("Insert kube namespace ", json.dumps(userRequestData), "post", json.dumps(result))
                    return result
                else:
                    return {"code": 1, "messages": "create kube namespace  failure ", "status": True, "data": "failure"}
            else:
                return insert_result_data
    else:
        return {'code': 1, 'messages': "If the parameter is insufficient, check it", "data": "", "status": False}


class CreateDeployK8S(BaseModel):
    client_config_path: str
    app_name: str
    env: str
    cluster: str
    namespace: str
    resources: str = "0.5c1g"
    replicas: int = "1"
    image: str
    affinity: str = None
    ant_affinity: str = None
    deploy_env: str = None
    ports: int = 80
    volumeMounts: str = None
    volume: str = None
    image_pull_secrets: str = None
    health_liven_ess: str = None
    health_readiness: str = None


class UpdateDeployK8S(BaseModel):
    deployment_name: str
    id: int
    client_config_path: str
    app_name: str
    env: str
    cluster: str
    namespace: str
    resources: str
    replicas: int
    image: str
    affinity: str = None
    ant_affinity: str = None
    deploy_env: str = "name=TEST,value=test"
    ports: int = None
    volumeMounts: str = None
    volume: str = None
    image_pull_secrets: str = None
    health_liven_ess: str = None
    health_readiness: str = None


class deleteDeployK8S(BaseModel):
    id: int
    app_name: str
    namespace: str
    client_config_path: str


@app.post("/v1/k8s/deployment/plan/", summary="Add deployment App Plan", tags=["DeployKubernetes"])
def post_deploy_plan(ReQuest: Request, request_data: CreateDeployK8S):
    item_dict = request_data.dict()
    from sql_app.models import DeployK8sData
    userRequestData = ReQuest.json()
    from sqlalchemy.orm import sessionmaker, query
    from sql_app.database import engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    data = request_data.dict()
    result_Cluster_Info = query_kube_env_cluster_all()
    clusterList = result_Cluster_Info.get("env")
    print("环境存在", clusterList)
    if data.get("env") in clusterList:
        result_deploy_name = session.query(DeployK8sData).filter_by(app_name=data.get("app_name")).all()
        if data.get('cluster') and data.get('namespace') and data.get("app_name") and data.get(
                'replicas') and data.get("image") and data.get('client_config_path'):
            # print("表中集群字段信息result_app_name", result_app_name.env)
            if result_deploy_name:
                msg = '''App_info 环境:{env} 集群:{cluster} APP应用: {app_name} existing 提示: 已经存在,不允许覆盖操作!'''.format(
                    env=data.get("env"),
                    cluster=data.get("cluster"), app_name=data.get("app_name"))
                return {"code": 1, "data": msg, "message": "App_info Record already exists", "status": True}
            else:
                deploy_env = data.get("deploy_env")
                deployEnv = {}
                try:
                    for deploy_env in deploy_env.split(","):
                        k = deploy_env.split("=")[0]
                        v = deploy_env.split("=")[1]
                        deployEnv[k] = v
                except Exception as e:
                    msg = "Failed to create Deployment  because the deploy env format is incorrect"
                    return {"code": 1, "data": str(e), "message": msg, "status": True}

                insert_deploy_instance = k8sDeploymentManager(data.get('client_config_path'),
                                                              data.get('namespace'))
                insert_result_data = insert_deploy_instance.create_kube_deployment(data.get('namespace'), data.get("app_name"),
                                                                                   data.get("resources"), data.get("replicas"),
                                                                                   data.get("image"), deployEnv, data.get("ports")
                                                                                   )
                if insert_result_data.get("code") == 0:
                    result = insert_kube_deployment(item_dict.get("app_name"), item_dict.get("env"),
                                                    item_dict.get("cluster"), item_dict.get("namespace"),
                                                    item_dict.get("resources"), item_dict.get("replicas"), item_dict.get("image"),
                                                    item_dict.get("affinity"), item_dict.get("ant_affinity"),
                                                    item_dict.get("deploy_env"),
                                                    item_dict.get("ports"), item_dict.get("volumeMounts"), item_dict.get("volume"),
                                                    item_dict.get("image_pull_secrets"), item_dict.get("health_liven_ess"),
                                                    item_dict.get("health_readiness"), "")
                    if result.get("code") == 0:
                        insert_ops_bot_log("Insert kube deploy app ", json.dumps(userRequestData), "post", json.dumps(result))
                        return result
                    else:
                        return {"code": 1, "messages": "create kube deploy app failure ", "status": True, "data": "failure"}
                else:
                    return insert_result_data
        else:
            return {'code': 1, 'messages': "If the parameter is insufficient, check it", "data": "", "status": False}
    else:
        return {'code': 1, 'messages': "Configure the {name} env cluster to be in use first".format(name=data.get("env")), "data": "", "status": False}


@app.put("/v1/k8s/deployment/plan/", summary="Change deployment App Plan", tags=["DeployKubernetes"])
async def put_deploy_plan(ReQuest: Request, request_data: UpdateDeployK8S):
    item_dict = request_data.dict()
    from sql_app.models import DeployK8sData
    userRequestData = await ReQuest.json()
    from sqlalchemy.orm import sessionmaker, query
    from sql_app.database import engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    data = request_data.dict()
    if data.get("env") and data.get('cluster') and data.get('namespace') and data.get("app_name") and data.get(
            'replicas') and data.get("image") and data.get('client_config_path'):
        update_deploy_instance = k8sDeploymentManager(data.get('client_config_path'),
                                                      data.get('namespace'))
        data_result = update_deploy_instance.replace_kube_deployment(data.get('deployment_name'),
                                                                     data.get('replicas'),
                                                                     data.get("image"),
                                                                     data.get('namespace')
                                                                     )
        if data_result.get("code") == 0:
            result = updata_kube_deployment(
                item_dict.get("id"),
                item_dict.get("app_name"), item_dict.get("env"),
                item_dict.get("cluster"), item_dict.get("namespace"),
                item_dict.get("resources"), item_dict.get("replicas"), item_dict.get("image"),
                item_dict.get("affinity"), item_dict.get("ant_affinity"), item_dict.get("deploy_env"),
                item_dict.get("ports"), item_dict.get("volumeMounts"), item_dict.get("volume"),
                item_dict.get("image_pull_secrets"), item_dict.get("health_liven_ess"),
                item_dict.get("health_readiness"), "")
            if result.get("code") == 0:
                insert_ops_bot_log("Update kube deploy app ", json.dumps(userRequestData), "post", json.dumps(result))
                return result
        else:
            return {"code": 1, "messages": "update kube deploy app failure ", "status": True, "data": "failure"}
    else:
        return {'code': 1, 'messages': "If the parameter is insufficient, check it", "data": "", "status": False}


@app.get("/v1/k8s/deployment/plan/", summary="Get deployment App Plan", tags=["DeployKubernetes"])
def get_deploy_plan(env: Optional[str] = None, cluster: Optional[str] = None, app_name: Optional[str] = None,
                    image: Optional[str] = None, ports: Optional[str] = None,
                    image_pull_secrets: Optional[str] = None, deploy_id: Optional[int] = None):
    result_data = query_kube_deployment(env, cluster, app_name, image, ports, image_pull_secrets, deploy_id)
    return result_data


@app.delete("/v1/k8s/deployment/plan/", summary="Delete deployment App Plan", tags=["DeployKubernetes"])
async def del_deploy_plan(ReQuest: Request, request_data: deleteKubeConfig):
    item_dict = request_data.dict()
    from sql_app.models import DeployK8sData
    userRequestData = await ReQuest.json()
    data = request_data.dict()
    if data.get("app_name") and data.get('namespace') and data.get('client_config_path'):
        delete_deploy_instance = k8sDeploymentManager(data.get('client_config_path'), data.get('namespace'))
        result_data = delete_deploy_instance.delete_kube_deployment(data.get('namespace'), data.get("app_name"))
        if result_data.get("code") == 0:
            deleteInstance = deleteDeployK8S(data.get("id"))
            insert_ops_bot_log("Delete kube Deploy App", json.dumps(userRequestData), "delete", json.dumps(deleteInstance))
            return deleteInstance
        else:
            return {"code": 1, "messages": "delete deploy App  failure ", "status": True, "data": "failure"}
    else:
        return {"code": 1, "messages": "Delete deploy App failure, Incorrect parameters", "status": True, "data": "failure"}


class CreateSvcK8S(BaseModel):
    client_config_path: str
    namespace: str
    svc_name: str
    selector_labels: str = "app=web,name=test_svc"
    svc_port: int
    svc_type: str = "ClusterIP"
    target_port: int


class UpdateSvcK8S(BaseModel):
    id: int
    client_config_path: str
    namespace: str
    svc_name: str
    selector_labels: str
    svc_port: int
    svc_type: str = "ClusterIP"
    target_port: int


class deleteSvcK8S(BaseModel):
    id: int
    namespace: str
    svc_name: str
    client_config_path: str


@app.post("/v1/k8s/service/plan/", summary="Add Service App Plan", tags=["ServiceKubernetes"])
async def post_service_plan(ReQuest: Request, request_data: CreateSvcK8S):
    item_dict = request_data.dict()
    from sql_app.models import ServiceK8sData
    userRequestData = await ReQuest.json()
    from sqlalchemy.orm import sessionmaker, query
    from sql_app.database import engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    data = request_data.dict()
    result_svc_name = session.query(ServiceK8sData).filter_by(svc_name=data.get("svc_name")).all()
    if data.get("namespace") and data.get('svc_name') and data.get("selector_labels") and data.get('svc_port') and data.get(
            'target_port') and data.get('client_config_path'):
        if result_svc_name:
            msg = '''Service_info  Service: {svc_name} existing 提示: 已经存在,不允许覆盖操作!'''.format(svc_name=data.get("svc_name"))
            return {"code": 1, "data": msg, "message": "Service_info Record already exists", "status": True}
        else:
            insert_svc_instance = k8sServiceManger(data.get('client_config_path'))
            selector_labels = data.get("selector_labels")
            labels = {}
            try:
                for sl in selector_labels.split(","):
                    k = sl.split("=")[0]
                    v = sl.split("=")[1]
                    labels[k] = v
            except Exception as e:
                msg = "Failed to create SVC because the label format is incorrect"
                return {"code": 1, "data": str(e), "message": msg, "status": True}

            insert_result_data = insert_svc_instance.create_kube_svc(data.get('namespace'), data.get("svc_name"),
                                                                     labels,
                                                                     data.get("svc_port"), data.get("target_port"),
                                                                     data.get("svc_type"))
            if insert_result_data.get("code") == 0:
                result = insert_db_svc(item_dict.get("namespace"),
                                       item_dict.get("svc_name"),
                                       item_dict.get("selector_labels"),
                                       item_dict.get("svc_port"),
                                       item_dict.get("svc_type"),
                                       item_dict.get("target_port"))
                if result.get("code") == 0:
                    insert_ops_bot_log("Insert kube service app ", json.dumps(userRequestData), "post", json.dumps(result))
                    return result
                else:
                    return {"code": 1, "messages": "create kube service app failure ", "status": True, "data": "failure"}
    else:
        return {'code': 1, 'messages': "If the parameter is insufficient, check it", "data": "", "status": False}


@app.put("/v1/k8s/service/plan/", summary="Change Service App Plan", tags=["ServiceKubernetes"])
async def put_service_plan(ReQuest: Request, request_data: UpdateSvcK8S):
    item_dict = request_data.dict()
    from sql_app.models import DeployK8sData
    userRequestData = await ReQuest.json()
    from sqlalchemy.orm import sessionmaker, query
    from sql_app.database import engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    data = request_data.dict()
    if data.get("env") and data.get('cluster') and data.get('namespace') and data.get("app_name") and data.get(
            'replicas') and data.get("image") and data.get('client_config_path'):
        update_deploy_instance = k8sDeploymentManager(data.get('client_config_path'),
                                                      data.get('namespace'))
        data_result = update_deploy_instance.replace_kube_deployment(data.get('deployment_name'),
                                                                     data.get('replicas'),
                                                                     data.get("image"),
                                                                     data.get('namespace')
                                                                     )
        if data_result.get("code") == 0:
            result = updata_kube_deployment(
                item_dict.get("id"),
                item_dict.get("app_name"), item_dict.get("env"),
                item_dict.get("cluster"), item_dict.get("namespace"),
                item_dict.get("resources"), item_dict.get("replicas"), item_dict.get("image"),
                item_dict.get("affinity"), item_dict.get("ant_affinity"), item_dict.get("deploy_env"),
                item_dict.get("ports"), item_dict.get("volumeMounts"), item_dict.get("volume"),
                item_dict.get("image_pull_secrets"), item_dict.get("health_liven_ess"),
                item_dict.get("health_readiness"), "")
            if result.get("code") == 0:
                insert_ops_bot_log("Update kube deploy app ", json.dumps(userRequestData), "post", json.dumps(result))
                return result
        else:
            return {"code": 1, "messages": "update kube deploy app failure ", "status": True, "data": "failure"}
    else:
        return {'code': 1, 'messages': "If the parameter is insufficient, check it", "data": "", "status": False}


@app.get("/v1/k8s/service/plan/", summary="Get Service App Plan", tags=["ServiceKubernetes"])
def get_service_plan(namespace: Optional[str] = None, svc_name: Optional[str] = None, svc_port: Optional[str] = None,
                     svc_type: Optional[str] = None, target_port: Optional[str] = None):
    result_data = query_kube_svc(namespace, svc_name, svc_port, svc_type, target_port)
    return result_data


@app.delete("/v1/k8s/service/plan/", summary="Delete Service App Plan", tags=["ServiceKubernetes"])
async def del_service_plan(ReQuest: Request, request_data: deleteSvcK8S):
    item_dict = request_data.dict()
    from sql_app.models import DeployK8sData
    userRequestData = await ReQuest.json()
    data = request_data.dict()
    if data.get("app_name") and data.get('namespace') and data.get('client_config_path'):
        delete_deploy_instance = k8sDeploymentManager(data.get('client_config_path'), data.get('namespace'))
        result_data = delete_deploy_instance.delete_kube_deployment(data.get('namespace'), data.get("app_name"))
        if result_data.get("code") == 0:
            deleteInstance = deleteDeployK8S(data.get("id"))
            insert_ops_bot_log("Delete kube Deploy App", json.dumps(userRequestData), "delete", json.dumps(deleteInstance))
            return deleteInstance
        else:
            return {"code": 1, "messages": "delete deploy App  failure ", "status": True, "data": "failure"}
    else:
        return {"code": 1, "messages": "Delete deploy App failure, Incorrect parameters", "status": True, "data": "failure"}


class CreateIngressK8S(BaseModel):
    client_config_path: str
    namespace: str
    ingress_name: str
    host: str
    path: str = "/"
    path_type: str = "Prefix"
    ingress_class_name: str = "nginx"
    tls: bool = 0
    tls_secret: str = ""
    svc_name: str
    svc_port: int
    used: str


class UpdateIngressK8S(BaseModel):
    id: int
    client_config_path: str
    namespace: str
    ingress_name: str
    host: str
    path: str = "/"
    path_type: str = "Prefix"
    ingress_class_name: str = "nginx"
    tls: bool = 0
    tls_secret: str = ""
    svc_name: str
    svc_port: int
    used: str


class deleteIngressK8S(BaseModel):
    id: int
    namespace: str
    ingress_name: str
    client_config_path: str


@app.post("/v1/k8s/ingress/plan/", summary="Add Ingress App Plan", tags=["IngressKubernetes"])
async def post_ingress_plan(ReQuest: Request, request_data: CreateIngressK8S):
    item_dict = request_data.dict()
    from sql_app.models import IngressK8sData
    userRequestData = await ReQuest.json()
    from sqlalchemy.orm import sessionmaker, query
    from sql_app.database import engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    data = request_data.dict()
    result_ingress_name = session.query(IngressK8sData).filter_by(ingress_name=data.get("ingress_name")).all()
    if data.get("namespace") and data.get('ingress_name') and data.get('host') and data.get(
            'svc_name') and data.get("svc_port") and data.get('client_config_path') and data.get("used"):
        if result_ingress_name:
            msg = '''Ingress_info  Service: {ingress_name} existing 提示: 已经存在,不允许覆盖操作!'''.format(
                ingress_name=data.get("ingress_name"))
            return {"code": 1, "data": msg, "message": "ingress_info Record already exists", "status": True}
        else:
            insert_ingress_instance = k8sIngressManager(data.get('client_config_path'), data.get('namespace'))
            insert_result_data = insert_ingress_instance.create_kube_ingress(data.get('ingress_name'),
                                                                             data.get("host"),
                                                                             data.get("svc_name"),
                                                                             data.get("svc_port"),
                                                                             data.get("path"),
                                                                             data.get("path_type"),
                                                                             data.get("ingress_class_name"),
                                                                             data.get("tls"),
                                                                             data.get("tls_secret")
                                                                             )
            if insert_result_data.get("code") == 0:
                result = insert_db_ingress(item_dict.get("namespace"), data.get('ingress_name'), item_dict.get("host"),
                                           item_dict.get("svc_name"),
                                           item_dict.get("path"), item_dict.get("path_type"),
                                           item_dict.get("ingress_class_name"), item_dict.get("tls"),
                                           item_dict.get("tls_secret"),
                                           item_dict.get("svc_port"), item_dict.get("used"))
                if result.get("code") == 0:
                    insert_ops_bot_log("Insert kube ingress app ", json.dumps(userRequestData), "post", json.dumps(result))
                    return result
                else:
                    return {"code": 1, "messages": "create kube ingress failure ", "status": True, "data": "failure"}
    else:
        return {'code': 1, 'messages': "If the parameter is insufficient, check it", "data": "", "status": False}


@app.put("/v1/k8s/ingress/plan/", summary="Change Ingress App Plan", tags=["IngressKubernetes"])
async def put_ingress_plan(ReQuest: Request, request_data: UpdateIngressK8S):
    item_dict = request_data.dict()
    from sql_app.models import IngressK8sData
    userRequestData = await ReQuest.json()
    from sqlalchemy.orm import sessionmaker, query
    from sql_app.database import engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    data = request_data.dict()
    if data.get("namespace") and data.get('ingress_name') and data.get('host') and data.get("svc_port") and data.get(
            'used') and data.get("svc_name") and data.get('client_config_path'):
        update_ingress_instance = k8sIngressManager(data.get('client_config_path'), data.get('namespace'))
        data_result = update_ingress_instance.replace_kube_ingress(
            data.get('ingress_name'),
            data.get('host'),
            data.get("svc_name"),
            data.get('svc_port'),
            data.get('path'),
            data.get('path_type'),
            data.get('ingress_class_name'),
            data.get('tls'),
            data.get("tls_secret")
        )
        if data_result.get("code") == 0:
            result = updata_db_ingress(
                item_dict.get("id"),
                item_dict.get("namespace"), item_dict.get("ingress_name"),
                item_dict.get("host"), item_dict.get("svc_name"),
                item_dict.get("path"),
                item_dict.get("path_type"), item_dict.get("ingress_class_name"), item_dict.get("tls"),
                item_dict.get("tls_secret"),
                item_dict.get("svc_port"), item_dict.get("used")
            )
            if result.get("code") == 0:
                insert_ops_bot_log("Update kube ingress  app ", json.dumps(userRequestData), "post", json.dumps(result))
                return result
        else:
            return {"code": 1, "messages": "update kube deploy app failure ", "status": True, "data": "failure"}
    else:
        return {'code': 1, 'messages': "If the parameter is insufficient, check it", "data": "", "status": False}


@app.get("/v1/k8s/ingress/plan/", summary="Get Ingress App Plan", tags=["IngressKubernetes"])
def get_ingress_plan(namespace: Optional[str] = None, ingress_name: Optional[str] = None, host: Optional[str] = None,
                     svc_name: Optional[str] = None, svc_port: Optional[str] = None, tls: Optional[str] = None,
                     tls_secret: Optional[str] = None):
    result_data = query_kube_ingres(namespace, ingress_name, host, svc_name, svc_port, tls, tls_secret)
    return result_data


@app.get("/v1/k8s/sys/ingress/", summary="Get sys Ingress App Plan", tags=["IngressKubernetesSys"])
def get_sys_ingress_plan(client_config_path: Optional[str]):
    if client_config_path:
        ns_k8s_instance = k8sIngressManager(client_config_path, "dev")
        ns_result = ns_k8s_instance.get_kube_ingress_all()
    return ns_result


@app.delete("/v1/k8s/ingress/plan/", summary="Delete Ingress App Plan", tags=["IngressKubernetes"])
async def del_ingress_plan(ReQuest: Request, request_data: deleteIngressK8S):
    item_dict = request_data.dict()
    from sql_app.models import IngressK8sData
    userRequestData = await ReQuest.json()
    data = request_data.dict()
    if data.get("ingress_name") and data.get('namespace') and data.get('client_config_path'):
        delete_ingress_instance = k8sIngressManager(data.get('client_config_path'), data.get('namespace'))
        result_data = delete_ingress_instance.delete_kube_ingress(data.get('namespace'), data.get("ingress_name"))
        if result_data.get("code") == 0:
            deleteInstance = deleteDeployK8S(data.get("id"))
            insert_ops_bot_log("Delete kube Ingress App", json.dumps(userRequestData), "delete", json.dumps(deleteInstance))
            return deleteInstance
        else:
            return {"code": 1, "messages": "delete Ingress App  failure ", "status": True, "data": "failure"}
    else:
        return {"code": 1, "messages": "Delete Ingress App failure, Incorrect parameters", "status": True, "data": "failure"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8888, log_level="debug")
