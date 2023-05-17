import os

HERE = os.path.abspath(__file__)
HOME_DIR = os.path.split(os.path.split(HERE)[0])[0]
conf_path = os.path.join(HOME_DIR, "conf")
os.sys.path.append(conf_path)


class templeContent():
    def __init__(self, language, content):
        self.language = language
        self.content = content

    def controller(self, name, op="create"):
        opList = ["create", "update", "delete"]
        if not op in opList:
            return {"code": 50000, "messages": f"参数不支持", "status": True,
                    "data": "create File failure"}
        if op == "create":
            result = self.public_write(path=conf_path + "/temple", filename=name)
            return result
        elif op == "update":
            result = self.public_write_force(path=conf_path + "/temple", filename=name)
            return result
        elif op == "delete":
            result = self.public_delete(path=conf_path + "/temple", filename=name)
            return result

    def public_write(self, path, filename):
        file_path = os.path.join(path, filename)
        try:
            if not os.path.exists(file_path):
                with open(file_path, "w") as file:
                    file.write(self.content)
                return {"code": 20000, "messages": f"File {filename} success", "status": True, "data": "create file success"}
            else:
                return {"code": 50000, "messages": f"File {filename} already exists", "status": True,
                        "data": "create File failure"}
        except Exception as e:
            print(e)
            return {"code": 50000, "messages": str(e), "status": True, "data": "create File failure"}

    def public_write_force(self, path, filename):
        file_path = os.path.join(path, filename)
        try:
            if os.path.exists(file_path):
                with open(file_path, "w") as file:
                    file.write(self.content)
                return {"code": 20000, "messages": f"File {filename} success", "status": True, "data": "create file success"}
            else:
                return {"code": 50000, "messages": f"File {filename} already not exists", "status": True,
                        "data": "create File failure"}
        except Exception as e:
            print(e)
            return {"code": 50000, "messages": str(e), "status": True, "data": "create File failure"}

    def public_delete(self, path, filename):
        """
        Args:
            path:
            filename:

        Returns:

        """
        file_path = os.path.join(path, filename)
        print("文件路径",file_path)
        try:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    return {"code": 20000, "messages": f"File {file_path} deleted successfully", "status": True,
                            "data": "create file success"}
                except Exception as e:
                    return {"code": 50000, "messages": "Error deleting the file: {e}".format(e=str(e)), "status": True,
                            "data": "delete  File failure"}
            else:
                return {"code": 50000, "messages": f"File {file_path} Not exists", "status": True,
                        "data": "create File failure"}
        except Exception as e:
            print(e)
            return {"code": 50000, "messages": str(e), "status": True, "data": "delete  File failure"}

def public_download():
    file_path = conf_path + "/temple"
    return file_path


def get_file_extension(language):
    language_extensions = {
        "shell": ".sh",
        "python": ".py",
        "yaml": ".yaml",
        "nginx": ".conf",
        "dockerfile": "_Dockerfile",
        "go": ".go"
    }
    return language_extensions.get(language, "")

