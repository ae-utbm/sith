Cette page expose la politique du Pôle informatique de l'AE
en ce qui concerne l'usage et l'implémentation de systèmes d'IA
dans le cadre de l'AE et du développement de ses outils.

## Cadre

En accord avec le règlement européen sur 
l'intelligence artificielle du 13 juin 2024,
nous définissons comme IA :

> Un système basé sur une machine qui est 
> conçu pour fonctionner avec différents niveaux d'autonomie 
> et qui peut faire preuve d'adaptabilité après son déploiement, 
> et qui, pour des objectifs explicites ou implicites, déduit,
> à partir des données qu'il reçoit, 
> comment générer des résultats tels que des prédictions, 
> du contenu, des recommandations ou des décisions 
> qui peuvent influencer des environnements physiques ou virtuels.

Cette définition recouvre toutes les IAs génératives, ce qui inclut
ChatGPT, DeepSeek, Claude, Copilot, Mistral, Llama et autres outils similaires.

## Intégration dans le site

L'intégration sur le site AE de systèmes d'IA 
et de toute fonctionnalité basée sur des systèmes d'IA
est strictement prohibée, quel qu'en soit l'objectif.

Toute tâche de modération, de génération
ou de détection de contenu ne doit être accomplie
que par des êtres humains ou par des algorithmes
déterministes, testés et compris.

L'usage des données du site a des fins d'entrainement d'IA,
ainsi que la transmission de ces données à un système d'IA
est strictement interdit.
Tout acte de cette nature sera considéré comme une violation
grave de la politique de gestion des données de l'AE.

!!!question "Pourquoi ?"

    Le pôle informatique ne possède pas à ce jour
    la maitrise technique suffisante pour garantir un traitement
    automatisé des données utile, fiable et respectueux des
    utilisateurs et du RGPD.
    
    Nous n'avons également pas les ressources matérielles
    nécessaires pour faire tourner un modèle local.

## Utilisation dans le développement

!!!abstract
    
    Vous faites ce que vous voulez, à une condition essentielle :
    vous devez savoir ce que vous faites.

Nous n'imposons pas de manière de travailler de votre côté.
Vous pouvez utiliser les outils avec lesquels vous êtes le plus à l'aise, 
sans restriction autre que le respect de la loi et des licences.

Nous conseillons tout de même une approche humaine du développement.
Quand vous vous documentez, préférez la documentation du site, 
celle de Django et l'aide des autres développeurs,
plutôt que de recourir immédiatement à l'IA.
Quand vous codez, pareil, bidouillez un peu avec le code ;
ça ne sera pas forcément facile, mais ça vous apprendra des choses.
Ce ne sont évidemment que des conseils, vous en faites ce que vous voulez.

Cependant, il y a une condition essentielle à respecter :
vous devez être en mesure de pouvoir expliquer ce que vous avez fait.
Les PR de mille lignes où les reviewers sont censés trouver
à votre place ce que le code fait, c'est non.
C'est un énorme manque de respect envers les bénévoles de l'AE.

Bien entendu, il faut nuancer :
vous n'êtes pas non plus obligés de savoir parfaitement ce que vous faites.
Il est normal de ne pas tout saisir du premier coup (voire d'être complètement perdu),
surtout quand on est nouveau sur une base de code.
Les autres développeurs sont là pour accompagner et expliquer.
Nous sommes prêts à prendre tout le temps qu'il faut,
si vous vous engagez également dans une démarche de compréhension.

En bref, nous ne refusons pas les gens qui ne comprennent pas (au contraire),
mais nous ne pouvons pas tolérer celles et ceux qui ne font pas l'effort
de chercher à comprendre.


!!!question "Pourquoi ?"

    Nous ne pouvons pas, ne voulons pas et n'avons pas
    à imposer aux gens les outils avec lesquels ils veulent travailler de leur côté.

    De plus, nous ne sommes pas devins, nous ne savons pas
    comment le monde du développment va bouger dans les prochains années.
    Aussi vaut-il mieux laisser une certaine flexibilité
    pour s'adapter aux méthodes de travail qui pourront apparaitre
    dans les années à venir.

    Cependant, nous devons quand même nous assurer que la base de code du site
    résistera au mieux à l'épreuve du temps, malgré le turnover.
    Le code doit donc rester compréhensible, maintenable, cohérent et explicable.
    Dans l'idéal, il doit toujours y avoir un humain
    en mesure de comprendre et d'expliquer telle ou telle partie du code.

## Petits rappels

Les points suivants ne sont ni des obligations, ni même des conseils,
mais il est tout de même bien de l'avoir en tête :

- Les projets commerciaux d'IA se livrent fréquemment 
  à des violations flagrantes du droit d'auteur 
  et à un mépris complet des petits acteurs du web
  (dont le site AE fait partie) pour entraîner leurs modèles.
- Leurs activités nécessitent une consommation massive d'énergie et de matériel, 
  entrainant conflits d'usage et intensification 
  des dommages sociaux et environnementaux de l'industrie.
- La promotion et l'utilisation des modèles d'IA ont causé un préjudice
  important aux salariés et une aliénation de leur travail.
- Les LLM ont favorisé les activités de spam et d'escroquerie.
- L'IA est devenu un maillon essentiel du fichage des individus,
  du renforcement des biais sociétaux, et de la désinformation de masse.