## Mettre à jour la base de données antispam

L'anti spam nécessite d'être à jour par rapport à des bases de données externe.
Il existe une commande pour ça qu'il faut lancer régulièrement.
Lors de la mise en production, il est judicieux de configurer
un cron pour la mettre à jour au moins une fois par jour.

```bash
python manage.py update_spam_database
```
