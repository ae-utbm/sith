Vous avez ajouté une application et vous voulez y mettre du javascript ?

Vous voulez importer depuis cette nouvelle application dans votre script géré par webpack ?

Eh bien il faut manuellement enregistrer dans node où les trouver et c'est très simple.

D'abord, il faut ajouter dans node via `package.json`:

```json
{
    // ...
    "imports": {
        // ...
        "#mon_app:*": "./mon_app/static/webpack/*"
    }
    // ...
}
```

Ensuite, pour faire fonctionne l'auto-complétion, il faut configurer `tsconfig.json`:

```json
{
    "compilerOptions": {
        // ...
        "paths": {
            // ...
            "#mon_app:*": ["./mon_app/static/webpack/*"]
        }
    }
}
```

Et c'est tout !

!!!note

	Il se peut qu'il soit nécessaire de redémarrer `./manage.py runserver` pour
	que les changements prennent effet.