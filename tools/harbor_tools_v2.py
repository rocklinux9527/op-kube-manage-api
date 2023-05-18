import asyncio
import aiohttp
import base64
from tools.harbor_yaml_load import YamlHandler

async def get_harbor_tags(base_url, project_name, repo_name, headers):
    """
    1. 检查响应状态码是否为200
    2. 使用列表推导式生成镜像标签列表.
        遍历响应中的每个元素,
        确保标签列表存在且为列表类型
        遍历每个元素中的标签列表.
        确保标签为字典类型且具有名称属性
    3. 处理响应状态码不为200的情况
    """
    async with aiohttp.ClientSession() as session:
        url = f"{base_url}/api/v2.0/projects/{project_name}/repositories/{repo_name}/artifacts?page=1&page_size=20"
        async with session.get(url, headers=headers, verify_ssl=False) as response:
            if response.status == 200:
                data = await response.json()
                repoTagsList = [
                    f'{base_url.replace("https://", "")}/{project_name}/{repo_name}:{tag["name"]}'
                    for item in data
                    if isinstance(item.get("tags"), list)
                    for tag in item["tags"]
                    if isinstance(tag, dict) and tag.get("name")
                ]
            else:
                repoTagsList = []
            return repoTagsList

async def harbor_main_aio(project_name, repo_name):
    try:
        if not (project_name and repo_name):
            raise HTTPException(status_code=400, detail="Missing parameter")
        base_url = YamlHandler().get("access_url")
        project_name = project_name
        repo_name = repo_name
        username = YamlHandler().get("access_username")
        password = YamlHandler().get("access_password")
        credentials = f'{username}:{password}'
        base64_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        headers = {'Authorization': f'Basic {base64_credentials}'}

        async with aiohttp.ClientSession() as session:
            tags = await get_harbor_tags(base_url, project_name, repo_name, headers)
            if tags:
                return {"code": 20000, "message": "query images success", "status": True, "data": tags}
            else:
                return {"code": 50000, "messages": f'Could not retrieve tags for {base_url.replace("https://", "")}/{project_name}/{repo_name}', "status": False, "data": "project name or repo_name does not exist!"}
    except Exception as e:
        print(f"Error: {e}")
        return {"code": 50000, "messages": str(e), "status": False, "data": ""}

# if __name__ == "__main__":
#     loop = asyncio.get_event_loop()
#     result = loop.run_until_complete(harbor_main_aio("k8s", "op-kube-manage-ui"))
#     print(result)
