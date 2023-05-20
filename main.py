# https://github.com/kubernetes-client/python/tree/master/kubernetes/docs
# from logging

import datetime
import json
import os
import random
from typing import Optional, Dict, Any

# login token
import jwt
import uvicorn
from fastapi import APIRouter, Request
from fastapi import FastAPI, HTTPException
from fastapi import Query
from fastapi import WebSocket
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBearer
from passlib.hash import ldap_salted_sha1
from sqlalchemy.orm import sessionmaker
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse

# ops kube func method
from kube.kube_config import add_kube_config, get_kube_config_content, get_key_file_path, get_kube_config_dir_file, \
    delete_kubeconfig_file
from kube.kube_deployment import k8sDeploymentManager
from kube.kube_ingress import k8sIngressManager
from kube.kube_namespace import K8sNamespaceManager
# pod
from kube.kube_pod import PodManager
from kube.kube_service import K8sServiceManager
from kube.sys_temple import templeContent, public_download, get_file_extension
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
# 导入系统用户数据结构
from schemas.user import UserManager, updateUserManager, deleteUser
from sql_app.database import engine
# db ops kube service
from sql_app.kub_svc_db_play import insert_db_svc, delete_db_svc, query_kube_svc, query_kube_svc_by_name, \
    updata_kube_svc, \
    query_kube_svc_by_id, query_kube_all_svc_name, query_kube_all_svc_port
from sql_app.kube_cnfig_db_play import insert_kube_config, updata_kube_config, delete_kube_config, query_kube_config, \
    query_kube_db_env_cluster_all, query_kube_config_id, query_kube_db_env_all, query_kube_db_cluster_all, \
    query_kube_db_env_cluster_wrapper
from sql_app.kube_deploy_db_play import insert_kube_deployment, updata_kube_deployment, delete_kube_deployment, \
    query_kube_deployment, query_kube_deployment_by_name
# db ops kube ingress
from sql_app.kube_ingress_db_play import insert_db_ingress, updata_db_ingress, delete_db_ingress, query_kube_ingres, \
    query_kube_ingress_by_name, query_kube_ingress_by_id
# db ops kube namespace
from sql_app.kube_ns_db_play import insert_db_ns, query_ns, query_ns_any, query_kube_db_ns_all
from sql_app.login_users import insert_db_users, delete_db_users, query_users, query_users_name, updata_users
# db ops deploy and kube config
from sql_app.models import DeployK8sData
from sql_app.models import ServiceK8sData
from sql_app.ops_log_db_play import query_operate_ops_log, insert_ops_bot_log
from tools.config import setup_logging
from tools.harbor_tools_v2 import harbor_main_aio

# import user service
from service.sys_user import UserService

# import ws service
from service.sh_ws import websocket_handler, terminal_html

# import template service
from service.sys_template import TemplateService

security = HTTPBearer()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
app_name = "op-kube-manage-api"
app = FastAPI(
    title="op-kube-manage-api",
    description="kubernetes管理工具",
    version="0.0.1",
)
router = APIRouter()

origins = ["*"]
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


@app.get("/sys/ops/log/v1", summary="排查问题请求日志", tags=["sre_ops_list"])
def get_sys_ops_log(descname: Optional[str] = None, request: Optional[str] = None):
    return query_operate_ops_log(descname, request)


@app.get("/v1/kube/config/", summary="get KubeConfig k8s Plan", tags=["ConfigKubernetes"])
def get_kube_config(page: int = Query(1, gt=0), page_size: int = Query(10, gt=0, le=100), env: Optional[str] = None,
                    cluster_name: Optional[str] = None, server_address: Optional[str] = None,
                    client_key_path: Optional[str] = None):
    result_data = query_kube_config(page, page_size, env, cluster_name, server_address, client_key_path)
    return result_data


@app.get("/v1/kube/env/list/", summary="get KubeConfig k8s EnvList Plan", tags=["ConfigKubernetes"])
def get_kube_envList():
    result_data = query_kube_db_env_all()
    return result_data


