#!/bin/sh
set -e

CONFIG_DEST=/volume1/docker/Music/beets-flask/config

case "$1" in
    build)
        sudo docker build -f docker/Dockerfile -t shlagi-tagger:latest .
        ;;
    update_config)
        cp -r config/beets/. "$CONFIG_DEST/beets/"
        cp -r config/beets-flask/. "$CONFIG_DEST/beets-flask/"
        cp config/startup.sh "$CONFIG_DEST/startup.sh"
        chmod +x "$CONFIG_DEST/startup.sh"
        ;;
    *)
        echo "Usage: $0 {build|update_config}"
        exit 1
        ;;
esac
