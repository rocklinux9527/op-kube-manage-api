from kubernetes import client, config
from kubernetes.client.rest import ApiException
from kube.kube_config import get_kube_namespace


class k8sPvcManager():
    def __init__(self, clint_config_file, namespace="default"):
        self.client_config = clint_config_file
        self.namespace = namespace
        config.load_kube_config(config_file=self.client_config)
        self.v1 = client.CoreV1Api()

    def get_kube_pvc(self):
        """
        1.查询pvc
        :return:
        """
        pvcList = []
        for pvc in self.v1.list_namespaced_persistent_volume_claim(namespace=self.namespace).items:
            name = pvc.metadata.name
            namespace = pvc.metadata.namespace
            labels = pvc.metadata.labels
            storage_class_name = pvc.spec.storage_class_name
            access_modes = pvc.spec.access_modes
            capacity = (pvc.status.capacity if pvc.status.capacity is None else pvc.status.capacity["storage"])
            volume_name = pvc.spec.volume_name
            status = pvc.status.phase
            create_time = pvc.metadata.creation_timestamp
            pvcList.append({"code": 0, "name": name, "namespace": namespace, "lables": labels,
                            "storage_class_name": storage_class_name, "access_modes": access_modes, "capacity": capacity,
                            "volume_name": volume_name, "status": status, "create_time": create_time})
        return pvcList

    def create_kube_pvc(self, pvc_name, access_mode, capacity=100, storage_class="", ):
        """
        1.pvc名称,访问权限,容量, 动态卷名
        :return:
        """
        access_mode_list = ["ReadWriteOnce", "ReadOnlyMany", "ReadWriteMany", "ReadWriteOncePod"]
        if access_mode in access_mode_list:
            if storage_class and capacity >= 10 and capacity < 500:
                body = client.V1PersistentVolumeClaim(
                    api_version="v1",
                    kind="PersistentVolumeClaim",
                    metadata=client.V1ObjectMeta(name=pvc_name, namespace=self.namespace),
                    spec=client.V1PersistentVolumeClaimSpec(
                        storage_class_name=storage_class,  # 使用存储类创建PV，如果不用可去掉
                        access_modes=[access_mode],
                        resources=client.V1ResourceRequirements(
                            requests={"storage": str(capacity) + "Gi"}
                        )
                    )
                )
                data = self.v1.create_namespaced_persistent_volume_claim(namespace=self.namespace, body=body)
                print(data)
            else:
                body = client.V1PersistentVolumeClaim(
                    api_version="v1",
                    kind="PersistentVolumeClaim",
                    metadata=client.V1ObjectMeta(name=pvc_name, namespace=self.namespace),
                    spec=client.V1PersistentVolumeClaimSpec(
                        access_modes=[access_mode],
                        resources=client.V1ResourceRequirements(
                            requests={"storage": str(capacity) + "Gi"}
                        )
                    )
                )
                data = self.v1.create_namespaced_persistent_volume_claim(namespace=self.namespace, body=body)
                print(data)
        else:
            return {"code": 1,
                    "messages": "Parameter {args} does not exist, Support list "
                                "[ReadWriteOnce, ReadOnlyMany, ReadWriteMany]".format(args=access_mode)}

    def delete_kube_pvc(self, pvc_name):
        """
        1.卷名
        :param pvc_name:
        :return:
        """
        ""
        data = self.v1.delete_namespaced_persistent_volume_claim(namespace=self.namespace, name=pvc_name)
        print(data)


if __name__ == "__main__":
    client_config = "/Users/lijianxing/lijx-devops/python/fastapi/op-kube-manage-api/conf/kubeconf/dev_k8s-cluster-service.conf"
    pvc_instance = k8sPvcManager(client_config)
    # print(pvc_instance.get_kube_pvc())
    # pvc_instance = k8sPvcManager(client_config)
    data = pvc_instance.create_kube_pvc("demo-nginx-04", "ReadWriteOnce", 600)
    # pvc_instance.delete_kube_pvc("demo-nginx-01")
    print(data)
