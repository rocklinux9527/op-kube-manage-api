# https://github.com/kubernetes-client/python/tree/master/kubernetes/docs

from fastapi import FastAPI, APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional, Set, Dict, Any
from starlette.middleware.cors import CORSMiddleware
import uvicorn
import json

from fastapi import APIRouter, Depends, HTTPException, Request

# ops kube func method
from kube.kube_config import add_kube_config, get_kube_config_content, get_key_file_path, get_kube_config_dir_file, \
    delete_kubeconfig_file
from kube.kube_deployment import k8sDeploymentManager
from kube.kube_namespace import k8sNameSpaceManager
from kube.kube_service import k8sServiceManger

# db ops deploy and kube config
from sql_app.models import DeployK8sData
from sqlalchemy.orm import sessionmaker, query, Session
from sql_app.database import engine
from sql_app.ops_log_db_play import query_operate_ops_log, insert_ops_bot_log
from sql_app.kube_cnfig_db_play import insert_kube_config, updata_kube_config, delete_kube_config, query_kube_config, \
    query_kube_env_cluster_all, query_kube_db_env_cluster_all
from sql_app.kube_deploy_db_play import insert_kube_deployment, updata_kube_deployment, delete_kube_deployment, \
    query_kube_deployment

# db ops kube namespace
from sql_app.kube_ns_db_play import insert_db_ns, delete_db_ns, query_ns

# db ops kube service
from sql_app.kub_svc_db_play import insert_db_svc, delete_db_svc, query_kube_svc

from kube.kube_ingress import k8sIngressManager
# db ops kube ingress
from sql_app.kube_ingress_db_play import insert_db_ingress, updata_db_ingress, delete_db_ingress, query_kube_ingres

#  k8s install deploy

