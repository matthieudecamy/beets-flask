build:
	sudo docker build -f docker/Dockerfile -t shlagi-tagger:latest .

update_config:
	cp -r config/beets/. /volume1/docker/Music/beets-flask/config/beets/
	cp -r config/beets-flask/. /volume1/docker/Music/beets-flask/config/beets-flask/
	cp config/startup.sh /volume1/docker/Music/beets-flask/config/startup.sh
	chmod +x /volume1/docker/Music/beets-flask/config/startup.sh
