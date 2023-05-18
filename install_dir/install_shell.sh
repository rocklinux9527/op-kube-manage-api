#!/bin/bash
set -e
deploy_attempts=0
max_deploy_attempts=3
function cleanDeploy() {
    echo -e "\e[32m 开始清理部署环境\e[0m"
    /bin/sh deploy_env_clear.sh
    echo -e "\e[32m 环境清理完毕\e[0m"
}


function add_sys_admin_user()
{
url="http://127.0.0.1:8888"
curl --location --request POST "${url}/user/add" \
--header 'Content-Type: application/json' \
--data-raw '{
"username": "admin",
"password": "11111111"
}'
}

function checkDockerCompose() {
    echo -e "\e[32m 开始检查Docker-compose环境\e[0m"
    checkDockerCompose=$(docker-compose -v | wc -l)
    if [ $checkDockerCompose -eq 1 ]; then
        cd ./docker-compose/
        echo -e "\e[32m 开始容器化kube-manager-api服务部署\e[0m"
        docker-compose up -d
        resultDeploy=$(docker-compose ps | grep -E "op-kube-manage-api|op-kube_manage-mysql-5.7|op-kube-manage-ui" | grep "Up" | wc -l)
        if [ $resultDeploy -eq 3 ]; then
            echo -e "\e[32m 等待20秒MYSQL就绪,服务table初始化\e[0m"
            sleep 20
            docker exec -i op-kube-manage-api python /app/op-kube-manage-api/sql_app/models.py
            docker restart op-kube-manage-api
            sleep 3
            add_sys_admin_user
        else
            echo -e "\e[31m op-kube-manage-api|op-kube_manage-mysql-5.7 |op-kube-manage-ui|容器化服务部署失败啦!\e[0m"
            exit 1
        fi
        echo -e "\e[32m op-kube-manage-all 部署完毕,访问机器http://localhost:8888  Success\e[0m"
        exit 0
    else
        echo -e "\e[31m docker-compose环境没有安装自行,https://docs.docker.com/compose/install/ 获取并安装\e[0m"
        exit 1
    fi
}

function main()
{
    url="http://127.0.0.1:8888/"
    code=$(curl -I -m 30 -o /dev/null -s -w %{http_code}"\n" $url | awk -F '/' '{print $1}')
    if [ $code -eq 200 ]; then
        echo -e "\e[31m 应用已经存在或者端口被占用程序终止,请手动停止服务在执行脚本\e[0m"
        exit 1
    else
        while [ $deploy_attempts -lt $max_deploy_attempts ]; do
            cleanDeploy
            checkDockerCompose
            code=$(curl -I -m 30 -o /dev/null -s -w %{http_code}"\n" $url | awk -F '/' '{print $1}')
            if [ $code -eq 200 ]; then
                break
            fi
            deploy_attempts=$((deploy_attempts+1))
        done
    fi
}

function checkDocker(){
chcek=$(ps -ef |grep docker |wc -l)
if [ $chcek -ne 0 ];then echo -e "\e[32m Dokcer服务存在具备部署服务条件,下一步可选择执行deploy_op-kube-manage-all\e[0m";else  echo -e "\e[31m docker不存在请检查并自行安装docker\e[0m";fi
}

case $1 in
    "all")
        main
        ;;
    "deploy_env_clear")
        cleanDeploy
        ;;
    "deploy_op-kube-manage-all")
        cleanDeploy
        main
        ;;
    "deploy_check")
        checkDocker
     ;;
    *)
        echo -e "\033[32m 部署DNS web服务参数如下 \033[0m"
        echo -e "\033[32m deploy_env_clear \033[0m 部署前环境清理"
        echo -e "\033[32m deploy_check \033[0m 服务部署基础环境检查"
        echo -e "\033[32m deploy_op-kube-manage-all\033[0m op-kube-manage-all 环境部署"
        ;;
esac