@app.get("/v1/kube/cluster/List/", summary="get KubeConfig k8s EnvList Plan", tags=["ConfigKubernetes"])
def get_kube_clusterList():
    result_data = query_kube_db_cluster_all()
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
async def create_kube_config(request: Request, request_data: KubeConfig):
    from sql_app.models import KubeK8sConfig
    data = request_data.dict()
    if not all(data.get(field) for field in
               ['env', 'cluster_name', 'server_address', 'ca_data', 'client_crt_data', 'client_key_data']):
        return {'code': 20000, 'messages': "If the parameter is insufficient, check it", "data": "", "status": False}
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    result_app_name = session.query(KubeK8sConfig).filter_by(env=data.get("env"),
                                                             cluster_name=data.get('cluster_name')).first()
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
    user_request_data = await request.json()
    insert_ops_bot_log("Insert kube config", json.dumps(user_request_data), "post", json.dumps(insertInstance))
    return insertInstance


@app.put("/v1/kube/config/", summary="Put KubeConfig K8S Plan", tags=["ConfigKubernetes"])
async def update_kube_config(ReQuest: Request, request_data: updateKubeConfig):
    item_dict = request_data.dict()
    userRequestData = await ReQuest.json()
    db_kube_config = query_kube_config_id(item_dict.get('id'))
    if not (db_kube_config.get("data")):
        raise HTTPException(status_code=404, detail="KubeConfig not found")
    request_data = request_data.dict(exclude_unset=True)
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
        raise HTTPException(status_code=400, detail='update kube config failure')


@app.delete("/v1/kube/config/", summary="Delete KubeConfig K8S Plan", tags=["ConfigKubernetes"])
async def delete_kube_config_v1(ReQuest: Request, request_data: deleteKubeConfig):
    import asyncio
    item_dict = request_data.dict()
    userRequestData = await ReQuest.json()
    db_kube_config = query_kube_config_id(item_dict.get('id'))
    if not (db_kube_config.get("data")):
        raise HTTPException(status_code=404, detail="KubeConfig not found")
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


@app.get("/v1/sys/k8s/ns/plan/", summary="Get namespace App Plan", tags=["NamespaceKubernetes"])
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


@app.get("/v1/db/k8s/ns/plan/", summary="Get namespace App Plan", tags=["NamespaceKubernetes"])
def get_db_namespace_plan(page: int = Query(1, gt=0), page_size: int = Query(10, gt=0, le=100)):
    db_result = query_ns(page, page_size)
    return db_result


@app.get("/v1/db/k8s/ns/all/", summary="Get namespace App All Plan", tags=["NamespaceKubernetes"])
def get_db_namespace_plan():
    ns_all_db_result = query_kube_db_ns_all()
    return ns_all_db_result


@app.post("/v1/db/k8s/ns/plan/", summary="Add namespace App Plan", tags=["NamespaceKubernetes"])
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
    cluster_info = query_kube_db_env_cluster_all(env_name, cluster_name)
    if not (cluster_info.get("data")):
        raise HTTPException(status_code=400, detail=f"环境:{env_name}  集群:{cluster_name}  不存在请提前配置集群和环境")
    result_ns_name = query_ns_any(env_name, cluster_name, namespace_name)
    if result_ns_name.get("data"):
        msg = f" env {env_name} cluster_name {cluster_name} Namespace_info namespace: {namespace_name} existing 提示: 已经存在,不允许覆盖操作!"
        return {"code": 1, "data": msg, "message": "Namespace_info Record already exists", "status": True}
    else:
        for client_path in cluster_info.get("data"):
            if not (client_path.get("client_key_path")):
                raise HTTPException(status_code=400, detail="获取集群 client path  failure, 请检查问题")
            insert_ns_instance = K8sNamespaceManager(client_path.get("client_key_path"))
            insert_result_data = insert_ns_instance.create_kube_namespaces(namespace_name)
            print(insert_result_data)
            if insert_result_data.get("code") != 20000:
                raise HTTPException(status_code=400, detail=insert_result_data)
            result = insert_db_ns(env_name, cluster_name, data.get("ns_name"), data.get("used"))
            if result.get("code") != 20000:
                raise HTTPException(status_code=400, detail="create kube namespace  failure ")
            insert_ops_bot_log("Insert kube namespace ", json.dumps(user_request_data), "post", json.dumps(result))
            return result


