"""
"""
def opsLogInster( modelname, request, response):
    from models import db
    from models import bmclog
    import json
    import datetime
    Data = request.get_json()
    runTime = datetime.datetime.now()
    sourceIp = request.headers['X-Real-IP']
    opsmethod = request.method
    if  Data and runTime and modelname:
        bcmLogDataInsert = bmclog(descname=modelname,source=sourceIp,request=json.dumps(Data),response=json.dumps(response),opsmethod=opsmethod,run_time=runTime)
        db.session.add(bcmLogDataInsert)
        db.session.commit()
        return True
    else:
        return  False


