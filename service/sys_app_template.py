import json
from typing import Dict, Any, Union

from sql_app.ops_app_template import insert_db_app_template, updata_app_template, delete_db_app_template, query_app_template, query_Template_app_name
from sql_app.ops_log_db_play import insert_ops_bot_log

from datetime import datetime, timezone, timedelta
from tools.config import setup_logger

class AppTemplateService:
    @staticmethod
    def check_template_app_name(name: str) -> Dict[str, Union[int, str]]:
        """
        # 1.查询app 模板名是否存在
        """
        result = query_Template_app_name(name)
        if result.get("code") == 20000 and result.get("data"):
            return {"code": 20000, "message": f"Template {name} already exists", "status": True,
                    "data": "create Template failure"}
        return {}

    @classmethod
    def save_data_to_database(cls, transformed_data):
        for data in transformed_data:
            print("数据在这里")
            print(data)
            cls.add_controller_app_template(**data)

    @classmethod
    def add_controller_app_template(cls, name: str, used: str) -> Dict[str, Any]:
        logger = setup_logger()
        china_timezone = timezone(timedelta(hours=8))
        current_time = datetime.now(china_timezone)
        update_formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        """
        1.添加app 模板
        """
        result = AppTemplateService.check_template_app_name(name)
        if result:
            return result
        created_app_template = insert_db_app_template(
            name=name,
            used=used,
            uptime_time=str(update_formatted_time)
        )
        if created_app_template.get("code") == 20000:
            logger.info("Create App Template Successfully  ", extra={'props': {"app_template_info": name}})
            print("Successfully inserted data:", name)
        else:
            logger.info("Create App Template failure ", extra={'props': {"app_template_info": name }})
            return {"code": 50000, "message": "app template  failure", "status": True, "data": " create app template failure"}
        return created_app_template
    @classmethod
    def update_controller_app_template(cls, ID: int, name: str, used: str, user_request_data: Dict[str, Any]) -> Dict[str, Any]:
        """1.更新app 模板 """
        china_timezone = timezone(timedelta(hours=8))
        current_time = datetime.now(china_timezone)
        uptime_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        result = updata_app_template(ID, name, used, uptime_time)
        if result.get("code") == 20000:
            insert_ops_bot_log("Update App Template success", json.dumps(user_request_data), "post", json.dumps(result))
            return result
        else:
            return {"code": 50000, "message": "app template update failure", "status": True, "data": "failure"}

    @classmethod
    def delete_controller_app_template(cls, ID: int, name: str, user_request_data: Dict[str, Any]) -> Dict[str, Any]:
        """1.删除app 模板"""
        result = cls.check_template_app_name(name)
        if not result:
            return {"code": 50000, "message": "template app delete failure", "status": True, "data": "failure"}

        result = delete_db_app_template(ID)
        if result.get("code") == 20000:
            insert_ops_bot_log("Delete App Template success", json.dumps(user_request_data), "post", json.dumps(result))
            return result
        else:
            return {"code": 50000, "message": "Delete Template failure", "status": True, "data": "failure"}
