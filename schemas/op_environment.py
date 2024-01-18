from pydantic import BaseModel

class AddEnvironmentManager(BaseModel):
    name: str
    cluster_id: str
    ingress_id: str
    service_id: str
    deployment_id: str
    app_id: str

class UpdateEnvironmentManager(BaseModel):
    """用户模板更新模型"""
    id: int
    name: str
    cluster_id: str
    ingress_id: str
    service_id: str
    deployment_id: str
    app_id: str

class DeleteAppEnvironmentManager(BaseModel):
    """用户模板删除模型"""
    id: str
    name: str