@app.get("/v1/kube/pod/", summary="get Pod k8s Plan", tags=["PodKubernetes"])
def get_kube_pod(env: Optional[str], cluster: Optional[str], namespace: Optional[str]):
    if not (env and cluster and namespace):
        raise HTTPException(status_code=400, detail="The cluster or environment does not exist")
    cluster_info = query_kube_db_env_cluster_all(env, cluster)
    for client_path in cluster_info.get("data"):
        if not (client_path.get("client_key_path")):
            raise HTTPException(status_code=400, detail="获取集群 client path  failure, 请检查问题")
        pod_instance = PodManager(client_path.get("client_key_path"), namespace)
        return pod_instance.get_pods(env, cluster)


@app.post("/v1/kube/pod/restart", summary="POST Pod Restart k8s Plan", tags=["PodKubernetes"])
def get_kube_pod_restart(request: Request, request_data: postK8sRestartPodManager):
    data = request_data.dict()
    env = data.get("env")
    cluster = data.get("cluster")
    namespace = data.get("namespace")
    pod_name = data.get("pod_name")

    if not (env and cluster and namespace and pod_name):
        raise HTTPException(status_code=400, detail="The cluster or environment does not exist")
    cluster_info = query_kube_db_env_cluster_all(env, cluster)
    for client_path in cluster_info.get("data"):
        if not (client_path.get("client_key_path")):
            raise HTTPException(status_code=400, detail="获取集群 client path  failure, 请检查问题")
        pod_instance = PodManager(client_path.get("client_key_path"), namespace)
        return pod_instance.restart_pod(pod_name)


@app.get("/v1/kube/pod/mock", summary="get Pod Mock k8s Plan", tags=["PodKubernetes"])
def get_kube_mock_pod():
    from tools.config import k8sPodHeader
    return {"code": 20000, "total": 0, "data": [], "messages": "query data success", "status": True, "columns": k8sPodHeader}


@app.post("/v1/kube/pod/", summary="Add POD K8S Plan", tags=["PodKubernetes"])
async def create_kube_pod(request: Request, request_data: postK8sPodManager):
    data = request_data.dict()
    if not all(data.get(field) for field in
               ['env', 'cluster', 'namespace', 'pod_name', 'image', 'ports']):
        return {'code': 20000, 'messages': "If the parameter is insufficient, check it", "data": "", "status": False}
    env = data.get("env")
    cluster = data.get("cluster")
    container_port = data.get("ports")
    container_image = data.get("image")
    pod_name = data.get("pod_name")
    namespace_name = data.get("namespace")
    cluster_info = query_kube_db_env_cluster_all(env, cluster)
    for client_path in cluster_info.get("data"):
        if not (client_path.get("client_key_path")):
            raise HTTPException(status_code=400, detail="获取集群 client path  failure, 请检查问题")
        pod_instance = PodManager(client_path.get("client_key_path"), namespace_name)
        return pod_instance.create_pod(pod_name, container_image, container_port)


@app.put("/v1/kube/pod/", summary="Put POD K8S Plan", tags=["PodKubernetes"])
def update_kube_Pod(ReQuest: Request, request_data: putK8sPodManager):
    data = request_data.dict()
    if not all(data.get(field) for field in
               ['env', 'cluster', 'namespace', 'pod_name', 'image', 'ports']):
        return {'code': 20000, 'messages': "If the parameter is insufficient, check it", "data": "", "status": False}
    env = data.get("env")
    cluster = data.get("cluster")
    container_port = data.get("ports")
    container_image = data.get("image")
    pod_name = data.get("pod_name")
    namespace_name = data.get("namespace")
    cluster_info = query_kube_db_env_cluster_all(env, cluster)
    for client_path in cluster_info.get("data"):
        if not (client_path.get("client_key_path")):
            raise HTTPException(status_code=400, detail="获取集群 client path  failure, 请检查问题")
        pod_instance = PodManager(client_path.get("client_key_path"), namespace_name)
        return pod_instance.update_pod(pod_name, container_image)


def generate_deployment_id():
    current_date = datetime.datetime.now().strftime("%Y%m%d")
    random_string = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=4))
    deployment_id = f"{current_date}-{random_string}"
    return deployment_id


