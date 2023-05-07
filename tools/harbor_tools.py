import asyncio
import aiohttp

async def get_harbor_tags_async(base_url, project_name, repo_name, username, password, timeout=10):
    if not all([base_url, project_name, repo_name, username, password]):
        raise ValueError("Invalid input parameters")

    url = f"{base_url}/api/v2.0/projects/{project_name}/repositories/{repo_name}/tags"

    async with aiohttp.ClientSession(auth=aiohttp.BasicAuth(username, password), timeout=aiohttp.ClientTimeout(total=timeout)) as session:
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                tags = [tag.get("name") for tag in await response.json()]
                return tags
        except (aiohttp.ClientError, aiohttp.HttpProcessingError) as e:
            print(f"Error during HTTP request: {e}")
            return None

async def main():
    base_url = "https://my-harbor.com"
    project_name = "my-project"
    repo_name = "my-repo"
    username = "my-username"
    password = "my-password"

    tags = await get_harbor_tags_async(base_url, project_name, repo_name, username, password, timeout=5)

    if tags:
        print(tags)
    else:
        print(f"Could not retrieve tags for {base_url}/{project_name}/{repo_name}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
