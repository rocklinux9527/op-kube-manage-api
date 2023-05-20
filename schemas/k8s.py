from pydantic import BaseModel

class KubeConfig(BaseModel):
    """k8s Kube config 新增模型"""
    env: str
    cluster_name: str
    server_address: str
    ca_data: str
    client_crt_data: str
    client_key_data: str

class updateKubeConfig(BaseModel):
    """k8s Kube config 更新模型"""
    id: int
    env: str
    cluster_name: str
    server_address: str
    ca_data: str
    client_crt_data: str
    client_key_data: str
    client_key_path: str

class deleteKubeConfig(BaseModel):
    """k8s Kube config 删除模型"""
    id: int
    env: str
    cluster_name: str

class createNameSpace(BaseModel):
    """k8s namespace 命名空间增加模型"""
    env: str
    cluster_name: str
    ns_name: str
    used: str


class CreateDeployK8S(BaseModel):
    """k8s Deployment 增加模型"""
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
    """k8s Deployment 更新模型"""
    deployment_name: str
    id: int
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
    """k8s Deployment 删除模型"""
    id: int
    env: str
    cluster: str
    app_name: str
    namespace: str


class postK8sRestartPodManager(BaseModel):
    """k8s pod重启 数据模型"""
    env: str
    cluster: str
    namespace: str
    pod_name: str


class postK8sPodManager(BaseModel):
    """k8s pod新增数据模型"""
    env: str
    cluster: str
    namespace: str
    pod_name: str
    ports: int
    image: str


class putK8sPodManager(BaseModel):
    """k8s pod修改数据模型"""
    env: str
    cluster: str
    namespace: str
    pod_name: str
    ports: int
    image: str

class CreateSvcK8S(BaseModel):
    """k8s service 增加、数据模型"""
    env: str
    cluster_name: str
    namespace: str
    svc_name: str
    selector_labels: str = "app=web,name=test_svc"
    svc_port: int
    svc_type: str = "ClusterIP"
    target_port: int


class UpdateSvcK8S(BaseModel):
    """k8s service 更新数据模型"""
    id: int
    env: str
    cluster_name: str
    namespace: str
    svc_name: str
    selector_labels: str
    svc_port: int
    svc_type: str = "ClusterIP"
    target_port: int


class deleteSvcK8S(BaseModel):
    """k8s service 删除数据模型"""
    id: int
    env: str
    cluster_name: str
    namespace: str
    svc_name: str

class CreateIngressK8S(BaseModel):
    """k8s Ingress 增加数据模型"""
    env: str
    cluster_name: str
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
    """k8s Ingress 更新模型"""
    id: int
    env: str
    cluster_name: str
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
    """k8s Ingress 删除模型"""
    id: int
    env: str
    cluster_name: str
    namespace: str
    ingress_name: str