@app.post("/v1/k8s/deployment/plan/", summary="Add deployment App Plan", tags=["DeployKubernetes"])
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

    result_deploy_name = query_kube_deployment_by_name(env_name, cluster_name, data.get("app_name"),
                                                       data.get("namespace"))
    if result_deploy_name.get("data"):
        msg = f'''App_info 环境:{env_name} 集群:{cluster_name} APP应用: {data.get("app_name")} existing 提示: 已经存在,不允许覆盖操作!'''
        raise HTTPException(status_code=400, detail=msg)
    result_cluster_info = query_kube_db_env_cluster_all(env_name, cluster_name)
    if not (result_cluster_info.get("data")):
        raise HTTPException(status_code=400, detail=f"环境:{env_name}  集群:{cluster_name}  不存在请提前配置集群和环境")
    for client_path in result_cluster_info.get("data"):
        if not (client_path.get("client_key_path")):
            raise HTTPException(status_code=400, detail="获取集群 client path  failure, 请检查问题")
        deploy_env = data.get("deploy_env")
        if isinstance(deploy_env, str):
            try:
                deploy_env_dict = dict(kv.split('=') for kv in deploy_env.split(','))
            except ValueError:
                deploy_env_dict = {deploy_env.split('=')[0]: deploy_env.split('=')[1]}
                print("one", deploy_env_dict)
        elif isinstance(deploy_env, dict):
            deploy_env_dict = deploy_env
            print("sss", deploy_env_dict)
        else:
            raise HTTPException(status_code=400, detail="deploy_env must be a string or dictionary")

        insert_deploy_instance = k8sDeploymentManager(client_path.get("client_key_path"), data.get('namespace'))
        insert_result_data = insert_deploy_instance.create_kube_deployment(
            data.get('namespace'), data.get("app_name"), data.get("resources"), data.get("replicas"),
            data.get("image"), deploy_env_dict, data.get("ports"), health_liven_ess_path, health_readiness_path)

        if insert_result_data.get("code") != 20000:
            raise HTTPException(status_code=400, detail=insert_result_data.get("message"))
        deploy_id = generate_deployment_id()
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
        user_request_data = await request.json()
        insert_ops_bot_log("Insert kube deploy app ", json.dumps(user_request_data), "post", json.dumps(result))
        return result


@app.put("/v1/k8s/deployment/plan/", summary="Change deployment App Plan", tags=["DeployKubernetes"])
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
    session = SessionLocal()
    deployment = session.query(DeployK8sData).filter(DeployK8sData.id == data.get('id')).first()
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    deploy_env = data.get("deploy_env")
    if isinstance(deploy_env, str):
        try:
            deploy_env_dict = dict(kv.split('=') for kv in deploy_env.split(','))
            print("==", deploy_env_dict)
        except ValueError:
            deploy_env_dict = {deploy_env.split('=')[0]: deploy_env.split('=')[1]}
            print("one", deploy_env_dict)
    elif isinstance(deploy_env, dict):
        deploy_env_dict = deploy_env
    else:
        raise HTTPException(status_code=400, detail="deploy_env must be a string or dictionary")
    result_cluster_info = query_kube_db_env_cluster_all(env_name, cluster_name)
    for client_path in result_cluster_info.get("data"):
        if not (client_path.get("client_key_path")):
            raise HTTPException(status_code=400, detail="获取集群 client path  failure, 请检查问题")
        update_deploy_instance = k8sDeploymentManager(client_path.get("client_key_path"), data.get('namespace'))
        data_result = update_deploy_instance.replace_kube_deployment(data.get('deployment_name'),
                                                                     item_dict.get("replicas"), data.get("image"),
                                                                     data.get('namespace'), resources_name,
                                                                     deploy_env_dict,
                                                                     container_port_name, health_liven_ess_path,
                                                                     health_readiness_path)
        if data_result.get("code") != 0:
            raise HTTPException(status_code=500, detail="Failed to update kubernetes deployment")
        update_id = generate_deployment_id()
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


@app.get("/v1/k8s/deployment/plan/", summary="Get deployment App Plan", tags=["DeployKubernetes"])
def get_deploy_plan(page: int = Query(1, gt=0), page_size: int = Query(10, gt=0, le=1000), env: Optional[str] = None,
                    cluster: Optional[str] = None, app_name: Optional[str] = None,
                    image: Optional[str] = None, ports: Optional[str] = None,
                    image_pull_secrets: Optional[str] = None, deploy_id: Optional[int] = None):
    result_data = query_kube_deployment(page, page_size, env, cluster, app_name, image, ports, image_pull_secrets, deploy_id)
    return result_data


