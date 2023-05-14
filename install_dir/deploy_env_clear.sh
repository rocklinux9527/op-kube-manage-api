#!/bin/bash
docker rm  op-kube-manage-ui -f
docker rm  op-kube-manage-api -f
docker rm  op-kube_manage-mysql-5.7 -f
rm -rf install_dir/docker-compose/mysql/datadir/
