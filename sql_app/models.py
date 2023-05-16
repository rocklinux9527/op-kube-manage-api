import datetime

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Boolean, Integer, String, Text, ForeignKey, DateTime, UniqueConstraint, Index, func

from sqlalchemy_utc import utcnow
import sys, os
import imp

imp.reload(sys)

HERE = os.path.abspath(__file__)
HOME_DIR = os.path.split(os.path.split(HERE)[0])[0]
os.sys.path.append(HOME_DIR)
# script_path = os.path.join(HOME_DIR, "tools")


from sql_app.database import Base

STRFTIME_FORMAT = "%Y-%m-%d %H:%M:%S"
STRFDATE_FORMAT = "%Y-%m-%d"


class DeployK8sData(Base):
    __tablename__ = "op_kube_manage_deploy_data"
    id = Column(Integer, primary_key=True)
    app_name = Column(String(64), comment="应用名称")
    env = Column(String(16), comment="环境")
    cluster = Column(String(64), comment="集群")
    namespace = Column(String(64), comment="命名空间")
    resources = Column(String(32), comment="资源规格")
    replicas = Column(String(4), comment="副本数量")
    image = Column(String(128), comment="镜像版本tag")
    affinity = Column(Text, nullable=True, comment="亲核性")
    ant_affinity = Column(Text, nullable=True, comment="反亲核性")
    deploy_env = Column(Text, nullable=True, comment="环境变量")
    ports = Column(Text, nullable=True, comment="应用端口")
    volumeMounts = Column(Text, nullable=True, comment="挂载卷")
    volume = Column(Text, nullable=True, comment="卷名称")
    image_pull_secrets = Column(Text, nullable=True, comment="镜像拉取secrets")
    health_liven_ess = Column(Text, nullable=True, comment="探活接口")
    health_readiness = Column(Text, nullable=True, comment="流量控制接口")
    deploy_id = Column(String(24), comment="发布记录Id")
    deploy_time = Column(DateTime, server_default=func.now(), comment="创建时间")

    @property
    def to_dict(self):
        return {"id": self.id,
                "app_name": self.app_name,
                "env": self.env,
                "cluster": self.cluster,
                "namespace": self.namespace,
                "resources": self.resources,
                "replicas": self.replicas,
                "image": self.image,
                "affinity": self.affinity,
                "ant_affinity": self.ant_affinity,
                "deploy_env": self.deploy_env,
                "ports": self.ports,
                "volumeMounts": self.volumeMounts,
                "volume": self.volume,
                "image_pull_secrets": self.image_pull_secrets,
                "health_liven_ess": self.health_liven_ess,
                "health_readiness": self.health_readiness,
                "deploy_id": self.deploy_id,
                "deploy_time": self.deploy_time.strftime(STRFTIME_FORMAT)
                }


class ServiceK8sData(Base):
    """
    1.kube svc db column
    """
    __tablename__ = "op_kube_manage_svc_data"
    id = Column(Integer, primary_key=True)
    env = Column(String(32), comment="环境")
    cluster_name = Column(String(64), comment="集群")
    namespace = Column(String(64), comment="命名空间")
    svc_name = Column(String(64), comment="svc 服务名称")
    selector_labels = Column(String(64), comment="selector deploy 标签")
    svc_port = Column(String(12), comment="svc 端口")
    svc_type = Column(String(16), comment="svc 类型")
    target_port = Column(String(12), comment="svc deploy 后端target端口")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")

    @property
    def to_dict(self):
        return {"id": self.id,
                "env": self.env,
                "cluster_name": self.cluster_name,
                "namespace": self.namespace,
                "svc_name": self.svc_name,
                "selector_labels": self.selector_labels,
                "svc_port": self.svc_port,
                "svc_type": self.svc_type,
                "target_port": self.target_port,
                "create_time": self.create_time.strftime(STRFTIME_FORMAT)
                }


