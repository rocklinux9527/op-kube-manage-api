import subprocess
import sys
import yaml

class KubectlApplyExecutor:
    def __init__(self, src_file_path, dest_file_path, name=None, namespace='default', kubeconfig=None):
        """
        1.类的参数初始化
        :param src_file_path:
        :param dest_file_path:
        :param name:
        :param namespace:
        :param kubeconfig:
        """
        self.src_file_path = src_file_path
        self.dest_file_path = dest_file_path
        self.name = name
        self.namespace = namespace
        self.kubeconfig = kubeconfig

    def read_yaml(self, in_type="read_yaml"):
        """
        1.获取yaml 模版文件
        2.输入yaml in_type 值 "read_yaml" 给出yaml内容
        :param in_type:
        :return:
        """
        try:
            with open(self.src_file_path, 'r') as file:
                yaml_content = yaml.safe_load(file)
            if in_type == "read_yaml":
                return yaml_content
            else:
                return True
        except yaml.YAMLError as e:
            print(f"Error in YAML file {self.srcFilePath}: {e}")
            return False

    def write_yaml_to_file(self, yaml_content):
        """
        1.写入yaml 新的 文件路径中
        :param yaml_content:
        :return:
        """
        try:
            with open(self.dest_file_path, 'w') as file:
                yaml.dump(yaml_content, file, default_flow_style=False)

            return {"code": 200, "message": "YAML content successfully written to file.", "status": True}

        except Exception as e:
            return {"code": 500, "message": f"Error writing YAML content to file {self.dest_file_path}: {e}",
                    "status": False}

    def update_container(self,yaml_content, new_name, new_image):
        """
        1. 获取yaml 内容
        2. 更新container 容器名称
        3. 更新 container 镜像地址
        :param yaml_content:
        :param new_name:
        :param new_image:
        :return:
        """
        # 获取第一个容器
        containers = yaml_content.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [])
        if containers:
            first_container = containers[0]
            # 更新容器名称和镜像地址
            first_container['name'] = new_name
            first_container['image'] = new_image
            return True
        return False
    def update_yaml_metadata(self,yaml_content, app_name):
        """
        1.获取并检查 'spec' 和 'metadata' 部分是否为空
        2.更新name 和 labels
        3.检查 selector template 是否为空
        :param app_name:
        :return:
        """
        spec_global_metadata = yaml_content.get('spec', {})
        global_metadata = yaml_content.get('metadata', {})
        if global_metadata and spec_global_metadata:
            global_metadata['name'] = app_name
            global_metadata['labels'] = {"app": app_name}
            selector = spec_global_metadata.get('selector', {})
            template_metadata = spec_global_metadata.get('template', {}).get('metadata', {})
            if selector and template_metadata:
                spec_global_metadata['replicas'] = 1
                selector['matchLabels'] = {"app": app_name}
                template_metadata['labels'] = {"app": app_name}
                return True
        return False

    def update_spec_AntiAffinity(self, yaml_content, new_value):
        """
        1.更新yaml pod AntiAffinity 反亲和性
        :param yaml_content:
        :param new_value:
        :return:
        """
        spec_global_metadata = yaml_content.get('spec', {})
        if spec_global_metadata:
            affinity = spec_global_metadata.get('template', {}).get('spec', {}).get('affinity', {})
            pod_anti_affinity = affinity.get('podAntiAffinity', {})
            preferred_terms = pod_anti_affinity.get('preferredDuringSchedulingIgnoredDuringExecution', [])
            if preferred_terms:
                first_term = preferred_terms[0]
                pod_affinity_term = first_term.get('podAffinityTerm', {})
                label_selector = pod_affinity_term.get('labelSelector', {})
                match_expressions = label_selector.get('matchExpressions', [])
                if match_expressions:
                    first_expression = match_expressions[0]
                    values = first_expression.get('values', [])
                    if values is not None:
                        first_expression['values'] = [new_value]
                        return True
        return False

    def update_yaml(self):
        """
        1.先读取原来yaml模版内容
        2.更新yaml 容器参数替换
        :return:
        3.返回结果
        """
        new_image = "nginx:1.24.0-alpine-slim"
        new_name = "nginx-update"
        yaml_content = self.read_yaml(in_type="read_yaml")

        if new_image is not None:
            if self.update_container(yaml_content, new_name, new_image):
                print("yaml metadata  容器处理", yaml_content)
                if self.update_yaml_metadata(yaml_content, new_name):
                    print("yaml metadata  标签处理", yaml_content)
                    if self.update_spec_AntiAffinity(yaml_content, new_name):
                        print("yaml metadata pod反亲和性处理", yaml_content)
                        return yaml_content
            else:
                return {"code": 500, "message": "Container information container_name and container_image not found.",
                        "status": False}
        else:
            return {"code": 500, "message": "Key parameter missing [image, port, name, replicas]", "status": False}

    def aggregate_write(self):
        print("聚合yaml")
        update_yaml = self.update_yaml()
        if update_yaml:
            return self.write_yaml_to_file(update_yaml)
        return {"code": 500, "message": "YAML update failed.", "status": False}

    def check_kubectl_apply(self):
        """
        1.检查yaml 文件是否可以在 k8s 执行
        :return:
        """
        command = ['/usr/local/bin/kubectl', 'apply', '-f', self.dest_file_path, '--dry-run=client']
        if self.namespace:
            command.extend(['-n', self.namespace])
        try:
            subprocess.check_output(command)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error in kubectl apply check: {e}")
            return False

    def execute_kubectl_apply(self):
        """
        1.开始在k8s 执行yaml 并添加扩展参数
        :return:
        """
        command = ['/usr/local/bin/kubectl', 'apply', '-f', self.dest_file_path, '-n', self.namespace]
        if self.name:
            command.extend(['--', f"name={self.name}"])

        if self.kubeconfig:
            command.extend(['--kubeconfig', self.kubeconfig])

        try:
            subprocess.check_output(command)
            msg = f"Successfully applied {self.dest_file_path}"
            return {"code": 200, "message": msg, "status": False}
        except subprocess.CalledProcessError as e:
            msg = f"Error executing kubectl appl {self.dest_file_path} ,{e}"
            return {"code": 500, "message": msg, "status": False}


def exec_kube_main(src_file_path, dest_file_path, namespace="default", name=None, kubeconfig="/Users/li/.kube/config"):
    """
    1.入口函数 初始化类 主要逻辑入口
    :param src_file_path:
    :param dest_file_path:
    :param namespace:
    :param name:
    :param kubeconfig:
    :return:
    """
    kubectl_executor = KubectlApplyExecutor(src_file_path, dest_file_path, name, namespace, kubeconfig)
    update_content = kubectl_executor.aggregate_write()

    if update_content["code"] != 200:
        print("YAML update error ")
        sys.exit()

    if not kubectl_executor.read_yaml(in_type="read_yaml"):
        msg = "Invalid YAML file. Exiting."
        return msg

    if not kubectl_executor.check_kubectl_apply():
        msg = f"Error in kubectl apply check. Exiting."
        return msg
    if kubectl_executor.execute_kubectl_apply().get("code") == 200:
        return kubectl_executor.execute_kubectl_apply()
    else:
        return kubectl_executor.execute_kubectl_apply()

rest = exec_kube_main("./yaml/template_deployment.yaml","./yaml/nginx_new.yaml", "ops")
print(rest)
