#! /bin/sh
#
# entrypoint.sh

# make folders
mkdir -p /home/docker

# remove config-lock
[[ -f /config/.config-lock ]] && \
  { echo "Removing lockfile"; rm -f /config/.config-lock; }

# copy config.yml
[[ -f /config/config.yml ]] && \
  { echo "Using existing config.yml"; } || \
	{ echo "New config.yml from template"; cp /defaults/config.example.yml /config/config.yml; }

# set FG_WEBUI_PASSWD
if [[ ! -z "${FG_WEBUI_PASSWD}" ]]; then
  echo "Setting flexget web password to '${FG_WEBUI_PASSWD}'"
  flexget -c /config/config.yml web passwd "${FG_WEBUI_PASSWD}" | grep 'Updated password' >/dev/null 2>&1 && \
    echo "Updated password" || \
    echo "Oops, something went wrong"
fi

echo docker:x:${PUID:-0}:${PGID:-0}:docker:/home/docker:/bin/ash >> /etc/passwd
echo docker:x:${PGID:-0}: >> /etc/group

# permissions
chown -R docker:docker /config
chown docker:docker /downloads
chown docker:docker /home/docker

chmod 775 \
	/config \
	/downloads \
  /home/docker

su docker -c "flexget -c /config/config.yml -L ${FG_LOG_LEVEL:-info} daemon start --autoreload-config"