@app.delete("/v1/k8s/deployment/plan/", summary="Delete deployment App Plan", tags=["DeployKubernetes"])
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

    result_cluster_info = query_kube_db_env_cluster_all(env_name, cluster_name)
    if not (result_cluster_info.get("data")):
        raise HTTPException(status_code=400, detail=f"环境:{env_name}  集群:{cluster_name}  不存在请提前配置集群和环境")
    for client_path in result_cluster_info.get("data"):
        if not (client_path.get("client_key_path")):
            raise HTTPException(status_code=400, detail="获取集群 client path  failure, 请检查问题")
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


@app.post("/v1/k8s/service/plan/", summary="Add Service App Plan", tags=["ServiceKubernetes"])
async def post_service_plan(request: Request, request_data: CreateSvcK8S):
    item_dict = request_data.dict()
    user_request_data = await request.json()
    data = request_data.dict()
    env_name = data.get("env")
    cluster_name = data.get("cluster_name")
    if not (data.get("namespace") and data.get('svc_name') and data.get("selector_labels") and
            data.get('svc_port') and data.get('target_port')):
        return {'code': 1, 'messages': "If the parameter is insufficient, check it", "data": "", "status": False}
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    with SessionLocal() as session:
        result_svc_name = session.query(ServiceK8sData).filter_by(svc_name=data.get("svc_name")).all()
        if result_svc_name:
            msg = f"Service_info  Service: {data.get('svc_name')} existing 提示: 已经存在,不允许覆盖操作!"
            return {"code": 1, "data": msg, "message": "Service_info Record already exists", "status": True}
        else:
            result_cluster_info = query_kube_db_env_cluster_all(env_name, cluster_name)
            if not (result_cluster_info.get("data")):
                raise HTTPException(status_code=400,
                                    detail=f"环境:{env_name}  集群:{cluster_name}  不存在请提前配置集群和环境")
            for client_path in result_cluster_info.get("data"):
                if not (client_path.get("client_key_path")):
                    raise HTTPException(status_code=400, detail="获取集群 client path  failure, 请检查问题")
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


@app.put("/v1/k8s/service/plan/", summary="Change Service App Plan", tags=["ServiceKubernetes"])
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
    svc_by_id = query_kube_svc_by_id(ID)
    if not (svc_by_id.get("data")):
        raise HTTPException(status_code=404, detail="db is service  id not found")
    service = query_kube_svc_by_name(env_name, cluster_name, svc_name, namespace_name)
    if not (service.get("data")):
        raise HTTPException(status_code=404, detail="service cluster {cl} info not found".format(cl=cluster_name))
    result_cluster_info = query_kube_db_env_cluster_all(env_name, cluster_name)
    if not (result_cluster_info.get("data")):
        raise HTTPException(status_code=400, detail=f"环境:{env_name}  集群:{cluster_name}  不存在请提前配置集群和环境")
    labels = {}
    try:
        for sl in selector_labels.split(","):
            k, v = sl.split("=")
            labels[k] = v
    except Exception as e:
        return "Failed to create SVC because the label format is incorrect"
    for client_path in result_cluster_info.get("data"):
        if not (client_path.get("client_key_path")):
            raise HTTPException(status_code=400, detail="获取集群 client path  failure, 请检查问题")
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
        raise HTTPException(status_code=400, detail="Failed to update kube service app")


@app.get("/v1/k8s/service/plan/", summary="Get Service App Plan", tags=["ServiceKubernetes"])
def get_service_plan(page: int = Query(1, gt=0), page_size: int = Query(10, gt=0, le=1000), env: Optional[str] = None,
                     cluster_name: Optional[str] = None, namespace: Optional[str] = None,
                     svc_name: Optional[str] = None, selector_labels: Optional[str] = None,
                     svc_port: Optional[str] = None,
                     svc_type: Optional[str] = None, target_port: Optional[str] = None):
    result_data = query_kube_svc(page, page_size, env, cluster_name, namespace, svc_name, selector_labels, svc_port, svc_type,
                                 target_port)
    return result_data


@app.get("/v1/k8s/service/all/plan/", summary="Get ALL Service App Plan", tags=["ServiceKubernetes"])
def get_all_service_plan(env: Optional[str], cluster_name: Optional[str], namespace: Optional[str]):
    if not (env and cluster_name and namespace):
        raise HTTPException(status_code=400, detail="Incorrect parameters")
    result_data = query_kube_all_svc_name(env, cluster_name, namespace)
    return result_data


