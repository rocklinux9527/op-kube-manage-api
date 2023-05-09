import logging
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from kube.kube_config import get_kube_namespace

class k8sDeploymentManager:
    def __init__(self, client_config_file, namespace="default"):
        self.client_config = client_config_file
        self.namespace = namespace
        config.load_kube_config(config_file=self.client_config)
        self.apps_api = client.AppsV1Api()

    def get_kube_deployment(self):
        """
        1.获取指定namespace空间下所有deployment资源对象
        :return: list 包含deployment资源对象信息的列表
        """
        try:
            data = self.apps_api.list_namespaced_deployment(namespace=self.namespace).items
            return [{
                "code": 0,
                "messages": "success",
                "name": i.metadata.name,
                "namespace": i.metadata.namespace,
                "replicas": i.spec.replicas,
                "ready": "{a}/{b}".format(a=i.status.available_replicas, b=i.status.ready_replicas),
                "status": True
            } for i in data]
        except ApiException as e:
            logging.error(str(e))
            return [{
                "code": 1,
                "messages": str(e),
                "data": "",
                "status": False
            }]

    def get_kube_deployment_by_name(self, app_name):
        """
        1.跟进应用名称查询deployment资源对象.要求应用必须存在
        :return: dict 包含deployment资源对象信息的字典
        """
        data = self.get_kube_deployment()
        try:
            return next(i for i in data if i["name"] == app_name)
        except StopIteration:
            logging.error("the application does not exist. check the name of the cluster application")
            return {
                "code": 1,
                "messages": "the application does not exist. check the name of the cluster application",
                "data": "",
                "status": False
            }

    def create_kube_deployment(self, namespace, deployment_name, resources, replicas, image, env_vars, container_port, health_liven_ess=None, health_readiness=None):
        """
        1.命名空间和body内容
        :param ns: str 命名空间名称deploy_env
        :param deployment_name: str deployment名称
        :param resources: str 资源名称
        :param replicas: int 副本数
        :param image: str 镜像名称
        :param env: dict 环境变量
        :param container_port: int 容器启动端口
        :param health_liven_ess: str 是否开启活性探针
        :param health_readiness: str 是否开启可读探针
        :return: dict 返回操作结果
        """
        try:
            labels = {'app': deployment_name}
            for dp in self.apps_api.list_namespaced_deployment(namespace=self.namespace).items:
                if deployment_name == dp.metadata.name:
                    return {"code": 1, "messages": "Deployment已经存在！", "data": "", "status": False }

            resources_dict = {
                "1c2g": client.V1ResourceRequirements(limits={"cpu": "1", "memory": "2Gi"},
                                                      requests={"cpu": "0.9", "memory": "1.9Gi"}),
                "2c4g": client.V1ResourceRequirements(limits={"cpu": "2", "memory": "4Gi"},
                                                      requests={"cpu": "1.9", "memory": "3.9Gi"}),
                "4c8g": client.V1ResourceRequirements(limits={"cpu": "4", "memory": "8Gi"},
                                                      requests={"cpu": "3.9", "memory": "7.9Gi"}),
            }
            resources = resources_dict.get(resources, client.V1ResourceRequirements(limits={"cpu": "500m", "memory": "1Gi"},
                                                                                    requests={"cpu": "450m", "memory": "900Mi"}))
            if not health_liven_ess and not health_readiness:
                # 创建Deployment
                body = client.V1Deployment(
                    api_version="apps/v1",
                    kind="Deployment",
                    metadata=client.V1ObjectMeta(name=deployment_name, labels=labels),
                    spec=client.V1DeploymentSpec(
                        replicas=replicas,
                        selector={'matchLabels': labels},
                        template=client.V1PodTemplateSpec(
                            metadata=client.V1ObjectMeta(labels=labels),
                            spec=client.V1PodSpec(
                                containers=[client.V1Container(
                                    name=deployment_name,
                                    image=image,
                                    ports=[client.V1ContainerPort(container_port=container_port)],
                                    env=[client.V1EnvVar(name=key, value=value) for key, value in env_vars.items()],
                                    resources=resources
                                )]
                            )
                        )
                    )
                )
            else:
                container = client.V1Container(
                    env=[client.V1EnvVar(name=key, value=value) for key, value in env_vars.items()],
                    name=deployment_name,
                    image=image,
                    resources=resources,
                    ports=[client.V1ContainerPort(container_port=container_port)],
                    liveness_probe=client.V1Probe(
                        http_get=client.V1HTTPGetAction(
                            path=health_liven_ess,
                            port=container_port),
                        period_seconds=10,
                        initial_delay_seconds=15,
                        timeout_seconds=5,
                        failure_threshold=3),
                    readiness_probe=client.V1Probe(
                        http_get=client.V1HTTPGetAction(
                            path=health_readiness,
                            port=container_port),
                        initial_delay_seconds=15,
                        timeout_seconds=5,
                        period_seconds=10,
                        failure_threshold=3))
                template = client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels=labels),
                    spec=client.V1PodSpec(
                        restart_policy="Always",
                        containers=[container]))
                spec = client.V1DeploymentSpec(
                    replicas=1,
                    selector=client.V1LabelSelector(
                        match_labels={"app": deployment_name}),
                    template=template)
                body = client.V1Deployment(
                    api_version="apps/v1",
                    kind="Deployment",
                    metadata=client.V1ObjectMeta(name=deployment_name, labels=labels),
                    spec=spec)
                data = self.apps_api.create_namespaced_deployment(namespace=namespace, body=body)
                return {
                    "code": 20000,
                    "messages": "Create Deployment Success ",
                    "data": data,
                    "status": True
                }
        except ApiException as e:
            logging.error(str(e))
            status = getattr(e, "status")
            if status == 400:
                msg = "Deployment Invalid format"
            elif status == 403:
                msg = "No permission"
            elif status == 409:
                msg = "Create Deployment failure: App Deployment exist"
            elif status == 404:
                msg = f"Create Deployment failure: Namespace {namespace} not found"
            else:
                msg = "Create Deployment failure"
            return {"code": 50000, "messages": msg, "data": "", "status": False}

    def delete_kube_deployment(self, namespace, deploy_name):
        """
        1.输入命名空间和deployment名称
        :param namespace: str 命名空间名称
        :param deploy_name: str deployment名称
        :return: dict 返回操作结果
        """
        try:
            data = self.apps_api.delete_namespaced_deployment(namespace=namespace, name=deploy_name)
            return {"code": 0, "messages": "delete deployment success", "data": "delete deployment success",
                    "status": True}
        except ApiException as e:
            logging.error(str(e))
            status = getattr(e, "status")
            if status == 404:
                msg = "delete deployment failure: deployment not existing"
            else:
                msg = "delete deployment failure"
            return {"code": 1, "messages": msg, "data": "", "status": False}

    def replace_kube_deployment(self, deployment_name, replicas, image, namespace, resources, env_vars, container_port, health_liven_ess=None, health_readiness=None):
        """
        1.修改deployment资源对象
        :param deployment_name: str deployment名称
        :param namespace: str 命名空间名称
        :return: None
        """
        resources_dict = {
            "1c2g": client.V1ResourceRequirements(limits={"cpu": "1", "memory": "2Gi"},
                                                  requests={"cpu": "0.9", "memory": "1.9Gi"}),
            "2c4g": client.V1ResourceRequirements(limits={"cpu": "2", "memory": "4Gi"},
                                                  requests={"cpu": "1.9", "memory": "3.9Gi"}),
            "4c8g": client.V1ResourceRequirements(limits={"cpu": "4", "memory": "8Gi"},
                                                  requests={"cpu": "3.9", "memory": "7.9Gi"}),
        }
        resources = resources_dict.get(resources, client.V1ResourceRequirements(limits={"cpu": "500m", "memory": "1Gi"},
                                                                                requests={"cpu": "450m", "memory": "900Mi"}))
        try:
            labels = {'app': deployment_name}
            if not health_liven_ess and not health_readiness:
                labels = {'app': deployment_name}
                body = client.V1Deployment(
                    api_version="apps/v1",
                    kind="Deployment",
                    metadata=client.V1ObjectMeta(name=deployment_name, labels=labels),
                    spec=client.V1DeploymentSpec(
                        replicas=replicas,
                        selector={'matchLabels': labels},
                        template=client.V1PodTemplateSpec(
                            metadata=client.V1ObjectMeta(labels=labels),
                            spec=client.V1PodSpec(
                                containers=[client.V1Container(
                                    name=deployment_name,
                                    image=image,
                                    ports=[client.V1ContainerPort(container_port=container_port)],
                                    env=[client.V1EnvVar(name=key, value=value) for key, value in env_vars.items()],
                                    resources=resources
                                )]
                            )
                        ),
                    )
                )
                data = self.apps_api.replace_namespaced_deployment(deployment_name, namespace, body)
                return {
                    "code": 0,
                    "messages": "Update Deployment Success ",
                    "data": data,
                    "status": True
                }
            else:
                container = client.V1Container(
                    env=[client.V1EnvVar(name=key, value=value) for key, value in env_vars.items()],
                    name=deployment_name,
                    image=image,
                    resources=resources,
                    ports=[client.V1ContainerPort(container_port=container_port)],
                    liveness_probe=client.V1Probe(
                        http_get=client.V1HTTPGetAction(
                            path=health_liven_ess,
                            port=container_port),
                        period_seconds=10,
                        initial_delay_seconds=15,
                        timeout_seconds=5,
                        failure_threshold=3),
                    readiness_probe=client.V1Probe(
                        http_get=client.V1HTTPGetAction(
                            path=health_readiness,
                            port=container_port),
                        initial_delay_seconds=15,
                        timeout_seconds=5,
                        period_seconds=10,
                        failure_threshold=3))
                template = client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels=labels),
                    spec=client.V1PodSpec(
                        restart_policy="Always",
                        containers=[container]))
                spec = client.V1DeploymentSpec(
                    replicas=replicas,
                    selector=client.V1LabelSelector(
                        match_labels={"app": deployment_name}),
                    template=template)
                body = client.V1Deployment(
                    api_version="apps/v1",
                    kind="Deployment",
                    metadata=client.V1ObjectMeta(name=deployment_name, labels=labels),
                    spec=spec)
                data = self.apps_api.replace_namespaced_deployment(deployment_name, namespace, body)
                return {
                    "code": 0,
                    "messages": "Update Deployment Success ",
                    "data": data,
                    "status": True
                }
        except ApiException as e:
            logging.error(str(e))
            status = getattr(e, "status")
            if status == 400:
                msg = "Deployment Invalid format"
            elif status == 403:
                msg = "No permission"
            elif status == 409:
                msg = "Update Deployment failure: App Update exist"
            elif status == 404:
                msg = f"Update Deployment failure: Namespace {namespace} not found"
            else:
                msg = "Update Deployment failure"
            return {"code": 1, "messages": msg, "data": "", "status": False}

