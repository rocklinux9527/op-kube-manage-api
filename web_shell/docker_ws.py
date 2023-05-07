import docker
from fastapi import FastAPI, WebSocket, Depends
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
app = FastAPI()
websockets = []
@app.on_event("startup")
async def startup_event():
    global client
    client = docker.from_env()

@app.on_event("shutdown")
async def shutdown_event():
    client.close()

def get_docker_client():
    return docker.from_env()

class DockerRequest(BaseModel):
    method: str
    path: str
    data: str = ""

@app.post("/docker")
async def docker_api(request: DockerRequest,
                     client: docker.DockerClient = Depends(get_docker_client)):
    if not hasattr(client.api, request.method.lower()):
        raise HTTPException(status_code=400, detail="Invalid method.")
    method_func = getattr(client.api, request.method.lower())
    try:
        data = method_func(request.path, data=request.data)
    except docker.errors.APIError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return PlainTextResponse(data)
