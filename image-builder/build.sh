set -x
docker build --no-cache -t madwind/flexget $(dirname $0)