# if __name__ == "__main__":
#     client_config = "/Users/lijianxing/lijx-devops/python/fastapi/op-kube-manage-api/conf/kubeconf/dev_k8s-cluster-service.conf"
#     k8s_instance = k8sDeploymentManager(client_config)
#     result = k8s_instance.create_kube_deployment("default", "k8s-nginx-web6", "1c2g", 1, "nginx", {"name": "value"}, 80)
#     print(result)

""" startup_probe_path 逻辑
from kubernetes import client, config
config.load_kube_config()
deployment_name = "test-deployment"
container_port = 80
image = "nginx"
liveness_probe_path = "/healthz"
startup_probe_path = "/healthz-startup"
# Deployment 基本信息
metadata = client.V1ObjectMeta(name=deployment_name)
spec = client.V1DeploymentSpec(
    replicas=1,
    selector=client.V1LabelSelector(
        match_labels={"app": deployment_name}),
    template=client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(name=deployment_name),
        spec=client.V1PodSpec(
            containers=[client.V1Container(
                name=deployment_name,
                image=image,
                ports=[client.V1ContainerPort(container_port=container_port)],
                liveness_probe=client.V1Probe(
                    http_get=client.V1HTTPGetAction(
                        path=liveness_probe_path,
                        port=container_port),
                    period_seconds=10,
                    initial_delay_seconds=15,
                    timeout_seconds=5,
                    failure_threshold=3),
                startup_probe=client.V1Probe(
                    http_get=client.V1HTTPGetAction(
                        path=startup_probe_path,
                        port=container_port),
                    period_seconds=10,
                    initial_delay_seconds=10,
                    failure_threshold=30))))
)

deployment = client.V1Deployment(
    api_version="apps/v1",
    kind="Deployment",
    metadata=metadata,
    spec=spec
)

apps_v1_api = client.AppsV1Api()
response = apps_v1_api.create_namespaced_deployment(
    namespace="default",
    body=deployment
)
print("Deployment created. status='%s'" % response.metadata.self_link)
"""
