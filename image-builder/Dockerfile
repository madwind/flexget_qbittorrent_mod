FROM python:3-alpine

LABEL maintainer="madwind.cn@gmail.com" \ 
        org.label-schema.name="flexget"

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories && \
    apk add --no-cache ca-certificates nodejs build-base libffi-dev openssl-dev unzip bash tzdata zlib-dev jpeg-dev && \
    pip install -i https://mirrors.aliyun.com/pypi/simple/ -U pip && \
    pip install -i https://mirrors.aliyun.com/pypi/simple flexget python-telegram-bot brotli baidu-aip pillow && \ 
	  cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
  	echo "Asia/Shanghai" >  /etc/timezone && \
    rm -rf /var/cache/apk/*

# copy local files
COPY root/ /

# add default volumes
VOLUME /config /downloas
WORKDIR /config

# expose port for flexget webui
EXPOSE 3539 3539/tcp

ENTRYPOINT ["sh","-c","/usr/bin/entrypoint.sh"]
