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
         1.获取指定namespace空间下 所有deployment 资源对象
        :return:
        """

        data = self.apps_api.list_namespaced_deployment(namespace=self.namespace)
        try:
            return [{
                "code": 0,
                "messages": "success",
                "name": i.metadata.name,
                "namespace": i.metadata.namespace,
                "replicas": i.spec.replicas,
                "ready": "{a}/{b}".format(a=i.status.available_replicas, b=i.status.ready_replicas),
                "status": True
            } for i in data.items]
        except Exception as e:
            print(str(e))
            return [{
                "code": 1,
                "messages": str(e),
                "data": "",
                "status": False
            }]

    def get_kube_deployment_by_name(self, app_name):
        """
        1.跟进应用名称查询 deployment 资源对象.要求应用必须存
        :return:
        """
        data = self.get_kube_deployment()
        try:
            return [i for i in data if i["name"] == app_name][0]
        except Exception as e:
            status = getattr(e, "status")
            return [{
                "code": 1,
                "messages": str(e),
                "data": "the application does not exist. check the name of the cluster application",
                "status": False
            }]

    def create_kube_deployment(self, ns, deployment_name, resources, replicas, image, env, container_port, health_liven_ess="on", health_readiness="on"):
        """
        1.命名空间和body 内容
        :param ns:
        :param body:
        :return:
        """
        labels = {'app': deployment_name}
        if isinstance(env, dict) and isinstance(container_port, int):
            if resources == "1c2g":
                resources = client.V1ResourceRequirements(limits={"cpu": "1", "memory": "2Gi"},
                                                          requests={"cpu": "0.9", "memory": "1.9Gi"})
            elif resources == "2c4g":
                resources = client.V1ResourceRequirements(limits={"cpu": "2", "memory": "4Gi"},
                                                          requests={"cpu": "1.9", "memory": "3.9Gi"})
            elif resources == "4c8g":
                resources = client.V1ResourceRequirements(limits={"cpu": "4", "memory": "8Gi"},
                                                          requests={"cpu": "3.9", "memory": "7.9Gi"})
            else:
                resources = client.V1ResourceRequirements(limits={"cpu": "500m", "memory": "1Gi"},
                                                          requests={"cpu": "450m", "memory": "900Mi"})

            # liveness_probe = ""
            # if health_liven_ess == "on":
            #     liveness_probe = client.V1Probe(http_get="/", timeout_seconds=30, initial_delay_seconds=30)
            # readiness_probe = ""
            # if health_readiness == "on":
            #     readiness_probe = client.V1Probe(http_get="/", timeout_seconds=30, initial_delay_seconds=30)

            for dp in self.apps_api.list_namespaced_deployment(namespace=self.namespace).items:
                if deployment_name == dp.metadata.name:
                    res = {"code": 1, "messages": "Deployment已经存在！", "data": "", "status": False }
                    return res

            if ns and deployment_name and replicas and image:
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
                        ),
                    )
                )
                try:
                    data = self.apps_api.create_namespaced_deployment(namespace=ns, body=body)
                    if data:
                        return {
                            "code": 0,
                            "messages": "Create Deployment Success ",
                            "data": data,
                            "status": True
                        }
                except Exception as e:
                    print(e)
                    status = getattr(e, "status")
                    if status == 400:
                        msg = "Deployment Invalid format"
                    elif status == 403:
                        msg = "No permission"
                        return {"code": 1, "messages": msg, "data": "", "status": False}
                    elif status == 409:
                        msg = "Create Deployment failure App Deployment exist"
                        return {"code": 1, "messages": msg, "data": "", "status": False}
                    elif status == 404:
                        msg = "Create Deployment failure  Namespace {ns} not found".format(ns=ns)
                        return {"code": 1, "messages": msg, "data": "", "status": False}
        else:
            msg = " Deployment env  It doesn't work properly unless it exists and container_port is exists "
            return {"code": 1, "messages": msg, "data": "", "status": False}

    def delete_kube_deployment(self, namespace, deploy_name):
        """
        1.输入命名空间和deployment 名称
        :param namespace:
        :param deploy_name:
        :return:
        """
        try:
            data = self.apps_api.delete_namespaced_deployment(namespace=namespace, name=deploy_name)
            return {"code": 0, "messages": "delete deployment success", "data": "delete deployment success",
                    "status": True
                    }
        except ApiException as e:
            print(e)
            status = getattr(e, "status")
            if status == 404:
                msg = "delete deployment failure, deployment not existing "
                return {"code": 1, "messages": msg, "data": "", "status": False}

    def replace_kube_deployment(self, deployment_name, replicas, image, namespace):
        labels = {'app': deployment_name}
        """
        1.修改deployment资源对象
        :param deployment_name:
        :param namespace:
        :param body:
        :return:
        """
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
        self.apps_api.replace_namespaced_deployment(deployment_name, namespace, body)


if __name__ == "__main__":
    client_config = "/Users/lijianxing/lijx-devops/python/fastapi/op-kube-manage-api/conf/kubeconf/dev_k8s-cluster-service.conf"
    k8s_instance = k8sDeploymentManager(client_config)
    # app_name = k8s_instance.get_kube_deployment()
    # data = k8s_instance.get_kube_deployment_by_name("demo-test-nginx1")
    # print(data)
    # print(app_name)

    result = k8s_instance.create_kube_deployment("default", "k8s-nginx-web6", "1c2g", 1, "nginx")
    # result = k8s_instance.delete_kube_deployment("default", "demo-web-server")
    # result = k8s_instance.replace_kube_deployment("k8s-nginx-web3", 2, "nginx", "default")
    # # result = k8s_instance.create_kube_namespaces("prod")
    print(result)
