
import requests
sp = requests.get("http://0.0.0.0:8888/v1/kube/config/",timeout=3)
data = dict()
sp.close()
envs = list(set([i.get("env") for i in sp.json().get("data")]))

data["env"] = envs
envList = []
for i in sp.json().get("data"):
    envList.append({i.get("env"): i.get("cluster_name")})
data["cluster"] = envList
print(data)

{'cluster': {'dev': ['c1', 'c2'], 'test': ['c1']}, 'env': ['dev', 'test']}

# data["cluster"] = {"cluster": }

for i in sp.json().get("data"):
    print(i.get("env"), i.get("cluster_name"))