class IngressK8sData(Base):
    """
    1.kube ingress db column
    """
    __tablename__ = "op_kube_manage_ingress_data"
    id = Column(Integer, primary_key=True)
    env = Column(String(32), comment="环境")
    cluster_name = Column(String(64), comment="集群")
    namespace = Column(String(64), comment="命名空间")
    ingress_name = Column(String(64), comment="ingress 名称")
    host = Column(String(128), comment="访问域名fqdn")
    svc_name = Column(String(64), comment="svc 类型")
    path = Column(String(64), comment="请求路径")
    path_type = Column(String(64), server_default="Prefix", comment="路径类型")
    ingress_class_name = Column(String(64), server_default="nginx", comment="控制器名称")
    tls = Column(Boolean, server_default="0", comment="是否开启TLS,默认不开启")
    tls_secret = Column(String(128), server_default="", comment="TLS secret名字")
    svc_port = Column(String(8), comment="svc 端口")
    used = Column(Text, nullable=True, comment="ingress用途")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")

    @property
    def to_dict(self):
        return {"id": self.id,
                "env": self.env,
                "cluster_name": self.cluster_name,
                "namespace": self.namespace,
                "ingress_name": self.ingress_name,
                "host": self.host,
                "svc_name": self.svc_name,
                "path": self.path,
                "path_type": self.path_type,
                "ingress_class_name": self.ingress_class_name,
                "tls": self.tls,
                "tls_secret": self.tls_secret,
                "svc_port": self.svc_port,
                "used": self.used,
                "create_time": self.create_time.strftime(STRFTIME_FORMAT)
                }


class KubeK8sConfig(Base):
    __tablename__ = "op_kube_manage_config_data"
    id = Column(Integer, primary_key=True)
    env = Column(String(32), comment="环境")
    cluster_name = Column(String(64), comment="集群")
    server_address = Column(String(64), comment="api-server链接地址")
    ca_data = Column(Text, nullable=True, comment="CA证书")
    client_crt_data = Column(Text, nullable=True, comment="crt证书")
    client_key_data = Column(Text, nullable=True, comment="key密钥")
    client_key_path = Column(Text, nullable=True, comment="证书文件路径")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")

    @property
    def to_dict(self):
        return {"id": self.id,
                "env": self.env,
                "cluster_name": self.cluster_name,
                "server_address": self.server_address,
                "ca_data": self.ca_data,
                "client_crt_data": self.client_crt_data,
                "client_key_data": self.client_key_data,
                "client_key_path": self.client_key_path,
                "create_time": self.create_time.strftime(STRFTIME_FORMAT)
                }


class opsLog(Base):
    __tablename__ = 'op_kube_manage_ops_log'
    id = Column(Integer, primary_key=True)
    descname = Column(String(128), nullable=True)  #########模块名称###########
    source = Column(String(64), nullable=True)  ########ip源地址###########
    request = Column(Text, nullable=True)  #######请求参数##########
    response = Column(Text, nullable=True)  ########返回参数###########
    opsmethod = Column(String(64), nullable=True)  ########返回方法##########
    run_time = Column(DateTime, server_default=func.now(), comment="操作时间")

    @property
    def to_dict(self):
        return {"id": self.id, "descname": self.descname, "source": self.source,
                "request": self.request, "response": self.response, "opsmethod": self.opsmethod, "run_time":
                    self.run_time}

class Users(Base):
    __tablename__ = 'op_kube_manage_users'
    id = Column(Integer, primary_key=True)
    username = Column(String(64))
    password_hash = Column(String(1024), nullable=False)
    create_time = Column(DateTime, server_default=func.now(), comment="创建操作时间")
    @property
    def to_dict(self):
        return {"id": self.id, "username": self.username,
                "password_hash": self.password_hash,
                "create_time": self.create_time}

def init_db():
    from database import engine
    Base.metadata.create_all(engine)


class DeployNsData(Base):
    __tablename__ = "op_kube_manage_ns_data"
    id = Column(Integer, primary_key=True)
    env = Column(String(16), comment="环境")
    cluster_name = Column(String(64), comment="集群")
    ns_name = Column(String(63), comment="ns名称")
    used = Column(Text, nullable=True, comment="用途")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")

    @property
    def to_dict(self):
        return {"id": self.id,  "env": self.env,  "cluster_name": self.cluster_name, "ns_name": self.ns_name, "used": self.used, "create_time": self.create_time}


if __name__ == "__main__":
    print("ok")
    init_db()
