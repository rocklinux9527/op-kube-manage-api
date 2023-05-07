import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from kubernetes import client, config
import websocket
import ssl
import json

app = FastAPI()
# 加载kubeconfig
config.load_kube_config()

# 创建Kubernetes客户端
api = client.CoreV1Api()

# 建立WebSocket连接
async def pod_websocket(websocket: WebSocket, namespace: str, pod_name: str, command: str):
    # 搜索Pod
    pod = api.read_namespaced_pod(name=pod_name, namespace=namespace)

    # 获取Pod的IP地址
    pod_ip = pod.status.pod_ip

    # WebSocket连接
    command = ['/bin/sh', '-c', command]
    ws_url = "wss://" + pod_ip + ":443/api/v1/namespaces/" + namespace + "/pods/" + pod_name + "/exec?command=" + "+".join(command) + "&container=" + pod.spec.containers[0].name + "&stderr=true&stdin=true&stdout=true&tty=true"

    def on_message(ws, message):
        asyncio.run(websocket.send_json({"msg": message}))

    def on_error(ws, error):
        asyncio.run(websocket.send_json({"msg": error}))

    def on_close(ws):
        asyncio.run(websocket.close())

    def on_open(ws):
        request = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": "session-secret"
            }
        }
        ws.send(json.dumps(request))
        request = {
            "apiVersion": "v1",
            "kind": "Exec",
            "command": command,
            "stdin": True,
            "stdout": True,
            "stderr": True,
            "tty": True
        }
        ws.send(json.dumps(request))

    websocket_data = await websocket.receive_json()
    if "X-Forwarded-Proto" in websocket.headers:
        ws_url = ws_url.replace("https", "wss")
    websocket_data_url = ws_url + "&access_token=" + websocket_data['token']
    ssl_context = ssl.create_default_context(cafile='/var/run/secrets/kubernetes.io/serviceaccount/ca.crt')
    websocket_obj = websocket.WebSocketApp(websocket_data_url, on_message=on_message, on_error=on_error, on_close=on_close, on_open=on_open, sslopt={"cert_reqs": ssl.CERT_NONE})
    websocket_task = asyncio.create_task(websocket_obj.run_forever())
    while True:
        try:
            request = await websocket.receive_json()
            message = request['msg']
            websocket_obj.send(message)
        except:
            websocket_task.cancel()
            break


