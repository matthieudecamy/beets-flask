#!/bin/sh
# Copy custom beets plugins into the container's beetsplug directory
cp /config/beets/beetsplug/*.py /usr/local/lib/python3.11/site-packages/beetsplug/
