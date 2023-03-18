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

    def create_kube_deployment(self, ns, deployment_name, resources, replicas, image, env, container_port, health_liven_ess="on", health_readiness="on"):
        """
        1.命名空间和body内容
        :param ns: str 命名空间名称
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
            # 处理资源配置
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
            # # 处理探针
            # liveness_probe, readiness_probe = None, None
            # if health_liven_ess == "on":
            #     liveness_probe = client.V1Probe(http_get="/", timeout_seconds=30, initial_delay_seconds=30)
            # if health_readiness == "on":
            #     readiness_probe = client.V1Probe(http_get="/", timeout_seconds=30, initial_delay_seconds=30)

            # 检查Deployment是否已存在
            for dp in self.apps_api.list_namespaced_deployment(namespace=self.namespace).items:
                if deployment_name == dp.metadata.name:
                    return {"code": 1, "messages": "Deployment已经存在！", "data": "", "status": False }

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
                                env=[env],
                                # liveness_probe=liveness_probe,
                                # readiness_probe=readiness_probe,
                                resources=resources
                            )]
                        )
                    )
                )
            )

            data = self.apps_api.create_namespaced_deployment(namespace=ns, body=body)
            return {
                "code": 0,
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
                msg = f"Create Deployment failure: Namespace {ns} not found"
            else:
                msg = "Create Deployment failure"
            return {"code": 1, "messages": msg, "data": "", "status": False}

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

    def replace_kube_deployment(self, deployment_name, replicas, image, namespace):
        """
        1.修改deployment资源对象
        :param deployment_name: str deployment名称
        :param namespace: str 命名空间名称
        :return: None
        """
        print("请求来了哈", deployment_name, replicas, image, namespace)
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
                            image=image
                        )]
                    )
                ),
            )
        )
        try:
            data = self.apps_api.replace_namespaced_deployment(deployment_name, namespace, body)
            return {
                "code": 0,
                "messages": "Update Deployment Success ",
                "data": data,
                "status": True
            }
        except ApiException as e:
            print("异常了", str(e))
            logging.error(str(e))
            status = getattr(e, "status")
            print(status)
            if status == 400:
                msg = "Deployment Invalid format"

# if __name__ == "__main__":
#     client_config = "/Users/lijianxing/lijx-devops/python/fastapi/op-kube-manage-api/conf/kubeconf/dev_k8s-cluster-service.conf"
#     k8s_instance = k8sDeploymentManager(client_config)
#     result = k8s_instance.create_kube_deployment("default", "k8s-nginx-web6", "1c2g", 1, "nginx", {"name": "value"}, 80)
#     print(result)

