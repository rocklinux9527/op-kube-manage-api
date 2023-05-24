from fastapi import FastAPI, HTTPException
from kubernetes import client, config

import asyncio
import aiohttp
from kubernetes import client, config

async def check_k8s_cluster(client_config_file):
    """
    1.加载 Kubernetes 配置文件（如果在集群内部运行则不需要此步骤
    2.创建 Kubernetes API 客户端
    3.调用 Kubernetes API 获取集群信息
    4.run_in_executor() 方法来在事件循环中执行阻塞的同步函数 (进行超时检查)
    Returns:
    """
    try:
        config.load_kube_config(config_file=client_config_file)
        api_instance = client.CoreV1Api()
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(loop.run_in_executor(None, api_instance.list_node), timeout=2)
        if response.items:
            return {"code": 20000, "message": "Kubernetes 集群连接正常", "status": True}
        else:
            detail = "Kubernetes 集群连接异常"
            return {"code": 50000, "message": detail, "status": False}
    except asyncio.TimeoutError:
        return {"code": 50000, "message": "Kubernetes 连接超时", "status": False}
    except Exception as e:
        detail = f'无法连接到 Kubernetes 集群'
        return {"code": 50000, "message": detail, "status": False}

async def check_k8s_cluster_v2(client_config_file):
    """
     未添加超时版本
    1.加载 Kubernetes 配置文件（如果在集群内部运行则不需要此步骤
    2.创建 Kubernetes API 客户端
    3.调用 Kubernetes API 获取集群信息
    Returns:

    """
    try:
        config.load_kube_config(config_file=client_config_file)
        api_instance = client.CoreV1Api()
        response = api_instance.list_node()
    except Exception as e:
        detail = "无法连接到 Kubernetes 集群"
        return {"code": 50000, "message": detail, "status": True}
    if response.items:
        return {"code": 20000, "message": "Kubernetes 集群连接正常", "status": True}
    else:
        detail = "Kubernetes 集群连接异常"
        return {"code": 50000, "message": detail, "status": False}
