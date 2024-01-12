# https://github.com/kubernetes-client/python/tree/master/kubernetes/docs
# from logging


import json_logging

from typing import Optional, Dict, Any

# login token
import uvicorn
from fastapi import APIRouter, Request
from fastapi import FastAPI, HTTPException
from fastapi import Query
from fastapi import WebSocket
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBearer
from sqlalchemy.orm import sessionmaker
from starlette.middleware.cors import CORSMiddleware

# ops kube func method
from kube.kube_config import get_kube_config_content, get_kube_config_dir_file
from kube.kube_ingress import k8sIngressManager
from kube.kube_namespace import K8sNamespaceManager
# pod
from kube.kube_pod import PodManager
# 导入K8S Deployment 命名空间 相关数据结构
from schemas.k8s import CreateDeployK8S, UpdateDeployK8S, deleteDeployK8S
# 导入K8S Ingress 命名空间 相关数据结构
from schemas.k8s import CreateIngressK8S, UpdateIngressK8S, deleteIngressK8S
# 导入K8S Service 命名空间 相关数据结构
from schemas.k8s import CreateSvcK8S, UpdateSvcK8S, deleteSvcK8S
# 导入K8S kube config 相关数据结构
from schemas.k8s import KubeConfig, updateKubeConfig, deleteKubeConfig
# 导入K8S ns 命名空间 相关数据结构
from schemas.k8s import createNameSpace
# 导入K8S Pod 命名空间 相关数据结构
from schemas.k8s import postK8sRestartPodManager, postK8sPodManager, putK8sPodManager
# 导入系统模板数据结构
from schemas.template import templateManager, UpdateTemplateManager, deleteTemplateManager

# 导入App系统模板数据结构
from schemas.app_template import AddAppTemplateManager,UpdateAppTemplateManager,deleteAppTemplateManager

# 导入系统用户数据结构
from schemas.user import UserManager, updateUserManager, deleteUser
from service.kube_config import kubeConfigService

# import k8s cluster check
from service.kube_cluser_check import kubeClusterCheckService

# import mysql db connection check
from service.check_mysql_conn import check_mysql_connection

# import kube deployment
from service.kube_deployment import kubeDeploymentService
# import kube ingress
from service.kube_ingress import kubeIngressService
# import kubePodService
from service.kube_pod import kubePodService
# import kube service
from service.kube_service import kubeServiceService
# import kube namespaceService
from service.kueb_namespace import kubeNameSpaceService
# import ws service
from service.sh_ws import websocket_handler, terminal_html
# import template service
from service.sys_template import TemplateService

# import app template service
from service.sys_app_template import AppTemplateService
# import user service
from service.sys_user import UserService
from sql_app.database import engine
# db ops kube service
from sql_app.kub_svc_db_play import query_kube_svc, query_kube_all_svc_name, query_kube_all_svc_port
from sql_app.kube_cnfig_db_play import query_kube_config, \
    query_kube_db_env_cluster_all, query_kube_config_id, query_kube_db_env_all, query_kube_db_cluster_all, \
    query_kube_db_env_cluster_wrapper
from sql_app.kube_deploy_db_play import query_kube_deployment,query_search_like_deploy,query_kube_deployment_v2
# db ops kube ingress
from sql_app.kube_ingress_db_play import query_kube_ingres, \
    query_kube_ingress_by_name
# db ops kube namespace
from sql_app.kube_ns_db_play import query_ns, query_kube_db_ns_all
from sql_app.login_users import query_users, query_users_name
# db ops deploy and kube config
from sql_app.ops_log_db_play import query_operate_ops_log
# ops temple
from sql_app.ops_template import query_template,queryTemplateType
from sql_app.ops_app_template import insert_db_app_template,updata_app_template,delete_db_app_template,query_Template_app_name,query_app_template

from tools.config import setup_logger

from tools.harbor_tools_v2 import check_harbor, harbor_main_aio

# import kubeConfigService
security = HTTPBearer()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
app_name = "op-kube-manage-api"
app = FastAPI(
    title="op-kube-manage-api",
    description="kubernetes管理工具",
    version="0.0.1",
)

# 初始化和fastapi 关联
json_logging.init_fastapi(enable_json=True)
json_logging.init_request_instrument(app)


router = APIRouter()



