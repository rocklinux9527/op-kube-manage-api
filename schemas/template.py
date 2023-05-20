from pydantic import BaseModel

class templateManager(BaseModel):
    """用户模板新增模型"""
    name: str
    content: str
    t_type: str
    language: str
    remark: str


class UpdateTemplateManager(BaseModel):
    """用户模板更新模型"""
    id: int
    name: str
    content: str
    t_type: int
    language: str
    remark: str


class deleteTemplateManager(BaseModel):
    """用户模板删除模型"""
    id: str
    name: str
