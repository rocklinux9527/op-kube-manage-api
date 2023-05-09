from sqlalchemy.orm import sessionmaker, query
from sql_app.database import engine
from sql_app.models import *

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def model_create(model, request_data, fields):
    """
    1.公共新增方法
    :param model:
    :param request_data:
    :param fields:
    :return:
    """
    session = SessionLocal()

    data = model()
    for field in fields:
        if getattr(data, field) != request_data.get(field, ""):
            setattr(data, field, request_data.get(field, ""))
    session.add_all([
        data
    ])
    session.commit()
    session.close()
    return {"code": 20000, "messages": "create success", "status": True, "data": "success"}


def model_update(model, instanceid, request_data, fields):
    """
    1.公共修改 需要传Id
    :param model:
    :param instanceid:
    :param request_data:
    :param fields:
    :return:
    """
    session = SessionLocal()
    data = session.query(model).filter_by(instanceid=instanceid).first()
    for field in fields:
        if getattr(data, field) != request_data.get(field):
            setattr(data, field, request_data.get(field))

    session.commit()
    session.close(
    )
    return {"code": 20000, "messages": "update success", "status": True, "data": "success"}


def model_updateId(model, id, request_data, fields):
    """
     1.公共修改 需要传Id
    :param model:
    :param id:
    :param request_data:
    :param fields:
    :return:
    """
    session = SessionLocal()
    data = session.query(model).filter_by(id=id).first()

    for field in fields:
        if getattr(data, field) != request_data.get(field):
            setattr(data, field, request_data.get(field))
    session.commit()
    session.close()
    return {"code": 20000, "messages": "update success", "status": True, "data": "success"}


def model_delete(model, id):
    """
    1.公共删除
    :param model:
    :param id:
    :return:
    """
    session = SessionLocal()
    if id:
        data = session.query(model).filter_by(id=id).delete()
        session.commit()
        session.close()
        return {"code": 20000, "messages": "delete success", "status": True, "data": "success"}

    else:
        return {"code": 50000, "messages": "id is none failure", "status": False, "data": "failure"}