origins = ["*", "127.0.0.1:80"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# WebSocket路由
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket_handler(websocket)


@app.get('/web_shell', response_class=HTMLResponse)
async def terminal():
    return terminal_html


@app.get("/api/sys/ops/log/v1", summary="排查问题请求日志", tags=["sre_ops_list"])
def get_sys_ops_log(descname: Optional[str] = None, request: Optional[str] = None):
    return query_operate_ops_log(descname, request)


@app.get("/api/check-mysql", summary="mysql db connection heck ", tags=["ping"])
async def check_mysql():
    result = await check_mysql_connection()
    return result


@app.get("/api/check-harbor", summary="images harbor check ", tags=["ping"])
async def checkHarbor(host: Optional[str], version: Optional[str] = "v2"):
    versionList = ["v1", "v2"]
    if version not in versionList:
        return {"code": 50000, "data": "", "message": f'需要传递版本,仅支持{versionList}', "status": False}
    result = await check_harbor(host=host, version=version)
    return result

@app.get("/api/check-kube-cluster", summary="K8S  kube cluster check ", tags=["ping"])
async def check_k8s_kube_cluster(env: Optional[str], cluster_name: Optional[str]):
    if not (cluster_name, env):
        return {"code": 50000, "data": "", "message": f'需要传环境和集群标识', "status": False}
    k8s_cluster_instance = kubeClusterCheckService()
    result = await k8s_cluster_instance.kube_cluster_status_check(env_name=env, cluster_name=cluster_name)
    return result


@app.get("/api/v1/k8s/kube/config/", summary="get KubeConfig k8s Plan", tags=["ConfigKubernetes"])
def get_kube_config(page: int = Query(1, gt=0), page_size: int = Query(10, gt=0, le=100), env: Optional[str] = None,
                    cluster_name: Optional[str] = None, server_address: Optional[str] = None,
                    client_key_path: Optional[str] = None):
    result_data = query_kube_config(page, page_size, env, cluster_name, server_address, client_key_path)
    return result_data


@app.get("/api/v1/kube/env/list/", summary="get KubeConfig k8s EnvList Plan", tags=["ConfigKubernetes"])
def get_kube_envList():
    result_data = query_kube_db_env_all()
    return result_data


@app.get("/api/v1/kube/cluster/List/", summary="get KubeConfig k8s EnvList Plan", tags=["ConfigKubernetes"])
def get_kube_clusterList():
    result_data = query_kube_db_cluster_all()
    return result_data


@app.get("/api/v1/kube/config/content/", summary="get KubeConfig k8s content Plan", tags=["ConfigKubernetes"])
def get_kube_config_content_v1(env: str, cluster_name: str):
    result_data = get_kube_config_content(env, cluster_name)
    return result_data


@app.get("/api/v1/kube/kube/file/list", summary="get KubeConfig file list", tags=["ConfigKubernetes"])
def get_kube_config_file_list():
    result_data = get_kube_config_dir_file()
    return result_data


@app.post("/api/v1/k8s/kube/config/", summary="Add KubeConfig K8S Plan", tags=["ConfigKubernetes"])
async def create_kube_config(request: Request, request_data: KubeConfig):
    user_request_data = await request.json()
    data = request_data.dict()
    if not all(data.get(field) for field in
               ['env', 'cluster_name', 'server_address', 'ca_data', 'client_crt_data', 'client_key_data']):
        return {'code': 20000, 'messages': "If the parameter is insufficient, check it", "data": "", "status": False}
    kube_config_instance = kubeConfigService()
    result = kube_config_instance.create_kube_config(data, user_request_data)
    return result


@app.put("/api/v1/k8s/kube/config/", summary="Put KubeConfig K8S Plan", tags=["ConfigKubernetes"])
async def update_kube_config(ReQuest: Request, request_data: updateKubeConfig):
    item_dict = request_data.dict()
    userRequestData = await ReQuest.json()
    db_kube_config = query_kube_config_id(item_dict.get('id'))
    if not (db_kube_config.get("data")):
        raise HTTPException(status_code=404, detail="KubeConfig not found")
    request_data = request_data.dict(exclude_unset=True)
    kube_config_instance = kubeConfigService()
    result = kube_config_instance.update_kube_config(userRequestData, request_data, item_dict)
    return result


@app.delete("/api/v1/k8s/kube/config/", summary="Delete KubeConfig K8S Plan", tags=["ConfigKubernetes"])
async def delete_kube_config_v1(ReQuest: Request, request_data: deleteKubeConfig):
    import asyncio
    item_dict = request_data.dict()
    userRequestData = await ReQuest.json()
    kube_config_instance = kubeConfigService()
    result = await asyncio.gather(kube_config_instance.delete_kube_config(item_dict, userRequestData))
    return result


@app.get("/api/v1/sys/k8s/ns/plan/", summary="Get namespace App Plan", tags=["NamespaceKubernetes"])
def get_namespace_plan(env: Optional[str], cluster: Optional[str]):
    if not (env and cluster):
        raise HTTPException(status_code=400, detail="If the parameter is insufficient, check it")
    cluster_info = query_kube_db_env_cluster_all(env, cluster)
    if not (cluster_info.get("data")):
        raise HTTPException(status_code=400, detail=f"环境:{env}  集群:{cluster}  不存在请提前配置集群和环境")

    for client_path in cluster_info.get("data"):
        if not (client_path.get("client_key_path")):
            raise HTTPException(status_code=400, detail="获取集群 client path  failure, 请检查问题")
        ns_k8s_instance = K8sNamespaceManager(client_path.get("client_key_path"))
        ns_result = ns_k8s_instance.get_kube_all_namespaces()
        return ns_result


@app.get("/api/v1/db/k8s/ns/plan/", summary="Get namespace App Plan", tags=["NamespaceKubernetes"])
def get_db_namespace_plan(page: int = Query(1, gt=0), page_size: int = Query(10, gt=0, le=100),ns_name: Optional[str] =None):
    db_result = query_ns(ns_name,page, page_size)
    return db_result


@app.get("/api/v1/db/k8s/ns/all/", summary="Get namespace App All Plan", tags=["NamespaceKubernetes"])
def get_db_namespace_plan():
    ns_all_db_result = query_kube_db_ns_all()
    return ns_all_db_result


@app.post("/api/v1/db/k8s/ns/plan/", summary="Add namespace App Plan", tags=["NamespaceKubernetes"])
async def post_namespace_plan(request: Request, request_data: createNameSpace):
    from sqlalchemy.orm import sessionmaker
    from sql_app.database import engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    data = request_data.dict()
    user_request_data = await request.json()
    namespace_name = data.get("ns_name")
    env_name = data.get("env")
    cluster_name = data.get("cluster_name")
    if not (cluster_name and env_name):
        raise HTTPException(status_code=400, detail="If the parameter is insufficient, check it")
    namespace_instance = kubeNameSpaceService()
    ns_result = namespace_instance.create_namespace(data, env_name, cluster_name, namespace_name, user_request_data)
    return ns_result


@app.get("/api/v1/kube/pod/", summary="get Pod k8s Plan", tags=["PodKubernetes"])
def get_kube_pod(env: Optional[str], cluster: Optional[str], namespace: Optional[str]):
    if not (env and cluster and namespace):
        raise HTTPException(status_code=400, detail="The cluster or environment does not exist")
    cluster_info = query_kube_db_env_cluster_all(env, cluster)
    for client_path in cluster_info.get("data"):
        if not (client_path.get("client_key_path")):
            raise HTTPException(status_code=400, detail="获取集群 client path  failure, 请检查问题")
        pod_instance = PodManager(client_path.get("client_key_path"), namespace)
        return pod_instance.get_pods(env, cluster)


@app.post("/api/v1/kube/pod/restart", summary="POST Pod Restart k8s Plan", tags=["PodKubernetes"])
def get_kube_pod_restart(request: Request, request_data: postK8sRestartPodManager):
    data = request_data.dict()
    env = data.get("env")
    cluster = data.get("cluster")
    namespace = data.get("namespace")
    pod_name = data.get("pod_name")
    pod_instance = kubePodService()
    pod_restart_result = pod_instance.kube_pod_restart(env, cluster, namespace, pod_name)
    return pod_restart_result


@app.get("/api/v1/kube/pod/mock", summary="get Pod Mock k8s Plan", tags=["PodKubernetes"])
def get_kube_mock_pod():
    from tools.config import k8sPodHeader
    return {"code": 20000, "total": 0, "data": [], "messages": "query data success", "status": True, "columns": k8sPodHeader}


@app.post("/api/v1/kube/pod/", summary="Add POD K8S Plan", tags=["PodKubernetes"])
async def create_kube_pod(request: Request, request_data: postK8sPodManager):
    data = request_data.dict()
    if not all(data.get(field) for field in
               ['env', 'cluster', 'namespace', 'pod_name', 'image', 'ports']):
        return {'code': 20000, 'messages': "If the parameter is insufficient, check it", "data": "", "status": False}
    pod_create_instance = kubePodService()
    pod_create_result = pod_create_instance.create_pod(data)
    return pod_create_result


@app.put("/api/v1/kube/pod/", summary="Put POD K8S Plan", tags=["PodKubernetes"])
def update_kube_Pod(ReQuest: Request, request_data: putK8sPodManager):
    data = request_data.dict()
    if not all(data.get(field) for field in
               ['env', 'cluster', 'namespace', 'pod_name', 'image', 'ports']):
        return {'code': 20000, 'messages': "If the parameter is insufficient, check it", "data": "", "status": False}
    pod_update_instance = kubePodService()
    pod_update_result = pod_update_instance.update(data)
    return pod_update_result


@app.post("/api/v1/k8s/deployment/plan/", summary="Add deployment App Plan", tags=["DeployKubernetes"])
async def post_deploy_plan(request: Request, request_data: CreateDeployK8S) -> Dict[str, Any]:
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    item_dict = request_data.dict()
    user_request_data = await request.json()
    data = request_data.dict()
    cluster_name = data.get("cluster")
    env_name = data.get("env")
    health_liven_ess_path = data.get("health_liven_ess")
    health_readiness_path = data.get("health_readiness")
    if not (cluster_name and env_name):
        raise HTTPException(status_code=400, detail="The cluster or environment does not exist")
    deployment_instance = kubeDeploymentService()
    deploy_instance_result = deployment_instance.create_deployment(env_name, cluster_name, data, user_request_data,
                                                                   health_liven_ess_path, health_readiness_path, item_dict)
    return deploy_instance_result


@app.put("/api/v1/k8s/deployment/plan/", summary="Change deployment App Plan", tags=["DeployKubernetes"])
async def put_deploy_plan(request: Request, request_data: UpdateDeployK8S):
    item_dict = request_data.dict()
    user_request_data = await request.json()
    data = request_data.dict()
    env_name = data.get("env")
    cluster_name = data.get("cluster")
    deployment_name = data.get('deployment_name')
    app_name = data.get('app_name')
    replicas_name = data.get('replicas')
    image_name = data.get("image")
    namespace_name = data.get('namespace')
    resources_name = data.get('resources')
    deploy_env_name = data.get('deploy_env')
    container_port_name = data.get('ports')
    health_liven_ess_path = data.get("health_liven_ess")
    health_readiness_path = data.get("health_readiness")

    if not (env_name and cluster_name and deployment_name and replicas_name
            and image_name and namespace_name and app_name
            and resources_name and deploy_env_name and container_port_name):
        raise HTTPException(status_code=400, detail="Invalid input parameters")
    deployment_update_instance = kubeDeploymentService()
    deploy_update_instance_result = deployment_update_instance.update_deployment(env_name,
                                                                                 cluster_name,
                                                                                 data,
                                                                                 user_request_data,
                                                                                 item_dict,
                                                                                 container_port_name,
                                                                                 resources_name,
                                                                                 health_liven_ess_path,
                                                                                 health_readiness_path
                                                                                 )
    return deploy_update_instance_result


@app.get("/api/v1/k8s/deployment/like", summary="Get deployment like App Plan", tags=["DeployKubernetes"])
def get_app_name_like(app_name: str = Query(..., description="模糊查询名称"), page: int = Query(1, ge=1, description="页码"),
                      page_size: int = Query(10, ge=1, description="每页条数")):
    if not (app_name):
        return {
            "code": 50000,
            "messages": "Get deploy Like App failure, Incorrect parameters",
            "status": True,
            "data": "failure"
        }
    result_data = query_search_like_deploy(app_name, page, page_size)
    return result_data

@app.get("/api/v1/k8s/deployment/plan/", summary="Get deployment App Plan", tags=["DeployKubernetes"])
def get_deploy_plan(page: int = Query(1, gt=0), page_size: int = Query(10, gt=0, le=1000), env: Optional[str] = None,
                    cluster: Optional[str] = None, app_name: Optional[str] = None,
                    image: Optional[str] = None, ports: Optional[str] = None,
                    image_pull_secrets: Optional[str] = None, deploy_id: Optional[int] = None):
    result_data = query_kube_deployment_v2(page, page_size, env, cluster, app_name, image, ports, image_pull_secrets, deploy_id)
    return result_data


@app.delete("/api/v1/k8s/deployment/plan/", summary="Delete deployment App Plan", tags=["DeployKubernetes"])
async def del_deploy_plan(request: Request, request_data: deleteDeployK8S):
    data = request_data.dict()
    user_request_data = await request.json()
    env_name = data.get("env")
    cluster_name = data.get('cluster')
    app_name = data.get("app_name")
    namespace_name = data.get('namespace')
    if not (app_name and namespace_name):
        return {
            "code": 20000,
            "messages": "Delete deploy App failure, Incorrect parameters",
            "status": True,
            "data": "failure"
        }
    delete_deployment_instance = kubeDeploymentService()
    delete_instance_result = delete_deployment_instance.delete_deployment(env_name, cluster_name, data, namespace_name, app_name,
                                                                          user_request_data)
    return delete_instance_result


@app.post("/api/v1/k8s/service/plan/", summary="Add Service App Plan", tags=["ServiceKubernetes"])
async def post_service_plan(request: Request, request_data: CreateSvcK8S):
    item_dict = request_data.dict()
    user_request_data = await request.json()
    data = request_data.dict()
    env_name = data.get("env")
    cluster_name = data.get("cluster_name")
    if not (data.get("namespace") and data.get('svc_name') and data.get("selector_labels") and
            data.get('svc_port') and data.get('target_port')):
        return {'code': 1, 'messages': "If the parameter is insufficient, check it", "data": "", "status": False}
    create_service_instance = kubeServiceService()
    create_instance_result = create_service_instance.create_service(env_name, cluster_name, data, item_dict, user_request_data)
    return create_instance_result


@app.put("/api/v1/k8s/service/plan/", summary="Change Service App Plan", tags=["ServiceKubernetes"])
async def put_service_plan(request: Request, request_data: UpdateSvcK8S):
    data = request_data.dict()
    user_request_data = await request.json()
    env_name = data.get("env")
    ID = data.get("id")
    cluster_name = data.get('cluster_name')
    namespace_name = data.get("namespace")
    svc_name = data.get("svc_name")
    svc_port = data.get("svc_port")
    target_port = data.get("target_port")
    service_type = data.get("svc_type")
    selector_labels = data.get("selector_labels")
    if not (env_name and cluster_name and namespace_name and svc_name and svc_port and target_port and selector_labels):
        raise HTTPException(status_code=400, detail="Missing parameter")
    update_service_instance = kubeServiceService()
    update_instance_result = update_service_instance.update_service(ID, env_name,
                                                                    cluster_name,
                                                                    svc_name,
                                                                    namespace_name,
                                                                    selector_labels,
                                                                    svc_port,
                                                                    target_port,
                                                                    service_type,
                                                                    user_request_data
                                                                    )
    return update_instance_result


@app.get("/api/v1/k8s/service/plan/", summary="Get Service App Plan", tags=["ServiceKubernetes"])
def get_service_plan(page: int = Query(1, gt=0), page_size: int = Query(10, gt=0, le=1000), env: Optional[str] = None,
                     cluster_name: Optional[str] = None, namespace: Optional[str] = None,
                     svc_name: Optional[str] = None, selector_labels: Optional[str] = None,
                     svc_port: Optional[str] = None,
                     svc_type: Optional[str] = None, target_port: Optional[str] = None):
    result_data = query_kube_svc(page, page_size, env, cluster_name, namespace, svc_name, selector_labels, svc_port, svc_type,
                                 target_port)
    return result_data


@app.get("/api/v1/k8s/service/all/plan/", summary="Get ALL Service App Plan", tags=["ServiceKubernetes"])
def get_all_service_plan(env: Optional[str], cluster_name: Optional[str], namespace: Optional[str]):
    if not (env and cluster_name and namespace):
        raise HTTPException(status_code=400, detail="Incorrect parameters")
    result_data = query_kube_all_svc_name(env, cluster_name, namespace)
    return result_data


@app.get("/api/v1/k8s/service/svc-port/plan/", summary="Get ALL Service Port App Plan", tags=["ServiceKubernetes"])
def get_all_service_port_plan(env: Optional[str], cluster_name: Optional[str], namespace: Optional[str], svc_name: Optional[str]):
    if not (env and cluster_name and namespace and svc_name):
        raise HTTPException(status_code=400, detail="Incorrect parameters")
    result_data = query_kube_all_svc_port(env, cluster_name, namespace, svc_name)
    return result_data


@app.delete("/api/v1/k8s/service/plan/", summary="Delete Service App Plan", tags=["ServiceKubernetes"])
async def delete_service_plan(ReQuest: Request, request_data: deleteSvcK8S):
    svc_name = request_data.svc_name
    data = request_data.dict()
    env_name = data.get("env")
    cluster_name = data.get("cluster_name")
    app_id = data.get("id")
    namespace_name = request_data.namespace
    userRequestData = await ReQuest.json()
    if not (svc_name and namespace_name):
        raise HTTPException(status_code=400, detail="Incorrect parameters")
    if not (env_name and cluster_name):
        raise HTTPException(status_code=400, detail="Incorrect cluster or env parameters")
    delete_service_instance = kubeServiceService()
    delete_instance_result = delete_service_instance.delete_service(app_id, env_name, cluster_name, namespace_name, svc_name,
                                                                    userRequestData)
    return delete_instance_result


@app.post("/api/v1/k8s/ingress/plan/", summary="Add Ingress App Plan", tags=["IngressKubernetes"])
async def post_ingress_plan(ReQuest: Request, request_data: CreateIngressK8S):
    user_request_data = await ReQuest.json()
    env_name = request_data.env
    cluster_name = request_data.cluster_name
    namespace_name = request_data.namespace
    ingress_name = request_data.ingress_name
    host_name = request_data.host
    path_name = request_data.path
    path_type = request_data.path_type
    ingress_class_name = request_data.ingress_class_name
    tls_name = request_data.tls
    tls_secret = request_data.tls_secret
    svc_name = request_data.svc_name
    svc_port = request_data.svc_port
    used = request_data.used
    if not all([namespace_name, ingress_name, host_name, svc_name, svc_port, used]):
        raise HTTPException(status_code=400, detail="Invalid request data")

    result_ingress_name = query_kube_ingress_by_name(env_name, cluster_name, ingress_name, namespace_name)
    if result_ingress_name.get("data"):
        raise HTTPException(status_code=409, detail=f"Ingress {ingress_name} already exists")
    create_ingress_instance = kubeIngressService()
    create_instance_result = create_ingress_instance.create_ingress(
        env_name, cluster_name, namespace_name, ingress_name,
        host_name, svc_name, svc_port, path_name, path_type,
        ingress_class_name, tls_name, tls_secret, used, user_request_data
    )
    return create_instance_result


@app.put("/api/v1/k8s/ingress/plan/", summary="Change Ingress App Plan", tags=["IngressKubernetes"])
async def put_ingress_plan(request: Request, data: UpdateIngressK8S):
    item_dict = data.dict()
    user_request_data = await request.json()
    ID = data.id
    env_name = data.env
    cluster_name = data.cluster_name
    namespace_name = data.namespace
    ingres_name = data.ingress_name
    host_name = data.host
    svc_name = data.svc_name
    svc_port = data.svc_port
    used = data.used
    if not (namespace_name and ingres_name and host_name and svc_name and svc_port and used):
        return {'code': 1, 'messages': "If the parameter is insufficient, check it", "data": "", "status": False}
    update_ingress_instance = kubeIngressService()
    update_instance_result = update_ingress_instance.update_ingress(ID, env_name, cluster_name, data, item_dict,
                                                                    user_request_data)
    return update_instance_result


@app.get("/api/v1/k8s/ingress/plan/", summary="Get Ingress App Plan", tags=["IngressKubernetes"])
def get_ingress_plan(page: int = Query(1, gt=0), page_size: int = Query(10, gt=0, le=1000), env: Optional[str] = None,
                     cluster_name: Optional[str] = None, namespace: Optional[str] = None,
                     ingress_name: Optional[str] = None, host: Optional[str] = None,
                     svc_name: Optional[str] = None, svc_port: Optional[str] = None, tls: Optional[str] = None,
                     tls_secret: Optional[str] = None):
    result_data = query_kube_ingres(page, page_size, env, cluster_name, namespace, ingress_name, host, svc_name, svc_port, tls,
                                    tls_secret)
    return result_data


@app.get("/api/v1/k8s/sys/ns-by-ingress/", summary="Get sys Ingress App Plan", tags=["IngressKubernetesSys"])
def get_ns_by_ingress_plan(env: Optional[str] = None, cluster_name: Optional[str] = None,
                           namespace: Optional[str] = None):
    k8s_instance = k8sIngressManager(cluster_name,namespace)
    ns_result = k8s_instance.get_kube_ingress_by_name()
    return ns_result


@app.get("/api/v1/k8s/sys/ns-all-ingress/", summary="Get sys Ingress App Plan", tags=["IngressKubernetesSys"])
@query_kube_db_env_cluster_wrapper()
def get_ns_all_ingress_plan(k8s_instance: k8sIngressManager, env: Optional[str] = None,
                            cluster_name: Optional[str] = None):
    ns_k8s_instance = k8sIngressManager(k8s_instance, "dev")
    ns_result = ns_k8s_instance.get_kube_ingress_all()
    return ns_result


@app.delete("/api/v1/k8s/ingress/plan/", summary="Delete Ingress App Plan", tags=["IngressKubernetes"])
async def delete_ingress_plan(request: Request, request_data: deleteIngressK8S):
    data = request_data.dict()
    user_request_data = await request.json()
    env_name = request_data.env
    cluster_name = request_data.cluster_name
    if not all(data.values()):
        return {"code": 1, "messages": "Delete Ingress App failure, Incorrect parameters", "status": True,
                "data": "failure"}
    delete_ingress_instance = kubeIngressService()
    delete_instance_result = delete_ingress_instance.delete_ingress(env_name, cluster_name, data, user_request_data)
    return delete_instance_result


@app.post("/api/user/login/", summary="用户登录验证，如果成功返回用户 token，否则返回 HTTP 401 错误", tags=["sys-login-user"])
def login(request: Request, request_data: UserManager):
    data = request_data.dict()
    username = data.get("username")
    password = data.get("password")
    data = request_data.dict()
    if not all(data.get(field) for field in ['username', 'password']):
        return {'code': 20000, 'messages': "账号或者密码没有传递, 请检查!", "data": "", "status": False}
    auth_user_instance = UserService(username, password)
    if not auth_user_instance.authenticate_db_user():
        return {"code": 401, "message": "账号或者密码不正确,请检查!", "statue": True}
    token_result = auth_user_instance.login_auth()
    if token_result.get("code") == 20000:
        data = token_result
    else:
        data = {
            'username': username,
            'code': 50000,
            'message': "Description Failed to generate a token based on user information",
            'data': {
                'token': "",
                'token_type': 'Bearer'
            }
        }
    return data


@app.get("/api/user/info", summary="验证 JWT token，如果验证成功，返回用户名", tags=["sys-login-user"])
def protected(token):
    if not (token):
        raise HTTPException(status_code=400, detail="Missing parameter")
        return {"code": 50000, "message": "Missing parameter", "statue": True}
    return UserService.protected_token(token)


@app.post("/api/user/logout", summary="get logout user to  jwt token ", tags=["sys-login-user"])
def logout():
    return UserService.logout_msg()


@app.post("/api/user/add", summary="add user  ", tags=["sys-users"])
async def useradd(request: Request, request_data: UserManager):
    data = request_data.dict()
    user_request_data = await request.json()
    if not all(data.get(field) for field in
               ['username', 'password']):
        return {'code': 20000, 'messages': "If the parameter is insufficient, check it", "data": "", "status": False}
    username = data.get("username")
    password = data.get("password")
    userInstance = UserService(username, password)
    user_result = userInstance.add_user(user_request_data)
    return user_result


@app.get("/api/user/query", summary="query user", tags=["sys-users"])
def get_deploy_plan(page: int = Query(1, gt=0), page_size: int = Query(10, gt=0, le=1000)):
    result_data = query_users(page, page_size)
    return result_data


@app.delete("/api/user/delete", summary="Delete users Plan", tags=["sys-users"])
async def delete_users(request: Request, request_data: deleteUser):
    data = request_data.dict()
    user_request_data = await request.json()
    id = request_data.id
    username = request_data.username
    if not all(data.values()):
        return {"code": 1, "messages": "Delete Users  failure, Incorrect parameters", "status": True,
                "data": "failure"}
    result_username = query_users_name(username)
    if not result_username.get("data"):
        raise HTTPException(status_code=409, detail=f"User {username} not exists already,删除失败")
    userInstance = UserService(username, password="")
    user_result = userInstance.delete_user(id, user_request_data)
    return user_result


@app.put("/api/user/update", summary="User Update Plan", tags=["sys-users"])
async def put_user_update(request: Request, request_data: updateUserManager):
    data = request_data.dict()
    user_request_data = await request.json()
    username = data.get("username")
    ID = data.get("id")
    new_password = data.get('password')
    if not (username and new_password and ID):
        raise HTTPException(status_code=400, detail="Missing parameter")
    userInstance = UserService(username, new_password)
    user_result = userInstance.update_user(ID, user_request_data)
    return user_result


@app.get("/api/template", summary="query template", tags=["sys-template"])
def get_template_plan(q_type: str = "all", page: int = Query(1, gt=0), page_size: int = Query(10, gt=0, le=1000)):
    if q_type == "all":
        result_data = query_template(page, page_size)
    else:
        result_data = queryTemplateType(q_type, page, page_size)
    return result_data

@app.post("/api/template", summary="模板自定义模板", tags=["sys-template"])
def save_template(request_data: templateManager):
    data = request_data.dict()
    name = data.get("name")
    content = data.get("content")
    type = data.get("t_type")
    language = data.get("language")
    remark = data.get("remark")
    if not (name and content and type and language and remark):
        raise HTTPException(status_code=400, detail="Missing parameter")
    app_temple_instance = AppTemplateService()
    result = app_temple_instance.add_controller_app_template(name, content, language, type, remark)
    return result


@app.put("/api/template", summary="Template Update Plan", tags=["sys-template"])
async def put_temple_update(request: Request, request_data: UpdateTemplateManager):
    data = request_data.dict()
    user_request_data = await request.json()
    name = data.get("name")
    content = data.get("content")
    type = data.get("t_type")
    language = data.get("language")
    remark = data.get("remark")
    ID = data.get("id")
    if not (ID and name and content and type and language and remark):
        raise HTTPException(status_code=400, detail="Missing parameter")
    app_temple_instance = AppTemplateService()
    result = app_temple_instance.update_controller_app_template(ID, name, content, language, type, remark, user_request_data)
    return result


@app.delete("/api/template", summary="Template Delete Plan", tags=["sys-template"])
async def delete_temple(request: Request, request_data: deleteTemplateManager):
    data = request_data.dict()
    user_request_data = await request.json()
    name = data.get("name")
    content = data.get("content")
    language = data.get("language")
    remark = data.get("remark")
    ID = data.get("id")
    if not (ID and name):
        raise HTTPException(status_code=400, detail="Missing parameter")
    app_temple_instance = AppTemplateService()
    result = app_temple_instance.delete_controller_app_template(ID, name, content, language, type, remark, user_request_data)
    return result

@app.get("/api/template/download/", summary="template download  Plan", tags=["sys-template"])
async def download_file(name: Optional[str], language: Optional[str]):
    if not (name and language):
        raise HTTPException(status_code=50000, detail="Missing parameter")
    temple_instance = TemplateService()
    result = temple_instance.download_file_controller_template(name, language)
    return result


@app.get("/api/app/template", summary="query app template", tags=["sys-app-template"])
def get_app_template_plan(page: int = Query(1, gt=0), page_size: int = Query(10, gt=0, le=1000)):
    return query_app_template(page, page_size)

@app.post("/api/app/template", summary="app模板模板", tags=["sys-app-template"])
async def save_app_template(request_data: AddAppTemplateManager):
    """
    1.检查是否有任何必需的参数缺失.
    2.初始化一个空列表以存储转换后的数据.
    3.遍历 test、pre 和 prod 字典
    4.创建一个新字典，包含 "env" 键和对应 item_data 的值

    :param request_data:
    :return:
    """
    if not all(request_data.dict().values()):
        raise HTTPException(status_code=400, detail="Missing parameter")
    transformed_data = []
    for env, item_data in [("test", request_data.test), ("pre", request_data.pre), ("prod", request_data.prod)]:
        new_data = {"env": env, **item_data.dict()}
        transformed_data.append(new_data)
    resultAppTemplateData = AppTemplateService.save_data_to_database(transformed_data)
    return resultAppTemplateData
    # #result = app_temple_instance.add_controller_app_template(name, content, language, type, remark)
    # return {"code": 20000,"data":"success"}


@app.put("/api/app/template", summary="App Template Update Plan", tags=["sys-app-template"])
async def put_temple_app_update(request: Request, request_data: UpdateAppTemplateManager):
    data = request_data.dict()
    user_request_data = await request.json()
    name = data.get("name")
    content = data.get("content")
    type = data.get("t_type")
    language = data.get("language")
    remark = data.get("remark")
    ID = data.get("id")
    if not (ID and name and content and type and language and remark):
        raise HTTPException(status_code=400, detail="Missing parameter")
    app_temple_instance = AppTemplateService()
    result = app_temple_instance.update_controller_app_template(ID, name, content, language, type, remark, user_request_data)
    return result


@app.delete("/api/app/template", summary="App Template Delete Plan", tags=["sys-app-template"])
async def delete_app_temple(request: Request, request_data: deleteAppTemplateManager):
    data = request_data.dict()
    user_request_data = await request.json()
    name = data.get("name")
    content = data.get("content")
    language = data.get("language")
    remark = data.get("remark")
    ID = data.get("id")
    if not (ID and name):
        raise HTTPException(status_code=400, detail="Missing parameter")
    app_temple_instance = AppTemplateService()
    result = app_temple_instance.delete_controller_app_template(ID, name, content, language, type, remark, user_request_data)
    return result

@app.get("/api/image", summary="images  query", tags=["sys-image"])
async def queryHarbor(project_name: Optional[str], app_name: Optional[str], repo_type: Optional[str] = None):
    if not (project_name and app_name):
        raise HTTPException(status_code=50000, detail="Missing parameter")
    result = await harbor_main_aio(project_name, app_name)
    return result


if __name__ == "__main__":
    logger = setup_logger()
    logger.info("fastapi logging start success")
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="debug")
