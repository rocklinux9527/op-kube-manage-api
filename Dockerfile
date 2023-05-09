FROM python:3.7.0 As builder
COPY requirements.txt .
RUN  pip install passlib -i https://mirrors.aliyun.com/pypi/simple/ &&  pip install nacos-sdk-python -i https://mirrors.aliyun.com/pypi/simple/ && pip install --upgrade pip  -i https://mirrors.aliyun.com/pypi/simple/ && pip install  -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt
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
