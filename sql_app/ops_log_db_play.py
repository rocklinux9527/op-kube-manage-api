from sql_app.db_play import model_create
from sql_app.models import opsLog
from sqlalchemy.orm import sessionmaker
from sql_app.database import engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def insert_ops_bot_log(descname, request, opsmethod, response):
    """
    1.接口日志入参
    :param descname:
    :param request:
    :param opsmethod:
    :param response:
    :return:
    """
    fildes = {
        "descname": "descname",
        "request": "request",
        "opsmethod": "opsmethod",
        "response": "response"
    }

    request_data = {
        "descname": descname,
        "request": request,
        "opsmethod": opsmethod,
        "response": response
    }
    return model_create(opsLog, request_data, fildes)


def query_operate_ops_log(descname, request):
    """
    查询操作接口日志
    :param descname:
    :param request:
    :return:
    """
    """
    1.跟进不同条件查询日志
    """
    session = SessionLocal()
    data = session.query(opsLog)
    try:
        if descname:
            return {"code": 0, "data": data.filter_by(descname=descname).first()}
        if request:
            return {"code": 0, "data": data.filter_by(request=request).first()}

    except Exception as e:
        print(e)
    session.commit()
    session.close()
    return {"code": 0, "data": [i.to_dict for i in data]}
