FROM python:3-alpine

LABEL org.label-schema.name="flexget"

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories && \
    apk add --no-cache ca-certificates nodejs build-base libffi-dev openssl-dev unzip bash tzdata zlib-dev jpeg-dev && \
    pip install -i https://mirrors.aliyun.com/pypi/simple/ -U pip && \
    pip install -i https://mirrors.aliyun.com/pypi/simple flexget python-telegram-bot brotli selenium baidu-aip pillow && \ 
	cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
  	echo "Asia/Shanghai" >  /etc/timezone && \
    rm -rf /var/cache/apk/*

VOLUME /root/.flexget/config /downloads
WORKDIR /root/.flexget/config

COPY rootfs /

ENTRYPOINT ["/usr/bin/entrypoint.sh"]
