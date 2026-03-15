Le site AE offre des mécanismes permettant aux applications tierces
de récupérer les informations sur un utilisateur du site AE.
De cette manière, il devient possible de synchroniser les informations
qu possède l'application tierce sur l'utilisateur, directement depuis
le site AE.

## Fonctionnement général

Pour authentifier vos utilisateurs, vous aurez besoin d'un serveur web
et d'un client d'API (celui auquel est liée votre
[clef d'API](./connect.md#obtenir-une-clef-dapi)).
Deux informations vous sont nécessaires, en plus de votre clef d'API :

- l'id du client : vous pouvez l'obtenir soit en le demandant à l'équipe info,
  soit en appelant la route `GET /client/me` avec votre clef d'API
  renseignée dans le header [X-APIKey](./connect.md#x-apikey)
- la clef HMAC du client : vous devez la demander à l'équipe info.

Grâce à ces informations, vous allez pouvoir fournir le contexte nécessaire
au site AE pour qu'il authentifie vos utilisateurs.

En effet, la démarche d'authentification s'effectue presque entièrement
sur le site : le travail de l'application tierce consiste uniquement
à fournir à l'utilisateur une url avec les bons paramètres, puis
à recevoir la réponse du serveur si tout s'est bien passé.

Comme un dessin vaut parfois mieux que mille mots,
voici les diagrammes décrivant le processus.
L'un montre l'entièreté de la démarche ;
l'autre dans un souci de simplicité, ne montre que ce qui est visible
directement par l'application tierce.

=== "Intégralité du processus"

    ```mermaid
    sequenceDiagram
        actor User
        participant App
        User->>+App: Authentifie-moi, stp
        App-->>-User: url de connexion<br/>avec signature
        User->>+Sith: GET url
        opt Utilisateur non-connecté
            Sith->>+User: Formulaire de connexion
            User-->>-Sith: Connexion
        end
        Sith->>Sith: vérification de la signature
        Sith->>+User: Formulaire<br/>des conditions<br/>d'utilisation
        User-->>-Sith: Validation
        Sith->>+App: URL de retour<br/>avec données utilisateur
        App->>App: Traitement des <br/>données utilisateur
        App-->>-Sith: 204 OK, No content
        Sith-->>-User: Message de succès
        App--)User: Message de succès
    ```

=== "Point de vue de l'application tierce"

    ```mermaid
    sequenceDiagram
        actor User
        participant App
        User->>+App: Authentifie-moi, stp
        App-->>-User: url de connexion<br/>avec signature
        opt
            Sith->>+App: URL de retour<br/>avec données utilisateur
            App->>App: Traitement des <br/>données utilisateur
            App-->>-Sith: 204 OK, No content
            App--)User: Message de succès
        end
    ```

## Données attendues

### URL de connexion

L'URL de connexion que vous allez fournir à l'utilisateur doit
être `https://ae.utbm.fr/api-link/auth/`
et doit contenir les données décrites dans
[`ThirdPartyAuthParamsSchema`][api.schemas.ThirdPartyAuthParamsSchema] :

- `client_id` (integer) : l'id de votre client, que vous pouvez obtenir
  de la manière décrite plus haut
- `third_party_app`(string) : le nom de la plateforme pour laquelle
  l'authentification va être réalisée (si votre application est un bot
  discord, mettez la valeur "discord")
- `privacy_link`(URL) : l'URL vers la page de politique de confidentialité
  qui s'appliquera dans le cadre de l'application
  (s'il s'agit d'un bot discord, donnez le lien vers celles de Discord)
- `username`(string) : le pseudonyme que l'utilisateur possède sur
  votre application
- `callback_url`(URL) : l'URL que le site AE appellera si l'authentification
  réussit
- `signature`(string) : la signature des données de la requête.

Ces données doivent être url-encodées et passées dans les paramètres GET.

!!!tip "URL de retour"

    Notre système n'impose aucune contrainte quant à la manière
    de construire votre URL (hormis le fait que ce doit être une URL HTTPS valide),
    mais il est tout de même conseillé d'utiliser l'identifiant de votre
    utilisateur comme paramètre dans l'URL 
    (par exemple `GET /callback/{int:user_id}/`).

???Example

    Supposons que votre client d'API soit utilisé dans le cadre d'un bot Discord,
    avec les données suivantes :
    
    - l'id du client est 15
    - sa clef HMAC est "beb99dd53"
      (c'est pour l'exemple, une vraie clef sera beaucoup plus longue)
    - le pseudonyme discord de votre utilisateur est Brian
    - son id sur discord est 123456789
    - votre route de callback est `GET /callback/{int:user_id}/`,
      accessible au domaine `https://bot.ae.utbm.fr`
    
    Alors les paramètres de votre URL seront :
    
    | Paramètre       | valeur                                                                |
    |-----------------|-----------------------------------------------------------------------|
    | client_id       | 15                                                                    |
    | third_party_app | discord                                                               |
    | privacy_link    | `https://discord.com/privacy`                                         |
    | username        | Brian                                                                 |
    | callback_url    | `https://bot.ae.utbm.fr/callback/123456789/`                          |
    | signature       | 1a383c51060be64f07772aa42e07<br/>18ae096b8f21f2cdb4061c0834a416d12101 |
    
    Et l'url fournie à l'utilisateur sera :
    
    `https://ae.utbm.fr/api-link/auth/?client_id=15&third_party_app=discord
    &privacy_link=https%3A%2F%2Fdiscord.com%2Fprivacy&username=Brian
    &callback_url=https%3A%2F%2Fbot.ae.utbm.fr%2Fcallback%2F123456789%2F
    &signature=1a383c51060be64f07772aa42e0718ae096b8f21f2cdb4061c0834a416d12101`

### Données de retour

Si l'authentification réussit, le site AE enverra une requête HTTP POST
à l'URL de retour fournie dans l'URL de connexion.

Le corps de la requête de callback et au format JSON 
et contient deux paires clef-valeur :

- `user` : les données utilisateur, telles que décrites
  par [UserProfileSchema][core.schemas.UserProfileSchema]
- `signature` : la signature des données utilisateur

???Example

    En reprenant les mêmes paramètres que dans l'exemple précédent,
    le site AE pourra renvoyer à l'application la requête suivante :

    ```http
    POST https://bot.ae.utbm.fr/callback/123456789/
    content-type: application/json
    body: {
        "user": {
            "id": 144131,
            "nick_name": "inzekitchen",
            "first_name": "Brian",
            ...
        },
        "signature": "f16955bab6b805f6e1abbb98a86dfee53fed0bf812aa6513ca46cfd461b70020"
    }
    ```

L'application doit répondre avec un des codes HTTP suivants :

| Code | Raison                                                                         |
|------|--------------------------------------------------------------------------------|
| 204  | Tout s'est bien passé                                                          |
| 403  | Les données de retour ne sont <br>pas signées ou sont mal signées              |
| 404  | L'URL de retour ne permet pas <br>d'identifier un utilisateur de l'application |

!!!note "Code d'erreur par défaut"

    Si l'appel de la route fait face à plusieurs problèmes en même temps 
    (par exemple, l'URL ne permet pas de retrouver votre utilisateur, 
    et en plus les données sont mal signées),
    le 403 prime et doit être retourné par défaut.

## Signature des données

Les données de l'URL de connexion doivent être signées,
et la signature de l'URL de retour doit être vérifiée.

Dans le deux cas, la signature est le digest HMAC-SHA512
des données url-encodées, en utilisant la clef HMAC du client d'API.

???Example "Signature de l'URL de connexion"

    En reprenant le même exemple que les fois précédentes,
    l'url-encodage des données est :

    `client_id=15&third_party_app=discord
    &privacy_link=https%3A%2F%2Fdiscord.com%2Fprivacy%2F&username=Brian
    &callback_url=https%3A%2F%2Fbot.ae.utbm.fr%2Fcallback%2F123456789%2F`

    Notez que la signature n'est pas (encore) dedans.
    Cette dernière peut-être obtenue avec le code suivant :

    === ":simple-python: Python"
    
        Dépendances :
    
        - `environs` (>=14.1)
    
        ```python
        import hmac
        from urllib.parse import urlencode
        
        from environs import Env
        
        env = Env()
        env.read_env()
        
        key = env.str("HMAC_KEY").encode()
        data = {
            "client_id": 15,
            "third_party_app": "discord",
            "privacy_link": "https://discord.com/privacy/",
            "username": "Brian",
            "callback_url": "https://bot.ae.utbm.fr/callback/123456789/",
        }
        urlencoded = urlencode(data)
        data["signature"] = hmac.digest(key, urlencoded.encode(), "sha512").hex()
        
        # URL a fournir à l'utilisateur pour son authentification
        user_url = f"https://ae.ubtm.fr/api-link/auth/?{urlencode(data)}"
        ```    
    
    === ":simple-rust: Rust"
    
        Dépendances :
        
        - `hmac` (>=0.12.1)
        - `url` (>=2.5.7, features `serde`)
        - `serde` (>=1.0.228, features `derive`)
        - `serde_urlencoded` (>="0.7.1)
        - `sha2` (>=0.10.9)
        - `dotenvy` (>= 0.15)
    
        ```rust
        use hmac::{Mac, SimpleHmac};
        use serde::Serialize;
        use sha2::Sha512;
        use url::Url;
        
        #[derive(Serialize, Debug)]
        struct UrlData<'a> {
            client_id: u32,
            third_party_app: &'a str,
            privacy_link: Url,
            username: &'a str,
            callback_url: Url,
        }
        
        impl<'a> UrlData<'a> {
            pub fn signature(&self, key: &[u8]) -> CtOutput<SimpleHmac<Sha512>> {
                let urlencoded = serde_urlencoded::to_string(self).unwrap();
                SimpleHmac::<Sha512>::new_from_slice(key)
                    .unwrap()
                    .chain_update(urlencoded.as_bytes())
                    .finalize()
            }
        }
        
        impl Into<Url> for UrlData<'_> {
            fn into(self) -> Url {
                let key = std::env::var("HMAC_KEY").unwrap();
                let mut url = Url::parse("http://ae.utbm.fr/api-link/auth/").unwrap();
                url.set_query(Some(
                    format!(
                        "{}&signature={:x}",
                        serde_urlencoded::to_string(&self).unwrap(),
                        self.signature(key.as_bytes()).into_bytes()
                    )
                    .as_str(),
                ));
                url
            }
        }
        
        fn main() {
            dotenvy::dotenv().expect("Couldn't load env");
            let data = UrlData {
                client_id: 1,
                third_party_app: "discord",
                privacy_link: "https://discord.com/privacy/".parse().unwrap(),
                username: "Brian",
                callback_url: "https://bot.ae.utbm.fr/callback/123456789/"
                    .parse()
                    .unwrap(),
            };
            let url: Url = data.into();
            println!("{:?}", url);
        }
        ```

???Example "Vérification de la signature de la réponse"

    Les données utilisateur peuvent ressembler à :

    ```json
    {
        "user": {
            "display_name": "Matthieu Vincent",
            "profile_url": "/user/380/",
            "profile_pict": "/static/core/img/unknown.jpg",
            "id": 380,
            "nick_name": None,
            "first_name": "Matthieu",
            "last_name": "Vincent",
        },
        "signature": "3802a280fbb01bd9fetc."
    }
    ```

    Vous pouvez vérifier la signature ainsi :

    ```python
        import hmac
        from urllib.parse import urlencode
        
        from environs import Env
        
        env = Env()
        env.read_env()
        
        def is_signature_valid(user_data: dict, signature: str) -> bool:
            key = env.str("HMAC_KEY").encode()
            urlencoded = urlencode(user_data)
            return hmac.compare_digest(
                hmac.digest(key, urlencoded.encode(), "sha512").hex(),
                signature,
            )
        
        
        post_data = <récupération des données POST>
        print(
            "signature valide :", 
            is_signature_valid(post_data["user"], post_data["signature"]
        )
    ```

!!!Warning

    Vous devez impérativement vérifier la signature 
    des données de la requête de callback !

    Si l'équipe informatique se rend compte que vous ne le faites pas,
    elle se réserve le droit de suspendre votre application,
    immédiatement et sans préavis.
