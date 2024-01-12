from pydantic import BaseModel

# 接受body 类 数据结构
class Item(BaseModel):
    service_id: str
    ingress_id: str
    deployment_id: str
    name: str
    cluster: str
    used: str

class AddAppTemplateManager(BaseModel):
    """用户模板新增模型"""
    test: Item
    pre: Item
    prod: Item

class UpdateAppTemplateManager(BaseModel):
    """用户模板更新模型"""
    id: int
    test: Item
    pre: Item
    prod: Item

class deleteAppTemplateManager(BaseModel):
    """用户模板删除模型"""
    id: str
    name: str
