from kubernetes import client, config
from kubernetes.client.rest import ApiException
from kube.kube_config import get_kube_namespace


class k8sIngressManager():
    def __init__(self, client_config_file, namespace):
        self.namespace = namespace
        self.client_config_file = client_config_file
        config.load_kube_config(config_file=self.client_config_file)
        networking_api = client.NetworkingV1Api()

    def get_kube_ingress_all(self):
        config.load_kube_config(config_file=self.client_config_file)
        networking_api = client.NetworkingV1Api()
        # data = networking_api.list_namespaced_ingress(namespace=self.namespace)
        ingNameList = []
        reslt = networking_api.list_ingress_for_all_namespaces().items
        for ing in reslt:
            ingNameDict = {}
            ingNameDict["namespace"] = ing.metadata.namespace
            ingNameDict["name"] = ing.metadata.name
            ingNameDict["create_time"] = ing.metadata.creation_timestamp
            if ing.metadata.labels == None:
                ingNameDict["labels"] = ""
            else:
                ingNameDict["labels"] = ing.metadata.labels
            ingNameList.append(ingNameDict)
        return ingNameList
        # print(ingNameList)
        # rulesList = []
        # try:
        #     data = {"code": 0, "data": rulesList, "messages": "success", "status": True}
        #     resut2 = networking_api.list_ingress_for_all_namespaces().items
        #     for ing in resut2:
        #         for y in ing.spec.rules:
        #             rulesList.append(y.host)
        #             rulesList.append(y.http.paths)
        # except Exception as e:
        #     data = {"code": 0, "data": str(e), "messages": "success", "status": True}
        # return data
        # service = "None"
        # http_hosts = "None"
        # for h in ing.spec.rules:
        #     host = h.host
        #     path_type = ("Prefix" if h.http.paths[0].path_type is None else h.http.paths[0].path_type)
        #     path = ("/" if h.http.paths[0].path is None else h.http.paths[0].path)
        #     service_name = h.http.paths[0].backend.service.name
        #     service_port = h.http.paths[0].backend.service.port.number
        #     http_hosts = {'host': host, 'path': path, 'path_type': 'path_type', 'service_name':service_name, 'service_port': service_port}
        # print(http_hosts)

        # for y in ing.spec.rules:
        #     host = y.host
        #     path_type = ("Prefix" if y.http.paths[1].path_type is None else y.http.paths[0].path_type)
        #     path = ("/" if y.http.paths[1].path is None else y.http.paths[0].path)
        #     service_name = y.http.paths[1].backend.service.name
        #     service_port = y.http.paths[1].backend.service.port.number
        #     http_hosts_y = {'host': host, 'path': path, 'path_type': 'path_type', 'service_name':service_name, 'service_port': service_port}
        # print(http_hosts_y)
        # #https_hosts = "None"
        # # if ing.spec.tls is None:
        # #     print(ing.spec.tls)
        # #     https_hosts = ing.spec.tls
        # # else:
        # #     for tls in ing.spec.tls:
        # #         host = tls.hosts[0]
        # #         secret_name = tls.secret_name
        # #         https_hosts = {'host': host, 'secret_name': secret_name}
        # # print(https_hosts)
        # ing = {"name": ingNameList.get("name"), "namespace": "", "labels": "", "http_hosts": http_hosts,
        #        "https_hosts": https_hosts, "service": http_hosts.get("service_name"), "create_time": ing.metadata.creation_timestamp}
        # return ing

    def get_kube_ingress_by_name(self, env, cluster, config_file, app_name):

        data = get_kube_ingress(env, cluster, config_file)

        try:
            return [i for i in data if i["name"] == app_name][0]
        except:
            return dict()

    def create_kube_ingress(self, ingress_name, host, svc_name, svc_port, path="/",
                            path_type="Prefix", ing_class_name="nginx", tls=False, tls_secret="default-token-gq7hl"):
        """
        1.创建ingress 参数
        :param ingress_name:
        :param host:
        :param svc_name:
        :param svc_port:
        :param path:
        :return:
        """
        config.load_kube_config(config_file=self.client_config_file)
        networking_api = client.NetworkingV1Api()
        if tls:
            print("start https func ")
            runHttpsBodyData = self.kube_https_ingress_body(ingress_name, host, svc_name, svc_port, path, path_type,
                                                            ing_class_name, tls_secret)
            try:
                data = networking_api.create_namespaced_ingress(namespace=self.namespace, body=runHttpsBodyData)
                if data:
                    return {
                        "code": 0,
                        "messages": "Create Ingress Success ",
                        "data": data,
                        "status": True
                    }
            except ApiException as e:
                print(e)
                status = getattr(e, "status")
                if status == 409:
                    msg = "create {name} ingress failure, ingress not existing".format(name=ingress_name)
                    return {"code": 1, "messages": str(e), "data": "", "status": False}
        else:
            print("start http func ")
            runHttpBodyData = self.kube_http_ingress_body(ingress_name, host, svc_name, svc_port, path, path_type, ing_class_name)
            try:
                data = networking_api.create_namespaced_ingress(namespace=self.namespace, body=runHttpBodyData)
                if data:
                    return {
                        "code": 0,
                        "messages": "Create Ingress Success ",
                        "data": data,
                        "status": True
                    }
            except ApiException as e:
                print(e)
                status = getattr(e, "status")
                if status == 409:
                    msg = "create {name} ingress failure, ingress not existing".format(name=ingress_name)
                    return {"code": 1, "messages": str(e), "data": "", "status": False}

    def replace_kube_ingress(self, ingress_name, host, svc_name, svc_port, path="/", path_type="Prefix",
                             ing_class_name="nginx", tls=False, tls_secret=""):

        """
        nginx 修改
        :param ingress_name:
        :param host:
        :param svc_name:
        :param svc_port:
        :param path:
        :param path_type:
        :param ingress_class_name:
        :return:
        """
        config.load_kube_config(config_file=self.client_config_file)
        networking_api = client.NetworkingV1Api()
        if tls:
            print("start https func ")
            runHttpsBodyData = self.kube_https_ingress_body(ingress_name, host, svc_name, svc_port, path, path_type,
                                                            ing_class_name, tls_secret)
            try:
                data = networking_api.create_namespaced_ingress(namespace=self.namespace, body=runHttpsBodyData)
                if data:
                    return {
                        "code": 0,
                        "messages": "Create Ingress Success ",
                        "data": data,
                        "status": True
                    }
            except ApiException as e:
                print(e)
                status = getattr(e, "status")
                if status == 409:
                    msg = "create {name} ingress failure, ingress not existing or http change https is not supported".format(name=ingress_name)
                    return {"code": 1, "messages": str(e), "data": msg, "status": False}
        else:
            print("start http func ")
            runHttpBodyData = self.kube_http_ingress_body(ingress_name, host, svc_name, svc_port, path, path_type, ing_class_name)
            try:
                data = networking_api.replace_namespaced_ingress(name=ingress_name, namespace=self.namespace,
                                                                 body=runHttpBodyData)
                if data:
                    return {
                        "code": 0,
                        "messages": "Replace Ingress Success ",
                        "data": data,
                        "status": True
                    }
            except ApiException as e:
                print(e)
                status = getattr(e, "status")
                if status == 409:
                    msg = "replace {name} ingress failure, svc not existing".format(name=ingress_name)
                    return {"code": 1, "messages": str(e), "data": "", "status": False}

    def kube_http_ingress_body(self, ingress_name, host, svc_name, svc_port, path, path_type,
                               ing_class_name):
        """
        1.定制http body
        :param ingress_name:
        :param host:
        :param svc_name:
        :param svc_port:
        :param path:
        :param path_type:
        :param ing_class_name:
        :return:
        """
        body = client.V1Ingress(
            api_version="networking.k8s.io/v1",
            kind="Ingress",
            metadata=client.V1ObjectMeta(name=ingress_name),
            spec=client.V1IngressSpec(
                ingress_class_name=ing_class_name,
                rules=[client.V1IngressRule(
                    host=host,
                    http=client.V1HTTPIngressRuleValue(
                        paths=[client.V1HTTPIngressPath(
                            path_type=path_type,
                            path=path,
                            backend=client.V1IngressBackend(
                                service=client.V1IngressServiceBackend(
                                    name=svc_name,
                                    port=client.V1ServiceBackendPort(
                                        number=svc_port
                                    )
                                )
                            )
                        )]
                    )
                )
                ]
            )
        )
        return body

    def kube_https_ingress_body(self, ingress_name, host, svc_name, svc_port, path, path_type, ing_class_name, tls_secret):
        """
        1.定制https body
        :param ingress_name:
        :param host:
        :param svc_name:
        :param svc_port:
        :param path:
        :param path_type:
        :param ing_class_name:
        :param tls_secret:
        :return:
        """
        body = client.V1Ingress(
            api_version="networking.k8s.io/v1",
            kind="Ingress",
            metadata=client.V1ObjectMeta(name=ingress_name),
            spec=client.V1IngressSpec(
                tls=[client.V1IngressTLS(
                    hosts=[host],
                    secret_name=tls_secret
                )],
                ingress_class_name=ing_class_name,
                rules=[client.V1IngressRule(
                    host=host,
                    http=client.V1HTTPIngressRuleValue(
                        paths=[client.V1HTTPIngressPath(
                            path_type=path_type,
                            path=path,
                            backend=client.V1IngressBackend(
                                service=client.V1IngressServiceBackend(
                                    name=svc_name,
                                    port=client.V1ServiceBackendPort(
                                        number=svc_port
                                    )
                                )
                            )
                        )]
                    )
                )
                ]
            )
        )
        return body

    def delete_kube_ingress(self, namespace, ingres_name):
        """
        :param namespace:
        :param ingres_name:
        :return:
        """
        networking_api = client.NetworkingV1Api()
        try:
            data = networking_api.delete_namespaced_ingress(namespace=namespace, name=ingres_name)
            return {"code": 0, "messages": "delete success", "data": data, "status": True}
        except ApiException as e:
            print(e)
            msg = """delete {ing_name}ingress failure {msg}""".format(ing_name=ingres_name, msg=str(e))
            return {"code": 1, "messages": msg, "data": "", "status": False}


if __name__ == "__main__":
    client_config = "/Users/lijianxing/lijx-devops/python/fastapi/op-kube-manage-api/conf/kubeconf/dev_k8s-cluster.conf"
    # ingres_instance = k8sIngressManager(client_config,"dev")
    # data = ingres_instance.get_kube_ingress_all()
    # ingres_instance = k8sIngressManager(client_config, "dev")
    # # data = ingres_instance.create_kube_ingress("ops-nginx-py-01", "ops-nginx-web-2.breaklinux.com", "ops-nginx-web", 80)
    # # print(data)
    # data = ingres_instance.replace_kube_ingress("ops-nginx-py-01",
    #                                             "test-nginx-web.breaklinux.com",
    #                                             "ops-nginx-web", 80, "/")
    # print(data)
    # ingres_instance = k8sIngressManager(client_config, "dev")
    # data = ingres_instance.delete_kube_ingress("dev", "ops-nginx-py-01")
    # data = svc_instance.delete_kube_svc("default","demo-test-nginx")
    # print(data)
