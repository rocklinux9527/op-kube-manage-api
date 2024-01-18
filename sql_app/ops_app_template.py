from sql_app.db_play import model_create, model_updateId, model_delete
from sql_app.models import AppTemplate
from sqlalchemy.orm import sessionmaker
from sql_app.database import engine

from typing import Dict, Any, Union, List
from sql_app.ops_log_db_play import insert_ops_bot_log
import json



SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
from fastapi.encoders import jsonable_encoder
from tools.config import appTemplateHeader
# 日志配置
from tools.config import setup_logger
import os

HERE = os.path.abspath(__file__)
HOME_DIR = os.path.split(os.path.split(HERE)[0])[0]
LOG_DIR = os.path.join(HOME_DIR, "logs")


def insert_db_app_template(name, used, uptime_time):
    """
    1.新增入库参数
    :param ns_name:
    :param used:
    :return:
    """
    fildes = {
        "name": "name",
        "used": "used",
        "uptime_time": "uptime_time"
    }

    request_data = {
        "name": name,
        "used": used,
        "uptime_time": uptime_time
    }
    return model_create(AppTemplate, request_data, fildes)


def delete_db_app_template(Id):
    """
    1.删除kube config 配置入库
    :param Id:
    :return:
    """
    return model_delete(AppTemplate, Id)

def delete_app_template(template_id: int, user_request_data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        session = SessionLocal()
        app_template = session.query(AppTemplate).get(template_id)
        if app_template and app_template.environments:
            related_env_data = [
                {
                    "env_id": env.id,
                    "name": env.name,
                    "cluster_id": env.cluster_id,
                    "ingress_id": env.ingress_id,
                    "service_id": env.service_id,
                    "deployment_id": env.deployment_id,
                    "app_id": env.app_id,
                    "uptime_time": env.uptime_time,
                    "create_time": env.create_time
                }
                for env in app_template.environments
            ]
            return {"code": 50000, "message": "存在关联的环境表数据，请先删除相关数据", "status": True,
                    "data": related_env_data}

        result = delete_db_app_template(template_id)
        if result.get("code") == 20000:
            insert_ops_bot_log("Delete App Template success", json.dumps(user_request_data), "post",
                               json.dumps(result))
        return result
    except Exception as e:
        print(f"Error deleting app template: {e}")
        return {"code": 50000, "message": "删除失败", "status": False, "data": None}
    finally:
        # 记得关闭 session
        session.close()


def updata_app_template(Id, name, used, uptime_time):
    fildes = {
        "name": "name",
        "used": "used",
        "uptime_time": "uptime_time"
    }

    request_data = {
        "name": name,
        "used": used,
        "uptime_time": uptime_time,
    }
    return model_updateId(AppTemplate, Id, request_data, fildes)


def query_app_template(page: int = 1, page_size: int = 10):
    """
    1.查询查询配置信息
    """
    session = SessionLocal()
    query = session.query(AppTemplate)
    try:
        data = query.limit(page_size).offset((page - 1) * page_size).all()
        total = query.count()
        return {"code": 20000, "total": total, "data": jsonable_encoder(data), "messages": "query success",
                "status": True,
                "columns": appTemplateHeader}
    except Exception as e:
        logger = setup_logger()
        logger.info("query app template  error  ", extra={'props': {"message": str(e)}})
        return {"code": 50000, "total": 0, "data": "query data failure", "messages": str(e), "status": True,
                "columns": appTemplateHeader}
    finally:
        session.commit()
        session.close()


def updata_app_template(Id, name, used, uptime_time):
    fildes = {
        "name": "name",
        "used": "used",
        "uptime_time": "uptime_time"
    }

    request_data = {
        "name": name,
        "used": used,
        "uptime_time": uptime_time,
    }
    return model_updateId(AppTemplate, Id, request_data, fildes)


def query_app_template_id_for_name(Id):
    """
    查询指定ID的AppTemplate数据
    :param id: AppTemplate的ID
    :return: JSON格式的响应
    """
    session = SessionLocal()
    data = session.query(AppTemplate)
    data = data.filter_by(id=Id)
    if len([i.to_dict for i in data]) >= 1:
        try:
            return {"code": 20000, "total": len([i.to_dict for i in data]),
                    "data": jsonable_encoder(data.all()),
                    "messages": "query data  success", "status": True, "columns": appTemplateHeader}
        except Exception as e:
            print(e)
            session.commit()
            session.close()
            return {"code": 50000, "total": 0, "data": "", "messages": "query fail", "status": True,
                    "columns": appTemplateHeader}
        finally:
            session.close()
    else:
        return {"code": 20000, "total": 0, "data": "template name not is data null",
                "messages": "query data fail ", "status": True, "columns": appTemplateHeader}


def queryTemplateType(q_type, page, page_size):
    session = SessionLocal()
    data = session.query(AppTemplate)
    try:
        data = data.filter_by(t_type=q_type)
        queryData = data.limit(page_size).offset((page - 1) * page_size).all()
        return {"code": 20000, "total": len([i.to_dict for i in data]), "data": jsonable_encoder(queryData),
                "messages": "query data success", "status": True, "columns": appTemplateHeader}
    except Exception as e:
        print(e)
        session.commit()
        session.close()
        return {"code": 50000, "total": 0, "data": "", "messages": "query fail", "status": True,
                "columns": appTemplateHeader}


def query_Template_app_name(name):
    session = SessionLocal()
    data = session.query(AppTemplate)
    if name:
        data = data.filter_by(name=name)
    try:
        return {"code": 20000, "total": len([i.to_dict for i in data]), "data": jsonable_encoder(data.all()),
                "messages": "query data success", "status": True, "columns": appTemplateHeader}
    except Exception as e:
        print(e)
        session.commit()
        session.close()
        return {"code": 50000, "total": 0, "data": "", "messages": "query fail", "status": True,
                "columns": appTemplateHeader}
