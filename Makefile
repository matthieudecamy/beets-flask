build:
	sudo docker build -f docker/Dockerfile -t shlagi-tagger:latest .

update_config:
	cp -r config/beets/ /volume1/docker/Music/beets-flask/config/beets
