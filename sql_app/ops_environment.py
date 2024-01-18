from sql_app.db_play import  model_updateId, model_delete
from sql_app.models import Environment, AppTemplate
from sqlalchemy.orm import sessionmaker
from sql_app.database import engine
from sqlalchemy.exc import SQLAlchemyError


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from fastapi.encoders import jsonable_encoder
from tools.config import environmentHeader
# 日志配置
from tools.config import setup_logger
import os

HERE = os.path.abspath(__file__)
HOME_DIR = os.path.split(os.path.split(HERE)[0])[0]
LOG_DIR = os.path.join(HOME_DIR, "logs")


def model_get_by_id(model, id):
    """
    根据ID获取模型记录
    """
    session = SessionLocal()
    result = session.query(model).get(id)
    session.close()
    return result

def insert_db_app_environment( name, cluster_id, ingress_id, service_id, deployment_id, app_name, uptime_time):
    """
    1.新增入库参数
    :param ns_name:
    :param used:
    :return:
    """
    session = SessionLocal()
    data = session.query(AppTemplate)
    app_temple_name = data.filter_by(name=app_name).first()
    print(app_temple_name)
    if not app_temple_name:
        return {"code": 50000, "total": 0, "data": "query app_temple_name fail ", "messages": "The template does not exist and cannot be add", "status": True}
    new_environment = Environment(
        name=name,
        cluster_id=cluster_id,
        ingress_id=ingress_id,
        service_id=service_id,
        deployment_id=deployment_id,
        app=app_temple_name,
        uptime_time=uptime_time
    )
    # 检查是否已经附加到当前会话
    if new_environment not in session.identity_map:
        session.add(new_environment)
        app_temple_name.environments.append(new_environment)
        session.commit()
        return {"code": 20000, "message": "Environment success ", "status": True}
    else:
        return {"code": 20000, "message": "Environment already attached", "status": True,
                "data": "Environment already attached"}

def delete_db_app_environment(Id):
    """
    1.删除kube config 配置入库
    :param Id:
    :return:
    """
    return model_delete(Environment, Id)


def updata_app_environment(Id, name, cluster_id, ingress_id, service_id, deployment_id, app_temple_name, uptime_time):
    """
    1.获取Environment实例
    2.更新Environment实例的字段
    3.如果需要更新关联的AppTemplate，可以使用关系属性.
    4.发生异常时回滚事务, 无论成功还是失败，都关闭会话.
    5.如果当前字段是 "app" 将整数转换为相应的 AppTemplate 对象
    6.其他字段直接设置
    :param Id:
    :param name:
    :param cluster_id:
    :param ingress_id:
    :param service_id:
    :param deployment_id:
    :param app_temple_name:
    :param uptime_time:
    :return:
    """
    session = SessionLocal()
    data = session.query(AppTemplate)
    app_temple_id = data.filter_by(name=app_temple_name).first()

    request_data = {
        "name": name,
        "cluster_id": cluster_id,
        "ingress_id": ingress_id,
        "service_id": service_id,
        "deployment_id": deployment_id,
        "app": app_temple_id.id,
        "uptime_time": str(uptime_time)
    }
    print("env获取数据结构",request_data)
    try:
        environment = model_get_by_id(Environment, Id)
        for field, value in request_data.items():
            if field == "app":
                app_temple_id = session.query(AppTemplate).get(value)
                setattr(environment, field, app_temple_id)
            else:
                setattr(environment, field, value)
        app_template_id = environment.app_id
        app_template = session.query(AppTemplate).get(app_template_id)
        app_template.name = app_temple_name
        session.commit()
        return {"code": 20000, "message": "Update successful", "status": True, "data": "Update successful"}
    except SQLAlchemyError as e:
        print(f"Error during update: {e}")
        session.rollback()
        return {"code": 50000, "message": f"Update failed: {str(e)}", "status": False, "data": "Update failed"}
    finally:
        session.close()


# def updata_app_environment(Id, name, cluster_id, ingress_id, service_id, deployment_id, app_temple_name, uptime_time):
#
#     fildes = {
#        "name": "name",
#         "cluster_id": "cluster_id",
#         "ingress_id": "ingress_id",
#         "service_id": "service_id",
#         "deployment_id": "deployment_id",
#         "app": "app",
#         "uptime_time": "uptime_time"
#     }
#
#     request_data = {
#         "name": name,
#         "cluster_id": cluster_id,
#         "ingress_id": ingress_id,
#         "service_id": service_id,
#         "deployment_id": deployment_id,
#         "app": app_temple_name,
#         "uptime_time": uptime_time
#     }
#     return model_updateId(Environment, Id, request_data, fildes)
#

def query_app_environment(page: int = 1, page_size: int = 10):
    """
    1.查询查询配置信息
    """
    session = SessionLocal()
    query = session.query(Environment)
    try:
        data = query.limit(page_size).offset((page - 1) * page_size).all()
        total = query.count()
        return {"code": 20000, "total": total, "data": jsonable_encoder(data), "messages": "query success",
                "status": True,
                "columns": environmentHeader}

    except Exception as e:
        logger = setup_logger()
        logger.info("query app template  error  ", extra={'props': {"message": str(e)}})
        return {"code": 50000, "total": 0, "data": "query data failure", "messages": str(e), "status": True,
                "columns": environmentHeader}
    finally:
        session.commit()
        session.close()


def query_environment_app_name(name):
    session = SessionLocal()
    data = session.query(Environment)
    if name:
        data = data.filter_by(name=name)
    try:
        return {"code": 20000, "total": len([i.to_dict for i in data]), "data": jsonable_encoder(data.all()),
                "messages": "query data success", "status": True, "columns": environmentHeader}
    except Exception as e:
        print(e)
        session.commit()
        session.close()
        return {"code": 50000, "total": 0, "data": "", "messages": "query fail", "status": True,
                "columns": environmentHeader}