@app.get("/v1/k8s/service/svc-port/plan/", summary="Get ALL Service Port App Plan", tags=["ServiceKubernetes"])
def get_all_service_port_plan(env: Optional[str], cluster_name: Optional[str], namespace: Optional[str], svc_name: Optional[str]):
    if not (env and cluster_name and namespace and svc_name):
        raise HTTPException(status_code=400, detail="Incorrect parameters")
    result_data = query_kube_all_svc_port(env, cluster_name, namespace, svc_name)
    return result_data


@app.delete("/v1/k8s/service/plan/", summary="Delete Service App Plan", tags=["ServiceKubernetes"])
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
    result_cluster_info = query_kube_db_env_cluster_all(env_name, cluster_name)
    for client_path in result_cluster_info.get("data"):
        if not (client_path.get("client_key_path")):
            raise HTTPException(status_code=400, detail="获取集群 client path  failure, 请检查问题")
        delete_svc_instance = K8sServiceManager(client_path.get("client_key_path"))
        result_data = delete_svc_instance.delete_kube_svc(namespace_name, svc_name)
        if result_data.get("code") == 0:
            delete_instance = delete_db_svc(app_id)
            insert_ops_bot_log("Delete kube Deploy App", json.dumps(userRequestData), "delete",
                               json.dumps(delete_instance))
            return delete_instance
        else:
            raise HTTPException(status_code=400, detail="Delete deploy App failure")


@app.post("/v1/k8s/ingress/plan/", summary="Add Ingress App Plan", tags=["IngressKubernetes"])
async def post_ingress_plan(ReQuest: Request, request_data: CreateIngressK8S):
    from kube.kube_ingress import k8sIngressManager
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
    result_cluster_info = query_kube_db_env_cluster_all(env_name, cluster_name)
    for client_path in result_cluster_info.get("data"):
        if not (client_path.get("client_key_path")):
            raise HTTPException(status_code=400, detail="获取集群 client path  failure, 请检查问题")
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
            raise HTTPException(status_code=400, detail="Create ingress App failure")


@app.put("/v1/k8s/ingress/plan/", summary="Change Ingress App Plan", tags=["IngressKubernetes"])
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
    query_ingres_id = query_kube_ingress_by_id(ID)
    if not query_ingres_id.get("data"):
        return {'code': 1, 'messages': "ingress Id not exist , check it", "data": "", "status": False}
    result_cluster_info = query_kube_db_env_cluster_all(env_name, cluster_name)
    for client_path in result_cluster_info.get("data"):
        if not (client_path.get("client_key_path")):
            raise HTTPException(status_code=400, detail="获取集群 client path  failure, 请检查问题")
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
        return {"code": 1, "messages": "update kube deploy app failure", "status": True, "data": "failure"}


@app.get("/v1/k8s/ingress/plan/", summary="Get Ingress App Plan", tags=["IngressKubernetes"])
def get_ingress_plan(page: int = Query(1, gt=0), page_size: int = Query(10, gt=0, le=1000), env: Optional[str] = None,
                     cluster_name: Optional[str] = None, namespace: Optional[str] = None,
                     ingress_name: Optional[str] = None, host: Optional[str] = None,
                     svc_name: Optional[str] = None, svc_port: Optional[str] = None, tls: Optional[str] = None,
                     tls_secret: Optional[str] = None):
    result_data = query_kube_ingres(page, page_size, env, cluster_name, namespace, ingress_name, host, svc_name, svc_port, tls,
                                    tls_secret)
    return result_data


@app.get("/v1/k8s/sys/ns-by-ingress/", summary="Get sys Ingress App Plan", tags=["IngressKubernetesSys"])
def get_ns_by_ingress_plan(env: Optional[str] = None, cluster_name: Optional[str] = None,
                           namespace: Optional[str] = None):
    k8s_instance = k8sIngressManager(k8s_instance, namespace)
    ns_result = k8s_instance.get_kube_ingress_by_name()
    return ns_result


@app.get("/v1/k8s/sys/ns-all-ingress/", summary="Get sys Ingress App Plan", tags=["IngressKubernetesSys"])
@query_kube_db_env_cluster_wrapper()
def get_ns_all_ingress_plan(k8s_instance: k8sIngressManager, env: Optional[str] = None,
                            cluster_name: Optional[str] = None):
    ns_k8s_instance = k8sIngressManager(k8s_instance, "dev")
    ns_result = ns_k8s_instance.get_kube_ingress_all()
    return ns_result


