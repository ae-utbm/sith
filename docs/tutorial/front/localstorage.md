[Documentation du localStorage (mozilla)](https://developer.mozilla.org/fr/docs/Web/API/Window/localStorage)

## Utilité et limitations

Le `localStorage` est un cache géré directement par le navigateur.
Il permet de stocker des données directement chez le client.
Il s'agit donc d'un outil extrêmement puissant, qui permet d'éviter
beaucoup de requêtes au serveur, améliorant ainsi les temps de chargement.

Cependant, il y a deux limitations majeures à prendre en compte :

- le `localStorage` est entièrement géré par le client,
  une fois le déploiement effectué, vous ne pouvez plus y toucher ;
  vous devez donc être sûr de vous avant d'apporter des modifications
  reposant sur le `localStorage`.
- la quantité de données stockable est limitée à 10Mo ;
  une fois ce quota rempli, le navigateur lèvera une `QuotaExceededError`.

## Invalidation du `localStorage`

Pour résoudre le premier de ces deux problèmes, il y a un script permettant
d'annuler une partie du cache.
Ce dernier se trouve dans le fichier `core/static/bundled/core/cache.ts`.

Vous devrez modifier ce cache chaque fois que vous effectuerez
un changement de schéma, c'est-à-dire dans un des cas suivants :

- une des clefs du cache n'est plus utilisée
- la clef n'a pas changé, mais la manière dont les données attachées à cette clef
  sont formées a été modifiée.

!!!Note

    Si vous ne faites qu'ajouter des données, sans modifier ni supprimer
    celles qui sont là, vous n'avez pas besoin d'invalider le cache.

Vous devez effectuer deux modifications dans ce fichier :

- incrémenter la version du cache
- ajouter une ligne permettant de retirer votre clef du cache

```ts hl_lines="2 11"
// increment this number when a breaking change is made with localStorage
const CURRENT_CACHE_VERSION = 2;  // <-- changez cette ligne

export function cacheBuster() {
  const version = Number.parseInt(localStorage.getItem("version") ?? "0", 10);
  if (version === CURRENT_CACHE_VERSION) {
    // The cache schema is up-to-date. Nothing to do.
    return;
  }
  // ...
  localStorage.removeItem("<clef>");  // <-- et rajoutez cette ligne
  localStorage.setItem("version", CURRENT_CACHE_VERSION.toString());
}
```
