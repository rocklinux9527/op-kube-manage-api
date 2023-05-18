import yaml
import os
HERE = os.path.abspath(__file__)
HOME_DIR = os.path.split(os.path.split(HERE)[0])[0]
LOG_DIR = os.path.join(HOME_DIR, "tools")

def YamlHandler():
    """
    1.文件为空检查
    2.读配置文件
    3.校验文件后缀名 yaml yml格式结尾
    4.校验配置项格式
    5.参数配置项检查
    6.配置项目不为空检查
    """
    # 检查文件是否为空
    yamlConfigFileName = "harbor_config.yaml"
    yaml_option = "harbor"
    if os.path.getsize(LOG_DIR + '/' + yamlConfigFileName) == 0:
        print("Configuration file is empty.")
        exit(1)

    # 读取配置文件
    with open(LOG_DIR + '/' + yamlConfigFileName, 'r') as f:
        try:
            config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"Error loading YAML file: {e}")
            exit(1)

    # 校验文件后缀名
    if not (yamlConfigFileName.endswith('.yaml') or yamlConfigFileName.endswith('.yml')):
        print("Invalid file extension. File must have .yaml or .yml extension.")
        exit(1)

    # 校验配置项格式
    if yaml_option not in config:
        print(f'Missing f{yaml_option} section in YAML file')
        exit(1)

    option_config = config[yaml_option]
    if not isinstance(option_config, dict):
        print(f'{yaml_option} section must be a dictionary')
        exit(1)

    if 'base_url' not in option_config or 'username' not in option_config or 'password' not in option_config:
        print('Missing required configuration items in {yaml_option} section')
        exit(1)

    access_url = option_config.get('base_url', 'default_url')
    access_username = option_config.get('username', 'default_secret')
    access_password = option_config.get('password', "default_secret")
    if "default_url" in [access_url, access_username, access_password]:
        print("Config is incomplete. Please check your configuration file.")
        exit(1)
    # 返回配置项字典
    return {"access_url": access_url, "access_username": access_username, "access_password": access_password}


if __name__ == "__main__":
    conf = YamlHandler()
    print(conf)

