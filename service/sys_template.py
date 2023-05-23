import json
import os
from typing import Dict, Any, Union

from fastapi import HTTPException
from sql_app.ops_template import insert_db_template, updata_template, delete_db_template, query_template, query_Template_name
from kube.sys_temple import templeContent, public_download, get_file_extension
from starlette.responses import FileResponse
from sql_app.ops_log_db_play import query_operate_ops_log, insert_ops_bot_log

class TemplateService():
    def check_template_name(self, name: str) -> Dict[str, Union[int, str]]:
        """
         #1.查询模板名是否存在
        """
        result = query_Template_name(name)
        if result.get("code") == 20000 and result.get("data"):
            return {"code": 20000, "message": f"Template {name} already exists", "status": True,
                    "data": "create Template failure"}
        return {}

    def handle_template_file(self, language: str, content: str, name: str, op="create") -> Dict[str, Any]:
        """
        1.查询模板名是否存在
        """
        fileInstance = templeContent(language, content)
        fileInstanceResult = fileInstance.controller(name=name, op=op)
        if fileInstanceResult.get("code") != 20000:
           return {"code": 50000, "message": "create File failure", "status": True, "data": "create File failure"}
        return fileInstanceResult

    def add_controller_template(self, name: str, content: str, language: str, type: str, remark: str) -> Dict[str, Any]:
        """
        1.添加模板
        """
        result = self.check_template_name(name)
        if result:
            return result
        file_extension = get_file_extension(language)
        new_name = name + file_extension
        result = self.handle_template_file(language, content, new_name)
        if result:
            created_template = insert_db_template(
                name=new_name,
                t_type=type,
                content=content,
                language=language,
                remark=remark
            )
            return created_template
        else:
            return {"code": 50000, "message": "create File failure", "status": True, "data": "create File failure"}

    def update_controller_template(self, ID: int, name: str, content: str, language: str, type: str, remark: str, user_request_data: Any) -> Dict[
        str, Any]:
        """1.更新模板 """
        result = self.check_template_name(name)
        if not result:
           return {"code": 50000, "message": "create File failure", "status": True, "data": "create File failure"}
        result_template = self.handle_template_file(language, content, name, op="update")
        if result_template:
            result = updata_template(ID, name, type, content, language, remark)
            if result.get("code") == 20000:
                insert_ops_bot_log("Update Template success", json.dumps(user_request_data), "post", json.dumps(result))
                return result
            else:
                return {"code": 1, "message": "Update Template failure", "status": True, "data": "failure"}
        else:
            return {"code": 50000, "message": "template update failure", "status": True, "data": "failure"}

    def delete_controller_template(self, ID: int, name: str, content: str, language: str, type: str, remark: str, user_request_data: Any) -> Dict[
            str, Any]:
        """1.删除模板"""
        result = self.check_template_name(name)
        if not result:
            return {"code": 50000, "message": "template delete failure", "status": True, "data": "failure"}
        result = self.handle_template_file(language, content, name, op="delete")
        if result:
            result = delete_db_template(ID)
            if result.get("code") == 20000:
                insert_ops_bot_log("Delete Template success", json.dumps(user_request_data), "post", json.dumps(result))
                return result
            else:
                return {"code": 1, "message": "Delete Template failure", "status": True, "data": "failure"}
        else:
            raise HTTPException(status_code=50000, detail="template delete failure")

    def download_file_controller_template(self, name: str, language: str):
        """1.下载模板"""
        base_path = public_download()
        file_path = os.path.join(base_path, f"{name}")
        if os.path.exists(file_path):
            return FileResponse(file_path, filename=name, media_type="application/octet-stream")
        else:
            return {"code": 50000, "message": "文件不存在", "status": True, "data": "ops failure"}
