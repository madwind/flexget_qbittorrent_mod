FROM python:3.8.6-alpine3.12

LABEL maintainer="madwind.cn@gmail.com" \ 
        org.label-schema.name="flexget"

# copy local files
COPY root/ /

# RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories && \
RUN apk add --no-cache ca-certificates nodejs build-base libffi-dev openssl-dev unzip bash tzdata zlib-dev jpeg-dev freetype-dev libpng-dev && \
    pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -U flexget==3.1.72 python-telegram-bot==12.8 brotli baidu-aip pillow pandas matplotlib fuzzywuzzy python-Levenshtein pyppeteer pyppeteer_stealth && \
    python -c 'from pyppeteer import command;command.install()' && \
	cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
  	echo "Asia/Shanghai" >  /etc/timezone && \
    chmod +x /usr/bin/entrypoint.sh && \
    rm -rf /var/cache/apk/* \
           /tmp/* \
	       /root/.cache

# add default volumes
VOLUME /config /downloads
WORKDIR /config

# expose port for flexget webui
EXPOSE 3539 3539/tcp

ENTRYPOINT ["sh","-c","/usr/bin/entrypoint.sh"]
