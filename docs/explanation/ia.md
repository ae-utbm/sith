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
ChatGPT, DeepSeek, Claude, Copilot, Llama et autres outils similaires.

## Utilisation dans le développement

!!!danger
    La soumission de code généré par IA est strictement interdite.

Aucune contribution contenant du code généré par IA n'est acceptée.
Toute PR contenant en proportion significative du code duquel
on peut raisonnablement penser qu'il a été généré par IA 
pourra être refusée sans aucun autre motif.

Bien que nous ne puissions pas l'interdire,
nous déconseillons également fortement l'usage de tout
recours à un système d'IA dans le processus de développement,
quel que soit son usage (debug, recherche d'information ou autres).
Référez-vous en priorité à la documentation du site,
à celle de Django et à l'aide des autres développeurs,
mais par pitié, ne faites jamais appel à l'IA.

## Intégration dans le site

L'intégration sur le site AE de systèmes d'IA 
et de toute fonctionnalité basée sur des systèmes d'IA
est strictement prohibée, quel qu'en soit l'objectif.

Toute tâche de modération, de génération
ou de détection de contenu ne doit être accomplie
par des êtres humains ou par des algorithmes
déterministes, testés et compris.

L'usage des données du site a des fins d'entrainement d'IA,
ainsi que la transmission de ces données à un système d'IA
est strictement interdit.
Tout acte de cette nature sera considéré comme une violation
grave de la politique de gestion des données de l'AE.

## Motifs de cette politique

Le site AE est un programme écrit par des humains, pour des humains.
C'est un logiciel dont la complexité nécessite des connaissances
plus approfondies que ce qui est attendu de la part d'un
étudiant en TC ou en base branche.
À ce titre, l'interdiction de l'IA dans le cadre de son
développement est pensée avant tout dans une optique 
de formation des développeurs, de stabilité de la base de code
et de transmission des connaissances.

Nous ferons ici abstraction de l'impact écologique néfaste de l'IA,
qui n'en reste pas moins préoccupant et qui renforce
les autres motifs ayant poussé à interdire l'IA dans le cadre de l'AE.

### Formation des développeurs

Travailler sur le site AE est possiblement le meilleur moyen de
monter en compétences en informatique pour un étudiant de l'UTBM.
Automatisation des tests, gestion des données et de la sécurité,
infrastructure, maintenance du code existant...

Le site AE est un logiciel complet, dont le développement
possède une dimension pédagogique réelle.
En utilisant l'IA, le développement n'est plus un moyen efficace
de se former.

### Stabilité de la base de code

Les développeurs du site AE sont pour la plupart en cours de formation,
sans compréhension globale de la base de code du site,
des outils logiciels sur lesquels il se base et des bonnes
pratiques permettant d'écrire du code viable.

En se reposant sur un système d'IA sans être capacité
de comprendre intégralement le code proposé ni de le mettre
en perspective avec le reste de la base de code,
c'est toute la maintenance de la base de code qui se retrouve compromise.

### Transmission des connaissances

L'équipe du pôle informatique se renouvelle très souvent.
À ce titre, les nouveaux développeurs se doivent d'hériter
d'une base de code viable. 
Quant aux anciens développeurs, ils se doivent d'en avoir 
compris le fonctionnement, afin d'être en mesure
de guider et d'aider leurs successeurs.

Comme développé dans les deux points précédents, 
cet objectif est incompatible avec l'usage de systèmes d'IA.

