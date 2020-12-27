FROM python:3.9.1-alpine3.12

LABEL maintainer="madwind.cn@gmail.com" \
      org.label-schema.name="flexget"

RUN \
 #sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories && \
 #pip config set global.index-url https://mirrors.aliyun.com/pypi/simple && \
 echo "**** install build packages ****" && \
 apk add --no-cache --virtual=build-dependencies \
	build-base \
  libffi-dev \
  openssl-dev \
 	zlib-dev \
  jpeg-dev \
  freetype-dev \
  libpng-dev  && \
 echo "**** install runtime packages ****" && \
 apk add --no-cache \
	shadow \
  chromium \
	ca-certificates \
	tzdata && \
 pip install --no-cache-dir -U pip && \
 pip install --no-cache-dir -U flexget python-telegram-bot==12.8 brotli baidu-aip pillow pandas matplotlib fuzzywuzzy python-Levenshtein pyppeteer pyppeteer_stealth && \
 echo "**** cleanup ****" && \
 apk del --purge \
 build-dependencies && \
 rm -rf \
  /var/cache/apk/* \
  /tmp/* \
	/root/.cache

ADD link_chromium.py .

# add local files
COPY root/ /

RUN \
 echo "**** create abc user and make our folders ****" && \
 python link_chromium.py && \
 rm link_chromium.py && \
 groupmod -g 1000 users && \
 useradd -u 911 -U -m -d /home/flexget -s /bin/sh flexget && \
 usermod -G users flexget && \
 chown -R flexget:flexget /home/flexget && \
 chmod +x /usr/bin/entrypoint.sh && \

# add default volumes
VOLUME /config /downloads
WORKDIR /config

# expose port for flexget webui
EXPOSE 3539 3539/tcp

ENTRYPOINT ["sh","-c","/usr/bin/entrypoint.sh"]
