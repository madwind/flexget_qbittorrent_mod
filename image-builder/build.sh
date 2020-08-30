set -x
#docker build --no-cache -t ivonwei/flexget $(dirname $0)
docker build -t ivonwei/flexget $(dirname $0)