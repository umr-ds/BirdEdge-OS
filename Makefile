PIMOD = docker-compose run --rm pimod pimod.sh --resolv host

Base-Nano.img:          Base-Nano.Pifile stages/0*.Pifile
	$(PIMOD) Base-Nano.Pifile

BirdEdge-Nano.img:    BirdEdge-Nano.Pifile stages/1*.Pifile
	cp Base-Nano.img BirdEdge-Nano.img
	$(PIMOD) $(basename $@).Pifile

Base-Nano2GB.img:          Base-Nano2GB.Pifile stages/0*.Pifile
	$(PIMOD) Base-Nano2GB.Pifile

BirdEdge-Nano2GB.img:    BirdEdge-Nano2GB.Pifile stages/1*.Pifile
	cp Base-Nano2GB.img BirdEdge-Nano2GB.img
	$(PIMOD) $(basename $@).Pifile
