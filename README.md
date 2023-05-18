# op-kube-manage-api
```
k8s管理平台 (环境验证:k8s 1.22.17版本)
```

1.1 传统方式部署
```
  1.部署mysql数据库服务;
  2.安装python 3.7 （参考:https://www.python.org/downloads/） 下载并安装
  3.执行pip -r install requirements.txt 
  4.启动服务:
  $ python3.7 main.py
```

1.2 容器化方式部署
```
   1.自行安装docker-compose 基础环境
   2.运行 install_dir/install_shell.sh 部署脚本等待完成部署
   3.部署成功出现如下提示-部署成功.
      op-kube-manage-all 部署完毕,访问机器http://localhost:8888  Success
```
