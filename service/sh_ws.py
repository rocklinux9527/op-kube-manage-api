# WebSocket处理函数
import asyncio
import subprocess
from fastapi import WebSocket

async def websocket_handler(websocket: WebSocket):
    # 运行Shell脚本并将输出发送到WebSocket连接
    process = await asyncio.create_subprocess_shell(
        '/Users/lijianxing/lijx-devops/python/fastapi/op-kube-manage-api/test.sh',
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

    while True:
        output = await process.stdout.readline()
        if output:
            # 将输出发送到WebSocket连接
            await websocket.send_text(output.decode())

        if process.stdout.at_eof():
            # 进程执行完毕，关闭WebSocket连接
            await websocket.close()
            break

terminal_html = """
<!DOCTYPE html>
<html>
<head>
  <title>Shell Output</title>
</head>
<body>
  <pre id="output"></pre>

  <script>
    var socket = new WebSocket('ws://192.168.0.2:8888/ws');

    socket.onmessage = function(event) {
      var outputElement = document.getElementById('output');
      outputElement.textContent += event.data + '\\n';
    };
  </script>
</body>
</html>
"""
# 测试示例代码
# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     websockets.append(websocket)
#     try:
#         while True:
#             data = await websocket.receive_text()
#             for ws in websockets:
#                 if ws == websocket:
#                     continue
#                 await ws.send_text(data)
#     except:
#         websockets.remove(websocket)