from kube.kube_deployment import k8sDeploymentManager

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app_name = "op-kube-manage-api"
app = FastAPI(
    title="op-kube-manage-api",
    description="kubernetes管理工具",
    version="0.0.1",
)
router = APIRouter()

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


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


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
def get_kube_config(env: Optional[str] = None, cluster_name: Optional[str] = None, server_address: Optional[str] = None,
                    client_key_path: Optional[str] = None):
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
    from sqlalchemy.orm import sessionmaker, query
    from sql_app.database import engine
    from sql_app.models import KubeK8sConfig
    item_dict = request_data.dict()
    userRequestData = await ReQuest.json()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    data = request_data.dict()
    result_app_name = session.query(KubeK8sConfig).filter_by(env=data.get("env"),
                                                             cluster_name=data.get('cluster_name')).first()
    if data.get("env") and data.get('cluster_name') and data.get('server_address') and data.get("ca_data") and data.get(
            'client_crt_data') and data.get("client_key_data"):
        if result_app_name:
            msg = '''cluster_info 环境:{env} 集群名称:{cluster} existing 提示: 已经存在,不允许覆盖操作!'''.format(
                env=data.get("env"),
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
                    insert_ops_bot_log("Insert kube config", json.dumps(userRequestData), "post",
                                       json.dumps(insertInstance))
                    return insertInstance
                else:
                    return {"code": 1, "messages": "create kube config file path failure ", "status": True,
                            "data": "failure"}
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
        return {"code": 1, "messages": "Delete kube config failure, Incorrect parameters", "status": True,
                "data": "failure"}


class createNameSpace(BaseModel):
    env: str
    cluster_name: str
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
async def post_namespace_plan(request: Request, request_data: createNameSpace):
    from sqlalchemy.orm import sessionmaker, query
    from sql_app.database import engine
    from sql_app.models import DeployNsData
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
    result_ns_name = session.query(DeployNsData).filter_by(ns_name=data.get("ns_name")).all()
    if result_ns_name:
        msg = f"Namespace_info namespace: {namespace_name} existing 提示: 已经存在,不允许覆盖操作!"
        return {"code": 1, "data": msg, "message": "Namespace_info Record already exists", "status": True}
    else:
        for client_path in cluster_info.get("data"):
            if not (client_path.get("client_key_path")):
                raise HTTPException(status_code=400, detail="获取集群 client path  failure, 请检查问题")
            insert_ns_instance = k8sNameSpaceManager(client_path.get("client_key_path"))
            insert_result_data = await insert_ns_instance.create_kube_namespaces(data.get("ns_name"))
            if insert_result_data.get("code") != 0:
                raise HTTPException(status_code=400, detail=insert_result_data)
            result = insert_db_ns(env_name, cluster_name, data.get("ns_name"), data.get("used"))
            if result.get("code") != 0:
                raise HTTPException(status_code=400, detail="create kube namespace  failure ")
            insert_ops_bot_log("Insert kube namespace ", json.dumps(user_request_data), "post", json.dumps(result))
            return result


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
    env: str
    cluster: str
    app_name: str
    namespace: str
    client_config_path: str


@app.post("/v1/k8s/deployment/plan/", summary="Add deployment App Plan", tags=["DeployKubernetes"])
def post_deploy_plan(request: Request, request_data: CreateDeployK8S) -> Dict[str, Any]:
    item_dict = request_data.dict()
    user_request_data = request.json()
    data = request_data.dict()
    cluster_name = data.get("cluster")
    env_name = data.get("env")
    if not (cluster_name and env_name):
        raise HTTPException(status_code=400, detail="The cluster or environment does not exist")
    result_deploy_name = session.query(DeployK8sData).filter_by(app_name=data.get("app_name")).all()
    if result_deploy_name:
        msg = f'''App_info 环境:{env_name} 集群:{cluster_name} APP应用: {data.get("app_name")} existing 提示: 已经存在,不允许覆盖操作!'''
        raise HTTPException(status_code=400, detail=msg)
    result_cluster_info = query_kube_db_env_cluster_all(env_name, cluster_name)
    if not (result_cluster_info.get("data")):
        raise HTTPException(status_code=400, detail=f"环境:{env_name}  集群:{cluster_name}  不存在请提前配置集群和环境")
    for client_path in result_cluster_info.get("data"):
        if not (client_path.get("client_key_path")):
            raise HTTPException(status_code=400, detail="获取集群 client path  failure, 请检查问题")
        deploy_env = data.get("deploy_env")
        deploy_env_dict = {}
        try:
            for env in deploy_env.split(","):
                k, v = env.split("=")
                deploy_env_dict[k] = v
        except Exception as e:
            raise HTTPException(status_code=400,
                                detail="Failed to create Deployment  because the deploy env format is incorrect")
        insert_deploy_instance = k8sDeploymentManager(client_path.get("client_key_path"), data.get('namespace'))
        insert_result_data = insert_deploy_instance.create_kube_deployment(
            data.get('namespace'), data.get("app_name"), data.get("resources"), data.get("replicas"),
            data.get("image"), deploy_env_dict, data.get("ports"))
        if insert_result_data.get("code") != 0:
            raise HTTPException(status_code=400, detail=insert_result_data.get("message"))
        result = insert_kube_deployment(item_dict.get("app_name"), item_dict.get("env"),
                                        item_dict.get("cluster"),
                                        item_dict.get("namespace"), item_dict.get("resources"),
                                        item_dict.get("replicas"), item_dict.get("image"),
                                        item_dict.get("affinity"),
                                        item_dict.get("ant_affinity"), item_dict.get("deploy_env"),
                                        item_dict.get("ports"), item_dict.get("volumeMounts"),
                                        item_dict.get("volume"),
                                        item_dict.get("image_pull_secrets"), item_dict.get("health_liven_ess"),
                                        item_dict.get("health_readiness"), "")
        insert_ops_bot_log("Insert kube deploy app ", json.dumps(user_request_data), "post", json.dumps(result))
        return result


@app.put("/v1/k8s/deployment/plan/", summary="Change deployment App Plan", tags=["DeployKubernetes"])
async def put_deploy_plan(id: int, request_data: UpdateDeployK8S, request: Request):
    item_dict = request_data.dict()
    user_request_data = await request.json()
    data = request_data.dict()
    if not all(data.values()):
        raise HTTPException(status_code=400, detail="Invalid input parameters")
    session = SessionLocal()
    try:
        deployment = session.query(DeployK8S).filter(DeployK8S.id == id).first()
        if not deployment:
            raise HTTPException(status_code=404, detail="Deployment not found")
        for client_path in result_cluster_info.get("data"):
            if not (client_path.get("client_key_path")):
                raise HTTPException(status_code=400, detail="获取集群 client path  failure, 请检查问题")
            update_deploy_instance = k8sDeploymentManager(client_path.get("client_key_path"), data.get('namespace'))
            data_result = update_deploy_instance.replace_kube_deployment(data.get('deployment_name'),
                                                                         data.get('replicas'), data.get("image"),
                                                                         data.get('namespace'))
            if data_result.get("code") != 0:
                raise HTTPException(status_code=500, detail="Failed to update kubernetes deployment")
            deployment.app_name = item_dict.get("app_name")
            deployment.env = item_dict.get("env")
            deployment.cluster = item_dict.get("cluster")
            deployment.namespace = item_dict.get("namespace")
            deployment.resources = item_dict.get("resources")
            deployment.replicas = item_dict.get("replicas")
            deployment.image = item_dict.get("image")
            deployment.affinity = item_dict.get("affinity")
            deployment.ant_affinity = item_dict.get("ant_affinity")
            deployment.deploy_env = item_dict.get("deploy_env")
            deployment.ports = item_dict.get("ports")
            deployment.volumeMounts = item_dict.get("volumeMounts")
            deployment.volume = item_dict.get("volume")
            deployment.image_pull_secrets = item_dict.get("image_pull_secrets")
            deployment.health_liven_ess = item_dict.get("health_liven_ess")
            deployment.health_readiness = item_dict.get("health_readiness")
            session.commit()
            insert_ops_bot_log("Update kube deploy app", json.dumps(user_request_data), "post", json.dumps(deployment))
            return deployment
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@app.get("/v1/k8s/deployment/plan/", summary="Get deployment App Plan", tags=["DeployKubernetes"])
def get_deploy_plan(env: Optional[str] = None, cluster: Optional[str] = None, app_name: Optional[str] = None,
                    image: Optional[str] = None, ports: Optional[str] = None,
                    image_pull_secrets: Optional[str] = None, deploy_id: Optional[int] = None):
    result_data = query_kube_deployment(env, cluster, app_name, image, ports, image_pull_secrets, deploy_id)
    return result_data


@app.delete("/v1/k8s/deployment/plan/", summary="Delete deployment App Plan", tags=["DeployKubernetes"])
async def del_deploy_plan(request: Request, request_data: deleteDeployK8S):
    data = request_data.dict()
    app_name = data.get("app_name")
    namespace_name = data.get('namespace')
    if not (app_name and namespace_name):
        return {
            "code": 1,
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
            delete_instance = deleteDeployK8S(data.get("id"))
            insert_ops_bot_log(
                "Delete kube Deploy App",
                await request.json(),
                "delete",
                delete_instance,
            )
            return delete_instance
        else:
            return {
                "code": 1,
                "messages": "delete deploy App  failure ",
                "status": True,
                "data": "failure",
            }


class CreateSvcK8S(BaseModel):
    env: str
    cluster_name: str
    client_config_path: str
    namespace: str
    svc_name: str
    selector_labels: str = "app=web,name=test_svc"
    svc_port: int
    svc_type: str = "ClusterIP"
    target_port: int


class UpdateSvcK8S(BaseModel):
    id: int
    env: str
    cluster_name: str
    client_config_path: str
    namespace: str
    svc_name: str
    selector_labels: str
    svc_port: int
    svc_type: str = "ClusterIP"
    target_port: int


class deleteSvcK8S(BaseModel):
    id: int
    env: str
    cluster_name: str
    namespace: str
    svc_name: str
    client_config_path: str


@app.post("/v1/k8s/service/plan/", summary="Add Service App Plan", tags=["ServiceKubernetes"])
async def post_service_plan(request: Request, request_data: CreateSvcK8S):
    item_dict = request_data.dict()
    user_request_data = await request.json()
    data = request_data.dict()
    client_config_path = data.get('client_config_path')
    if not (data.get("namespace") and data.get('svc_name') and data.get("selector_labels") and
            data.get('svc_port') and data.get('target_port') and client_config_path):
        return {'code': 1, 'messages': "If the parameter is insufficient, check it", "data": "", "status": False}
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    with SessionLocal() as session:
        result_svc_name = session.query(ServiceK8sData).filter_by(svc_name=data.get("svc_name")).all()
        if result_svc_name:
            msg = f"Service_info  Service: {data.get('svc_name')} existing 提示: 已经存在,不允许覆盖操作!"
            return {"code": 1, "data": msg, "message": "Service_info Record already exists", "status": True}
        else:
            insert_svc_instance = k8sServiceManger(client_config_path)
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
            svc_type = SVC_TYPE_NODE_PORT if data.get("svc_type") == "NodePort" else SVC_TYPE_CLUSTER_IP
            insert_result_data = insert_svc_instance.create_kube_svc(namespace_name, svc_name, labels,
                                                                     svc_port, target_port, svc_type)
            if insert_result_data.get("code") == 0:
                with session.begin():
                    session.add(ServiceK8sData(**item_dict))
                insert_ops_bot_log("Insert kube service app ", json.dumps(user_request_data), "post",
                                   json.dumps(insert_result_data))
            return insert_result_data


@app.put("/v1/k8s/service/plan/", summary="Change Service App Plan", tags=["ServiceKubernetes"])
async def put_service_plan(
        request: Request,
        request_data: UpdateSvcK8S,
        db: Session = Depends(get_db)
):
    data = request_data.dict()
    env_name = data.get("env")
    cluster_name = data.get('cluster')
    namespace_name = data.get("namespace")
    app_name = data.get("app_name")
    replicas = data.get('replicas')
    image_name = data.get('image')
    client_config_path = data.get('client_config_path')
    if not (
            env_name and cluster_name and namespace_name and app_name and replicas and image_name and client_config_path):
        raise HTTPException(status_code=400, detail="Missing parameter")

    deployment = crud.get_deployment_by_name_and_namespace(db, data.get('deployment_name'), data.get('namespace'))
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")

    update_deploy_instance = k8sDeploymentManager(data.get('client_config_path'), data.get('namespace'))
    data_result = update_deploy_instance.replace_kube_deployment(data.get('deployment_name'),
                                                                 data.get('replicas'),
                                                                 data.get("image"),
                                                                 data.get('namespace'))

    if data_result.get("code") == 0:
        updated_deployment = crud.update_deployment(
            db=db,
            deployment=deployment,
            app_name=data.get("app_name"),
            env=data.get("env"),
            cluster=data.get("cluster"),
            namespace=data.get("namespace"),
            resources=data.get("resources"),
            replicas=data.get("replicas"),
            image=data.get("image"),
            affinity=data.get("affinity"),
            ant_affinity=data.get("ant_affinity"),
            deploy_env=data.get("deploy_env"),
            ports=data.get("ports"),
            volumeMounts=data.get("volumeMounts"),
            volume=data.get("volume"),
            image_pull_secrets=data.get("image_pull_secrets"),
            health_liven_ess=data.get("health_liven_ess"),
            health_readiness=data.get("health_readiness")
        )

        if updated_deployment:
            insert_ops_bot_log("Update kube deploy app ", json.dumps(await request.json()), "post",
                               json.dumps(updated_deployment))
            return updated_deployment
    raise HTTPException(status_code=400, detail="Failed to update kube deploy app")


@app.get("/v1/k8s/service/plan/", summary="Get Service App Plan", tags=["ServiceKubernetes"])
def get_service_plan(namespace: Optional[str] = None, svc_name: Optional[str] = None, svc_port: Optional[str] = None,
                     svc_type: Optional[str] = None, target_port: Optional[str] = None):
    result_data = query_kube_svc(namespace, svc_name, svc_port, svc_type, target_port)
    return result_data


@app.delete("/v1/k8s/service/plan/", summary="Delete Service App Plan", tags=["ServiceKubernetes"])
async def delete_service_plan(ReQuest: Request, request_data: deleteSvcK8S):
    app_name = request_data.app_name
    namespace_name = request_data.namespace
    userRequestData = await ReQuest.json()
    client_config_path = request_data.client_config_path
    if not (app_name and namespace_name and client_config_path):
        raise HTTPException(status_code=400, detail="Incorrect parameters")
    delete_deploy_instance = k8sDeploymentManager(client_config_path, namespace_name)
    result_data = delete_deploy_instance.delete_kube_deployment(namespace_name, app_name)
    if result_data.get("code") == 0:
        delete_instance = delete_db_svc(request_data.id)
        insert_ops_bot_log("Delete kube Deploy App", json.dumps(userRequestData), "delete", json.dumps(deleteInstance))
        return delete_instance
    else:
        raise HTTPException(status_code=400, detail="Delete deploy App failure")


class CreateIngressK8S(BaseModel):
    env: str
    cluster_name: str
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
    env: str
    cluster_name: str
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
    env: str
    cluster_name: str
    namespace: str
    ingress_name: str
    client_config_path: str


@app.post("/v1/k8s/ingress/plan/", summary="Add Ingress App Plan", tags=["IngressKubernetes"])
async def post_ingress_plan(ReQuest: Request, request_data: CreateIngressK8S, db: Session = Depends(get_db)):
    user_request_data = await ReQuest.json()
    namespace_name = request_data.namespace
    ingres_name = request_data.ingress_name
    host_name = request_data.host
    svc_name = request_data.svc_name
    svc_port = request_data.svc_port
    client_config_path = request_data.client_config_path
    used = request_data.used

    if not all([namespace_name, ingres_name, host_name, svc_name, svc_port, client_config_path, used]):
        raise HTTPException(status_code=400, detail="Invalid request data")

    ingress = crud.get_ingress_by_name(db, ingress_name=ingres_name)
    if ingress:
        raise HTTPException(status_code=409, detail=f"Ingress {ingres_name} already exists")

    try:
        api_instance = client.ExtensionsV1beta1Api(client.Configuration.from_kube_config(client_config_path))
        body = client.V1beta1Ingress(
            metadata=client.V1ObjectMeta(name=ingres_name),
            spec=client.V1beta1IngressSpec(
                rules=[
                    client.V1beta1IngressRule(
                        host=host_name,
                        http=client.V1beta1HTTPIngressRuleValue(
                            paths=[
                                client.V1beta1HTTPIngressPath(
                                    path=request_data.path,
                                    backend=client.V1beta1IngressBackend(
                                        service_name=svc_name,
                                        service_port=svc_port
                                    )
                                )
                            ]
                        )
                    )
                ]
            )
        )
        api_instance.create_namespaced_ingress(namespace_name, body)
    except ApiException as e:
        raise HTTPException(status_code=500, detail=str(e))

    created_ingress = crud.create_ingress(
        db=db,
        ingress=schemas.IngressK8sDataCreate(
            namespace=namespace_name,
            ingress_name=ingres_name,
            host=host_name,
            svc_name=svc_name,
            svc_port=svc_port,
            path=request_data.path,
            path_type=request_data.path_type,
            ingress_class_name=request_data.ingress_class_name,
            tls=request_data.tls,
            tls_secret=request_data.tls_secret,
            used=used
        )
    )
    insert_ops_bot_log("Insert kube ingress app ", json.dumps(user_request_data), "post",
                       json.dumps(created_ingress))
    return created_ingress


@app.put("/v1/k8s/ingress/plan/", summary="Change Ingress App Plan", tags=["IngressKubernetes"])
async def put_ingress_plan(request: Request, data: UpdateIngressK8S):
    item_dict = data.dict()
    user_request_data = await request.json()
    namespace_name = data.namespace
    ingres_name = data.ingress_name
    host_name = data.host
    svc_name = data.svc_name
    svc_port = data.svc_port
    client_config_path = data.client_config_path
    used = data.used
    if not (namespace_name and ingres_name and host_name and svc_name and svc_port and client_config_path and used):
        return {'code': 1, 'messages': "If the parameter is insufficient, check it", "data": "", "status": False}
    update_ingress_instance = k8sIngressManager(data.client_config_path, data.namespace)
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
        with Session(engine) as session:
            result = updata_db_ingress(
                session,
                item_dict.get("id"),
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
async def delete_ingress_plan(request: Request, request_data: deleteIngressK8S):
    data = request_data.dict()
    if not all(data.values()):
        return {"code": 1, "messages": "Delete Ingress App failure, Incorrect parameters", "status": True,
                "data": "failure"}
    ingress_manager = K8sIngressManager(data["client_config_path"], data["namespace"])
    result_data = ingress_manager.delete_kube_ingress(data["namespace"], data["ingress_name"])
    if result_data["code"] == 0:
        delete_instance = DeleteDeployK8S(data["id"])
        insert_ops_bot_log("Delete kube Ingress App", await request.json(), "delete", delete_instance.json())
        return delete_instance
    else:
        return {"code": 1, "messages": "delete Ingress App failure", "status": True, "data": "failure"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8888, log_level="debug")