@app.delete("/v1/k8s/ingress/plan/", summary="Delete Ingress App Plan", tags=["IngressKubernetes"])
async def delete_ingress_plan(request: Request, request_data: deleteIngressK8S):
    from kube.kube_ingress import k8sIngressManager
    data = request_data.dict()
    user_request_data = await request.json()
    env_name = request_data.env
    cluster_name = request_data.cluster_name
    if not all(data.values()):
        return {"code": 1, "messages": "Delete Ingress App failure, Incorrect parameters", "status": True,
                "data": "failure"}
    result_cluster_info = query_kube_db_env_cluster_all(env_name, cluster_name)
    for client_path in result_cluster_info.get("data"):
        if not (client_path.get("client_key_path")):
            raise HTTPException(status_code=400, detail="获取集群 client path  failure, 请检查问题")
        ingress_manager = k8sIngressManager(client_path.get("client_key_path"), data["namespace"])
        result_data = ingress_manager.delete_kube_ingress(data["namespace"], data["ingress_name"])
        if result_data["code"] == 0:
            delete_instance = delete_db_ingress(data["id"])
            insert_ops_bot_log("Delete kube Ingress App", json.dumps(user_request_data), "delete",
                               json.dumps(delete_instance))
            return delete_instance
        else:
            return {"code": 1, "messages": "delete Ingress App failure", "status": True, "data": "failure"}

@app.post("/user/login/", summary="用户登录验证，如果成功返回用户 token，否则返回 HTTP 401 错误", tags=["sys-login-user"])
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

@app.get("/user/info", summary="验证 JWT token，如果验证成功，返回用户名", tags=["sys-login-user"])
def protected(token):
    if not (token):
        raise HTTPException(status_code=400, detail="Missing parameter")
        return {"code": 50000, "message": "Missing parameter", "statue": True}
    return UserService.protected_token(token)

@app.post("/user/logout", summary="get logout user to  jwt token ", tags=["sys-login-user"])
def logout():
    return UserService.logout_msg()


@app.post("/user/add", summary="add user  ", tags=["sys-users"])
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

@app.get("/user/query", summary="query user", tags=["sys-users"])
def get_deploy_plan(page: int = Query(1, gt=0), page_size: int = Query(10, gt=0, le=1000)):
    result_data = query_users(page, page_size)
    return result_data


@app.delete("/user/delete", summary="Delete users Plan", tags=["sys-users"])
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


@app.put("/user/update", summary="User Update Plan", tags=["sys-users"])
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
def get_template_plan(page: int = Query(1, gt=0), page_size: int = Query(10, gt=0, le=1000)):
    result_data = query_template(page, page_size)
    return result_data

@app.post("/api/template", summary="模板自定义模板", tags=["sys-template"])
def save_template(request: Request, request_data: templateManager):
    data = request_data.dict()
    name = data.get("name")
    content = data.get("content")
    type = data.get("t_type")
    language = data.get("language")
    remark = data.get("remark")
    if not (name and content and type and language and remark):
        raise HTTPException(status_code=400, detail="Missing parameter")
    temple_instance = TemplateService()
    result = temple_instance.add_controller_template(name, content, language, type, remark)
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
    temple_instance = TemplateService()
    result = temple_instance.update_controller_template(ID, name, content, language, type, remark, user_request_data)
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
    temple_instance = TemplateService()
    result = temple_instance.delete_controller_template(ID, name, content, language, type, remark, user_request_data)
    return result

@app.get("/api/template/download/", summary="template download  Plan", tags=["sys-template"])
async def download_file(name: Optional[str], language: Optional[str]):
    if not (name and language):
        raise HTTPException(status_code=50000, detail="Missing parameter")
    temple_instance = TemplateService()
    result = temple_instance.download_file_controller_template(name,language)
    return result

@app.get("/api/image", summary="images  query", tags=["sys-image"])
async def queryHarbor(project_name: Optional[str], app_name: Optional[str], repo_type: Optional[str] = None):
    if not (project_name and app_name):
        raise HTTPException(status_code=50000, detail="Missing parameter")
    result = await harbor_main_aio(project_name, app_name)
    return result


if __name__ == "__main__":
    setup_logging(log_file_path="fastapi.log", project_root="./logs", message="startup fastapi")
    uvicorn.run(app, host="0.0.0.0", port=8888, log_level="debug")
