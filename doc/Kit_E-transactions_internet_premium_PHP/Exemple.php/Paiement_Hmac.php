<?php

// --------------- VARIABLES A MODIFIER ---------------

// Ennonciation de variables
$pbx_site = '1520411';									//variable de test 1999888
$pbx_rang = '001';									//variable de test 32
$pbx_identifiant = '650995411';				//variable de test 3
$pbx_cmd = 'CMD_1';								//variable de test cmd_test1
$pbx_porteur = 'skia@git.an';							//variable de test test@test.fr
$pbx_total = '510';									//variable de test 100
// Suppression des points ou virgules dans le montant
	$pbx_total = str_replace(",", "", $pbx_total);
	$pbx_total = str_replace(".", "", $pbx_total);

// Paramétrage des urls de redirection après paiement
$pbx_effectue = 'http://www.votre-site.extention/page-de-confirmation';
$pbx_annule = 'http://www.votre-site.extention/page-d-annulation';
$pbx_refuse = 'http://www.votre-site.extention/page-de-refus';
// Paramétrage de l'url de retour back office site
$pbx_repondre_a = 'http://www.votre-site.extention/page-de-back-office-site';
// Paramétrage du retour back office site
$pbx_retour = 'Amount:M;BasketID:R;Auto:A;Error:E;Sig:K';

// Connection à la base de données
// mysql_connect...
// On récupère la clé secrète HMAC (stockée dans une base de données par exemple) et que l’on renseigne dans la variable $keyTest;
//$keyTest = '0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF';
$keyTest = '2d21b1f0d5b64bce056b342b5259db312dfc0176dcafb33eb804b6aaaa3acc07320742954ef3b052f36942b09f86ccb9d24c8814586c1a0d24319fd8985c19e5';



// --------------- TESTS DE DISPONIBILITE DES SERVEURS ---------------

/*
$serveurs = array('tpeweb.paybox.com', //serveur primaire
'tpeweb1.paybox.com'); //serveur secondaire
$serveurOK = "";
//phpinfo(); <== voir paybox
foreach($serveurs as $serveur){
$doc = new DOMDocument();
$doc->loadHTMLFile('https://'.$serveur.'/load.html');
$server_status = "";
$element = $doc->getElementById('server_status');
if($element){
$server_status = $element->textContent;}
if($server_status == "OK"){
// Le serveur est prêt et les services opérationnels
$serveurOK = $serveur;
break;}
// else : La machine est disponible mais les services ne le sont pas.
}
//curl_close($ch); <== voir paybox
if(!$serveurOK){
die("Erreur : Aucun serveur n'a été trouvé");}
// Activation de l'univers de préproduction
//$serveurOK = 'preprod-tpeweb.paybox.com';

//Création de l'url cgi paybox
$serveurOK = 'https://'.$serveurOK.'/cgi/MYchoix_pagepaiement.cgi';
// echo $serveurOK;
*/



// --------------- TRAITEMENT DES VARIABLES ---------------

// On récupère la date au format ISO-8601
$dateTime = date("c");
$dateTime = "2016-07-26T15:38:11+02:00";

// On crée la chaîne à hacher sans URLencodage
$msg = "PBX_SITE=".$pbx_site.
"&PBX_RANG=".$pbx_rang.
"&PBX_IDENTIFIANT=".$pbx_identifiant.
"&PBX_TOTAL=".$pbx_total.
"&PBX_DEVISE=978".
"&PBX_CMD=".$pbx_cmd.
"&PBX_PORTEUR=".$pbx_porteur.
// "&PBX_REPONDRE_A=".$pbx_repondre_a.
"&PBX_RETOUR=".$pbx_retour.
// "&PBX_EFFECTUE=".$pbx_effectue.
// "&PBX_ANNULE=".$pbx_annule.
// "&PBX_REFUSE=".$pbx_refuse.
"&PBX_HASH=SHA512".
"&PBX_TIME=".$dateTime;
// echo $msg;

// Si la clé est en ASCII, On la transforme en binaire
$binKey = pack("H*", $keyTest);

// On calcule l’empreinte (à renseigner dans le paramètre PBX_HMAC) grâce à la fonction hash_hmac et //
// la clé binaire
// On envoi via la variable PBX_HASH l'algorithme de hachage qui a été utilisé (SHA512 dans ce cas)
// Pour afficher la liste des algorithmes disponibles sur votre environnement, décommentez la ligne //
// suivante
// print_r(hash_algos());
echo $msg, "\n\n";
var_dump($binKey);
$hmac = strtoupper(hash_hmac('sha512', $msg, $binKey));

// La chaîne sera envoyée en majuscule, d'où l'utilisation de strtoupper()
// On crée le formulaire à envoyer
// ATTENTION : l'ordre des champs est extrêmement important, il doit
// correspondre exactement à l'ordre des champs dans la chaîne hachée
?>



<!------------------ ENVOI DES INFORMATIONS A PAYBOX (Formulaire) ------------------>
<form method="POST" action="<?php echo $serveurOK; ?>">
<input type="hidden" name="PBX_SITE" value="<?php echo $pbx_site; ?>">
<input type="hidden" name="PBX_RANG" value="<?php echo $pbx_rang; ?>">
<input type="hidden" name="PBX_IDENTIFIANT" value="<?php echo $pbx_identifiant; ?>">
<input type="hidden" name="PBX_TOTAL" value="<?php echo $pbx_total; ?>">
<input type="hidden" name="PBX_DEVISE" value="978">
<input type="hidden" name="PBX_CMD" value="<?php echo $pbx_cmd; ?>">
<input type="hidden" name="PBX_PORTEUR" value="<?php echo $pbx_porteur; ?>">
<input type="hidden" name="PBX_RETOUR" value="<?php echo $pbx_retour; ?>">
<input type="hidden" name="PBX_HASH" value="SHA512">
<input type="hidden" name="PBX_TIME" value="<?php echo $dateTime; ?>">
<input type="hidden" name="PBX_HMAC" value="<?php echo $hmac; ?>">
<input type="submit" value="Envoyer">
</form>
