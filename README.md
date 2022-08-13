# Baroucoin
Une implémentation d'une chaine de blocs visant à comparer preuve de travail et preuve de participation.

# TODO
### Communication entre les full nodes
- [x] Connexions TCP entre les noeuds
- [x] Sérialisation des messages en JSON
- [x] Récupération des informations avec l'API du serveur
### Échanges d'informations entres les full nodes
- [x] État de la blockchain
- [x] Nouveau bloc trouvé
### 'ProofOfWork'
- [x] Implémentation du minage des blocs
- [x] Vérification du bloc miné
- [X] Vérification des transactions
- [x] Calcul de la récompense de bloc
- [x] Actualisation dynamique de la difficulté par les pairs
### Amélioration du code
- [ ] Remplacer le booléen 'consensusAlgorithm' pour être plus explicite (énumération ?)
- [ ] Documentation des tests
- [ ] Documentation des classes
- [ ] Documentation des fonctions

# Lancement de la simulation et visualisation des graphes
Prérequis: altair, pandas, streamlit

Démarrer le serveur web Streamlit via `python -m streamlit run app\main.py`. Le navigateur s'ouvrira automatiquement ou naviguer à l'adresse `http://localhost:8501/` puis cliquer sur le bouton pour lancer la simulation !
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
