import json
from typing import Dict, Any, Union

from sql_app.ops_environment import insert_db_app_environment, updata_app_environment, delete_db_app_environment, \
    query_environment_app_name

from sql_app.ops_log_db_play import insert_ops_bot_log

from datetime import datetime, timezone, timedelta
from tools.config import setup_logger


class AppEnvironmentService:
    @staticmethod
    def check_environment_app_name(name: str) -> Dict[str, Union[int, str]]:
        """
        # 1.查询app 模板名是否存在
        """
        result = query_environment_app_name(name)
        if result.get("code") == 20000 and result.get("data"):
            return {"code": 20000, "message": f"Template {name} already exists", "status": True,
                    "data": "create environment failure"}
        return {}

    @classmethod
    def add_controller_app_environment(cls, name: str, cluster_id: str, ingress_id: str, service_id: str,
                                       deployment_id: str, app_name: str) -> Dict[str, Any]:
        logger = setup_logger()
        china_timezone = timezone(timedelta(hours=8))
        current_time = datetime.now(china_timezone)
        update_formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        """
        1.添加app 模板
        """
        result = AppEnvironmentService.check_environment_app_name(name)
        if result:
            return result
        created_app_environment = insert_db_app_environment(
            name=name,
            cluster_id=cluster_id,
            ingress_id=ingress_id,
            service_id=service_id,
            deployment_id=deployment_id,
            app_name=app_name,
            uptime_time=str(update_formatted_time)
        )
        if created_app_environment.get("code") == 20000:
            logger.info("Create App Environment Successfully  ", extra={'props': {"app_environment_info": name}})
            print("Successfully inserted data:", name)
        else:
            logger.info("Create App Environment failure ", extra={'props': {"app_environment_info": name}})
            return {"code": 50000, "message": "app env-template  failure", "status": True,
                    "data": " create app env-template failure"}
        return created_app_environment

    @classmethod
    def update_controller_app_environment(cls, ID: int, name: str, cluster_id: str, ingress_id: str, service_id: str,
                                          deployment_id: str, app_name: str, user_request_data: Dict[str, Any]) -> Dict[
        str, Any]:
        """1.更新app 模板 """
        china_timezone = timezone(timedelta(hours=8))
        current_time = datetime.now(china_timezone)
        uptime_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        result = updata_app_environment(ID, name, cluster_id, ingress_id, service_id, deployment_id, app_name,uptime_time)
        if result.get("code") == 20000:
            insert_ops_bot_log("Update App Environment success", json.dumps(user_request_data), "post",
                               json.dumps(result))
            return result
        else:
            return {"code": 50000, "message": "app Environment update failure", "status": True, "data": "failure"}

    @classmethod
    def delete_controller_app_environment(cls, ID: int, name: str, user_request_data: Dict[str, Any]) -> Dict[str, Any]:
        """1.删除app 模板"""
        result = cls.check_template_app_name(name)
        if not result:
            return {"code": 50000, "message": "Environment app delete failure", "status": True, "data": "failure"}

        result = delete_db_app_environment(ID)
        if result.get("code") == 20000:
            insert_ops_bot_log("Delete App Environment success", json.dumps(user_request_data), "post",
                               json.dumps(result))
            return result
        else:
            return {"code": 50000, "message": "Delete Environment failure", "status": True, "data": "failure"}
