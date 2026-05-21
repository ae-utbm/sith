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

Vous devrez modifier ce fichier chaque fois qu'un élément du localStorage
cessera d'être utilisé.
Les modifications à apporter sont les suivantes :

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

## Versionnage d'une clef

Dans le cas où une paire clef-valeur du localStorage subit un changement
dans son schéma de données, utilisez `versionedLocalStorage` :

```typescript
import { versionedLocalStorage } from "#core:core/localstorage";

const foo = () => {
  let obj = versionedLocalStorage.getItem("<key>", { version: 1 });
  if (obj === null) {
    obj = fetchMyObject();
    versionedLocalStorage.setItem("<key>", obj, { version: 1 })
  }
  // Do something with obj...
}
```

!!!Warning

    Il existe une différence d'usage entre `localStorage` et `versionedLocalStorage` :
    les valeurs données à `localStorage` doivent être des strings (généralement
    obtenus avec `JSON.stringify`), tandis que `versionedLocalStorage` utilise
    directement des objets JS.

    Cette différence résulte du fait que `versionedLocalStorage` doit légèrement
    modifier les données pour y inclure la version, et gérer en interne
    la conversion en JSON.