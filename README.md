# Baroucoin
Une implémentation d'une chaine de blocs visant à comparer preuve de travail et preuve de participation.

# TODO
### Communication entre les full nodes
- [ ] Récupération des informations avec l'API du serveur
- [ ] Connection TCP entre les noeuds
- [ ] Sérialisation des messages en JSON
### Échanges d'informations entres les full nodes
- [ ] État de la blockchain
- [ ] Nouveau bloc trouvé
- [ ] Nouvelles transactions
- [ ] Difficulté du bloc courant
### 'ProofOfWork'
- [x] Implémentation du minage des blocs
- [x] Vérification du bloc miné
- [ ] Redéfinir la structure d'une transaction : hash, frais
- [X] Vérification des transactions
- [ ] Gestion de la difficulté
- [ ] Calcul de la récompense de bloc
### Amélioration du code
- [ ] Remplacer le booléen 'consensusAlgorithm' pour être plus explicite (énumération ?)
- [ ] Documentation des classes
- [ ] Documentation des fonctions

# Lancement du serveur
Pour initialiser le serveur (jouant un rôle de DNS central pour simplifier la découvertes des noeuds du réseau), nous utilisons Docker.

En premier lieu, construire l'image :
```
cd /server
```
```
docker build -t barouchain_server .
```
Ensuite, lancer le conteneur avec l'image correspondante :
```
docker run -v $(pwd):/server -p 80:80 barouchain_server
```

# Participants
Ce projet est réalisé par :
- [Alexandre Ondet](https://github.com/AlexandreOndet)
- [Etienne Donneger](https://github.com/Krow10)
- [Maxime Durand](https://github.com/Maxim-Durand)