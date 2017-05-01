
///// script PHP de vérification de la signature Paybox.
///// Ce code peut s'executer dans un contexte Apache/PHP.
///// Il affiche alors une page web qui permet de vérifier et signer des données.



<html>
<head>
<title>formulaire d'exemple pour test signature</title>
</head>
<body>

<?php

$status = "GUY";

function LoadKey( $keyfile, $pub=true, $pass='' ) {         // chargement de la clé (publique par défaut)

    $fp = $filedata = $key = FALSE;                         // initialisation variables
    $fsize =  filesize( $keyfile );                         // taille du fichier
    if( !$fsize ) return FALSE;                             // si erreur on quitte de suite
    $fp = fopen( $keyfile, 'r' );                           // ouverture fichier
    if( !$fp ) return FALSE;                                // si erreur ouverture on quitte
    $filedata = fread( $fp, $fsize );                       // lecture contenu fichier
    fclose( $fp );                                          // fermeture fichier
    if( !$filedata ) return FALSE;                          // si erreur lecture, on quitte
    if( $pub )
        $key = openssl_pkey_get_public( $filedata );        // recuperation de la cle publique
    else                                                    // ou recuperation de la cle privee
        $key = openssl_pkey_get_private( array( $filedata, $pass ));
    return $key;                                            // renvoi cle ( ou erreur )
}

// comme precise la documentation Paybox, la signature doit être
// obligatoirement en dernière position pour que cela fonctionne

function GetSignedData( $qrystr, &$data, &$sig ) {          // renvoi les donnes signees et la signature

    $pos = strrpos( $qrystr, '&' );                         // cherche dernier separateur
    $data = substr( $qrystr, 0, $pos );                     // et voila les donnees signees
    $pos= strpos( $qrystr, '=', $pos ) + 1;                 // cherche debut valeur signature
    $sig = substr( $qrystr, $pos );                         // et voila la signature
    $sig = base64_decode( urldecode( $sig ));               // decodage signature
}

// $querystring = chaine entière retournée par Paybox lors du retour au site (méthode GET)
// $keyfile = chemin d'accès complet au fichier de la clé publique Paybox

function PbxVerSign( $qrystr, $keyfile ) {                  // verification signature Paybox

    $key = LoadKey( $keyfile );                             // chargement de la cle
    if( !$key ) return -1;                                  // si erreur chargement cle
//  penser à openssl_error_string() pour diagnostic openssl si erreur
    GetSignedData( $qrystr, $data, $sig );                  // separation et recuperation signature et donnees
    return openssl_verify( $data, $sig, $key );             // verification : 1 si valide, 0 si invalide, -1 si erreur
}

if( !isset( $_POST['data'] ))                               // pour alimentation par defaut quand premier affichage du formulaire
    $_POST['data'] = 'arg1=aaaa&arg2=bbbb&arg3=cccc&arg4=dddd';

if( isset( $_POST['signer']) ) {                            // si on a demande la signature

    $key = LoadKey( 'TestK004.prv.pem', false );            // chargement de la cle prive (de test, sans mot de passe)
    if( $key ) {
        openssl_sign( $_POST['data'], $signature, $key );   // generation de la signature
        openssl_free_key( $key );                           // liberation ressource (confidentialite cle prive)
        $status = "OK";
    }
    else $status = openssl_error_string();                  // diagnostic erreur

    $_POST['signeddata'] = $_POST['data'];                  //  construction chaine data + signature
    $_POST['signeddata'] .= '&sig=';
    $_POST['signeddata'] .= urlencode( base64_encode( $signature ));
}
if( isset( $_POST['verifier']) ) {                          // si on a demande la verification

    $CheckSig = PbxVerSign( $_POST['signeddata'], 'TestK004.pub.pem' );

    if( $CheckSig == 1 )       $status = "Signature valide";
    else if( $CheckSig == 0 )  $status = "Signature invalide : donnees alterees ou signature falsifiee";
    else                       $status = "Erreur lors de la vérification de la signature";
}

?>
    <form action="testsign.php" method="POST">
    <table border="0" cellpadding="3" cellspacing="0" align="center">
    <tr>
      <td>status = <?php echo $status; ?></td>
    </tr>
    <tr>
      <td><input type="text" name="data" size="80"value="<?= $_POST['data'] ?>"></td>
      <td><input type="submit" name="signer" value="signer"/></td>
    </tr>
    <tr>
      <td><input type="text" name="signeddata" size="80"value="<?= $_POST['signeddata'] ?>"></td>
      <td><input type="submit" name="verifier" value="verifier"/></td>
    </tr>
    </table>
    </form>
</body>
</html>
