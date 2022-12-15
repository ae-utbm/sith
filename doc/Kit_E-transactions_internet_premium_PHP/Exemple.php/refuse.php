<?php
$montant=$_GET['montant'];
$ref_com=$_GET['ref'];
#$auto=$_GET['auto'];
$trans=$_GET['trans'];
print ("<center><b><h2>Votre transaction a été refusée</h2></center></b><br>");
print ("<br><b>MONTANT : </b>$montant\n");
print ("<br><b>REFERENCE : </b>$ref_com\n");
#print ("<br><b>AUTO : </b>$auto\n");
print ("<br><b>TRANS : </b>$trans\n");
?>