# Baroucoin
Une implémentation d'une chaine de blocs visant à comparer preuve de travail et preuve de participation.


# Server side
To build the server (sort of central DNS to simplify the node addition process) we use Docker.
First build the image:
```
cd /server
```
```
docker build -t barouchain_server .
```
Then launch the container with the corresponding image
```
docker run -v $(pwd):/server -p 80:80 barouchain_server
```

# Participants
Ce projet est réalisé par :
- [Alexandre Ondet](https://github.com/AlexandreOndet)
- [Etienne Donneger](https://github.com/Krow10)
- [Maxime Durand](https://github.com/Maxim-Durand)