FROM python:3.7.0 As builder
COPY requirements.txt .
RUN  pip3 install --upgrade pip && pip3 install  -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
FROM python:3.7.0-alpine3.7
COPY --from=builder /usr/local/lib/python3.7/site-packages /usr/local/lib/python3.7/site-packages
#Set System TimeZone
# Set 阿里云软件更新源
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories

RUN apk add --no-cache tzdata bash bind-tools
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN mkdir -p /app/op-kube-manage-api && chmod 775 -R /app/

WORKDIR /app/op-kube-manage-api
COPY . .
CMD  python main.py
