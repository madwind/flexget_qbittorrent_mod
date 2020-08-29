#! /bin/sh
#
# entrypoint.sh

cd ~/.flexget/config

if [ ! -f ~/.flexget/config/config.yml ]; then
  echo "$(date '+%Y-%m-%d %H:%m') INIT     New config.yml from template"
  cp /etc/flexget/config.example.yml ~/.flexget/config/config.yml
fi

if [ ! -z "${FG_WEBUI_PASSWD}" ]; then
  echo "$(date '+%Y-%m-%d %H:%m') INIT     Using userdefined FG_WEBUI_PASSWD: ${FG_WEBUI_PASSWD}"
  flexget web passwd "${FG_WEBUI_PASSWD}"
fi

echo flexget:x:${PUID:-0}:${GUID:-0}:flexget:/home:/bin/ash >> /etc/passwd

su flexget

flexget -L ${FG_LOG_LEVEL:-info} daemon start --autoreload-config