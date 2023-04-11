"""
1.nacos 配置信息
"""
nacos_config = {"nacos_server_address": "http://localhost:8848",
                "namespace": "ops-k8s",
                "username": "nacos",
                "password": "nacos",
                "group": "DEFAULT_GROUP"
                }

queryClusterURL = "http://0.0.0.0:8888/v1/kube/config"

# K8S集群配置前端显示表头
k8sClusterHeader = [
    {"name": "env", "alias": "环境"},
    {"name": "cluster_name", "alias": "集群标识"},
    {"name": "server_address", "alias": "集群地址"},
    {"name": "ca_data", "alias": "集群CA"},
    {"name": "client_crt_data", "alias": "客户端证书"},
    {"name": "client_key_data", "alias": "客户端密钥"},
    {"name": "client_key_path", "alias": "证书路径"}
]
# K8S 命名空间 前端显示表头
k8sNameSpaceHeader = [
    {"name": "env", "alias": "环境"},
    {"name": "cluster_name", "alias": "集群标识"},
    {"name": "ns_name", "alias": "命名空间"},
    {"name": "used", "alias": "用途"},
    {"name": "create_time", "alias": "创建时间"}
]


# K8S deploy 前端显示表头
k8sDeployHeader = [
    {"name": "app_name", "alias": "应用名称"},
    {"name": "env", "alias": "环境"},
    {"name": "cluster", "alias": "集群"},
    {"name": "namespace", "alias": "命名空间"},
    {"name": "resources", "alias": "资源规格"},
    {"name": "replicas", "alias":  "副本"},
    {"name": "image", "alias": "镜像地址"},
    {"name": "deploy_env", "alias": "环境变量"},
    {"name": "ports", "alias": "应用端口"},
    {"name": "deploy_time", "alias": "创建时间"}
]
k8sServiceHeader = [
    {"name": "svc_name", "alias": "服务名称"},
    {"name": "env", "alias": "环境"},
    {"name": "cluster", "alias": "集群"},
    {"name": "namespace", "alias": "命名空间"},
    {"name": "selector_labels", "alias": "关联labels"},
    {"name": "svc_port", "alias":  "服务port"},
    {"name": "svc_type", "alias": "SVC类型"},
    {"name": "target_port", "alias": "应用端口"},
    {"name": "create_time", "alias": "创建时间"},
]

k8sIngressHeader = [
    {"name": "ingress_name", "alias": "ingress名称"},
    {"name": "env", "alias": "环境"},
    {"name": "cluster_name", "alias": "集群"},
    {"name": "namespace", "alias": "命名空间"},
    {"name": "host", "alias": "域名"},
    {"name": "svc_name", "alias":  "SVC名称"},
   #  {"name": "path", "alias": "请求路径"},
   # {"name": "tls", "alias": "是否TLS"},
    {"name": "svc_port", "alias": "端口"},
    {"name": "used", "alias": "用途"},
]
