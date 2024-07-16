Il existe deux types de groupes sur le site AE :

- l'un se base sur des groupes enregistrés en base de données pendant le développement,
  c'est le système de groupes réels.
- L'autre est plus dynamique et comprend tous les groupes générés
  pendant l'exécution et l'utilisation du programme.
  Cela correspond généralement aux groupes liés aux clubs. 
  Ce sont les méta-groupes.

## La définition d'un groupe

Les deux types de groupes sont stockés dans la même table
en base de données, et ne sont différenciés que par un attribut `is_meta`.

### Les groupes réels

Pour plus différencier l'utilisation de ces deux types de groupe,
il a été créé une classe proxy 
(c'est-à-dire qu'elle ne correspond pas à une vraie table en base de donnée)
qui encapsule leur utilisation. 
`RealGroup` peut être utilisé pour créer des groupes réels dans le code
et pour faire une recherche sur ceux-ci
(dans le cadre d'une vérification de permissions par exemple).

### Les méta-groupes

Les méta-groupes, comme expliqué précédemment,
sont utilisés dans les contextes où il est nécessaire de créer un groupe dynamiquement.
Les objets `MetaGroup`, bien que dynamiques, doivent tout de même s'enregistrer
en base de données comme des vrais groupes afin de pouvoir être affectés 
dans les permissions d'autres objets, comme un forum ou une page de wiki par exemple.
C'est principalement utilisé au travers des clubs,
qui génèrent automatiquement deux groupes à leur création :

- club-bureau : contient tous les membres d'un club **au dessus**
  du grade défini dans `settings.SITH_MAXIMUM_FREE_ROLE`.
- club-membres : contient tous les membres d'un club 
  **en dessous** du grade défini dans `settings.SITH_MAXIMUM_FREE_ROLE`.


## Les groupes réels utilisés

Les groupes réels que l'on utilise dans le site sont les suivants :

Groupes gérés automatiquement par le site :

- `Public` : tous les utilisateurs du site
- `Subscribers` : tous les cotisants du site
- `Old subscribers` : tous les anciens cotisants

Groupes gérés par les administrateurs (à appliquer à la main sur un utilisateur) :

- `Root` : administrateur global du site
- `Accounting admin` : les administrateurs de la comptabilité
- `Communication admin` : les administrateurs de la communication
- `Counter admin` : les administrateurs des comptoirs (foyer et autre)
- `SAS admin` : les administrateurs du SAS
- `Forum admin` : les administrateurs du forum
- `Pedagogy admin` : les administrateurs de la pédagogie (guide des UVs)
- `Banned from buying alcohol` : les utilisateurs interdits de vente d'alcool (non mineurs)
- `Banned from counters` : les utilisateurs interdits d'utilisation des comptoirs
- `Banned to subscribe` : les utilisateurs interdits de cotisation


