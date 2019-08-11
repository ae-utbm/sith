Introduction
============

Le but de ce projet est de fournir à l'Association des Étudiants de l'UTBM une plate-forme pratique et centralisée de ses services. Le Sith de l'AE tiens à jour le registre des cotisations à l'association, prend en charge la trésorerie, les ventes de produits et services, la diffusion d’événements, la gestion de la laverie et bien plus encore. Il est conçu de manière suffisamment générique pour être facilement adaptable à une autre association.

C'est un projet bénévole qui tire ses origines des années 2000. Il s'agit de la troisième version du site de l'association initiée en 2015. C'est une réécriture complète en rupture totale des deux versions qui l'ont précédé.

Pourquoi réécrire le site
-------------------------

L'ancienne version du site, sobrement baptisée `ae2 <https://ae-dev.utbm.fr/ae/ae2>`_ présentait un nombre impressionnant de fonctionnalités. Il avait été écrit en PHP et se basait sur son propre framework maison.

Malheureusement, son entretiens était plus ou moins hasardeux et son framework reposait sur des principes assez différents de ce qui se fait aujourd'hui, rendant la maintenance difficile. De plus, la version de PHP qu'il utilisait était plus que déprécié et à l'heure de l'arrivée de PHP 7 et de sa non rétrocompatibilité il était vital de faire quelque chose. Il a donc été décidé de le réécrire.

La philosophie du projet
------------------------

Pour éviter les erreurs du passé, ce projet met l'accent sur la maintenabilité. Le choix des technologies ne s'est donc pas fait uniquement sur le fait qu'elle soit récentes, mais également sur leur robustesse, leur fiabilité et leur potentiel à être maintenu loin dans le futur.

La maintenabilité passe également par le choix minutieux des dépendances qui doivent eux aussi passer l'épreuve du temps pour éviter qu'elles ne mettent le projet en danger.

Cela passe également par la minimisation des frameworks employés de manière à réduire un maximum les connaissances nécessaires pour contribuer au projet et donc simplifier la prise en main. La simplicité est à privilégier si elle est possible.

Le projet doit être simple à installer et à déployer.

Le projet étant à destination d'étudiants, il est préférable de minimiser les ressources utilisées par l'utilisateur final. Il faut qu'il soit au maximum économe en bande passante et calcul côté client.


Le projet est un logiciel libre et est sous licence GPL. Aucune dépendance propriétaire ne sera acceptée.
