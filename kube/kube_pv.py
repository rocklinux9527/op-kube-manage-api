from kubernetes import client, config
from kubernetes.client.rest import ApiException
from kube.kube_config import get_kube_namespace
# https://www.jianshu.com/p/84ca2edc80e8

class k8sPvManager():
    def __init__(self, clint_config_file, namespace="default"):
        self.client_config = clint_config_file
        self.namespace = namespace
        config.load_kube_config(config_file=self.client_config)
        self.v1 = client.CoreV1Api()

    def get_kube_pv(self):
        """
        1.获取pv卷
        :return:
        """
        pvList = []
        for pv in self.v1.list_persistent_volume().items:
            name = pv.metadata.name
            capacity = pv.spec.capacity["storage"]
            access_modes = pv.spec.access_modes
            reclaim_policy = pv.spec.persistent_volume_reclaim_policy
            status = pv.status.phase
            if pv.spec.claim_ref is not None:
                pvc_ns = pv.spec.claim_ref.namespace
                pvc_name = pv.spec.claim_ref.name
                pvc = "%s / %s" % (pvc_ns, pvc_name)
            else:
                pvc = "未绑定"
            storage_class = pv.spec.storage_class_name
            create_time = pv.metadata.creation_timestamp
            pvList.append({"name": name, "capacity": capacity, "access_modes": access_modes,
                           "reclaim_policy": reclaim_policy, "status": status, "pvc": pvc,
                           "storage_class": storage_class, "create_time": create_time})
        return pvList

    def create_kube_pv(self, pv_name, capacity, access_mode, storage_type, server_ip, mount_path):
        """
        1.创建pv参数,支持nfs pv
        :param pv_name:
        :param capacity:
        :param access_mode:
        :param storage_type:
        :param server_ip:
        :param mount_path:
        :return:
        """
        body = client.V1PersistentVolume(
            api_version="v1",
            kind="PersistentVolume",
            metadata=client.V1ObjectMeta(name=name),
            spec=client.V1PersistentVolumeSpec(
                capacity={'storage':capacity},
                access_modes=[access_mode],
                nfs=client.V1NFSVolumeSource(
                    server=server_ip,
                    path="/ifs/kubernetes/%s" %mount_path
                )
            )
        )
        self.v1.create_persistent_volume(body=body)

    def delete_kube_pv(self, pv_name):
        """
        1.删除pv
        :param pv_name:
        :return:
        """
        self.v1.delete_persistent_volume(name=pv_name)


if __name__ == "__main__":
    client_config = "/Users/lijianxing/lijx-devops/python/fastapi/op-kube-manage-api/conf/kubeconf/dev_k8s-cluster-service.conf"
    pv_instance = k8sPvManager(client_config)
    data = pv_instance.get_kube_pv()
    print(data)
