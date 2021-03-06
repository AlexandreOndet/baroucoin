# Baroucoin
Une implémentation d'une chaine de blocs visant à comparer preuve de travail et preuve de participation.

# TODO
### Communication entre les full nodes
- [x] Connexions TCP entre les noeuds
- [x] Sérialisation des messages en JSON
- [x] Récupération des informations avec l'API du serveur
### Échanges d'informations entres les full nodes
- [ ] État de la blockchain
- [x] Nouveau bloc trouvé
- [ ] Nouvelles transactions
- [ ] Difficulté du bloc courant
### 'ProofOfWork'
- [x] Implémentation du minage des blocs
- [x] Vérification du bloc miné
- [X] Vérification des transactions
- [x] Calcul de la récompense de bloc
- [ ] Actualisation autonome de la difficulté par les pairs
### Amélioration du code
- [ ] Remplacer le booléen 'consensusAlgorithm' pour être plus explicite (énumération ?)
- [ ] Documentation des tests
- [ ] Documentation des classes
- [ ] Documentation des fonctions

# Lancement de la simulation
Via le script `run.bat` ou `python -m app.main` depuis la racine. 

Les tests peuvent être lancés via `python -m unittest test.test_xxx`. L'option `-b` peut être utilisée pour supprimer les messages vers la console lors des tests.

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
