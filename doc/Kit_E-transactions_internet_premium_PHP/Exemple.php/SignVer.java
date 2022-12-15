package signver;

import java.security.interfaces.RSAPublicKey;
import java.security.Signature;
import java.security.KeyFactory;
import java.security.spec.X509EncodedKeySpec;
import java.io.FileInputStream;
import java.io.DataInputStream;

import org.apache.commons.codec.binary.Base64;
import org.apache.commons.codec.net.URLCodec;

public class SignVer {

    // verification signature RSA des donnees avec cle publique

    private static boolean verify( byte[] dataBytes, byte[] sigBytes, String sigAlg, RSAPublicKey pubKey) throws Exception
    {
        Signature sig = Signature.getInstance(sigAlg);
        sig.initVerify(pubKey);
        sig.update(dataBytes);
        return sig.verify(sigBytes);
    }

    // chargement de la cle AU FORMAT der :
    // openssl rsa -inform PEM -in pbx_pubkey.pem -outform DER -pubin -out /tmp/pubkey.der

    private static RSAPublicKey getPubKey(String pubKeyFile) throws Exception
    {
        FileInputStream fis = new FileInputStream(pubKeyFile);
        DataInputStream dis = new DataInputStream(fis);
        byte[] pubKeyBytes = new byte[fis.available()];
        dis.readFully(pubKeyBytes);
        fis.close();
        dis.close();
        KeyFactory keyFactory = KeyFactory.getInstance("RSA");
        // extraction cle
        X509EncodedKeySpec pubSpec = new X509EncodedKeySpec(pubKeyBytes);
        RSAPublicKey pubKey = (RSAPublicKey) keyFactory.generatePublic(pubSpec);
        return pubKey;
     }
    
     // exemple de verification de la signature
    
     public static void main(String[] unused) throws Exception {
        
        String sData = "";          // donnees signees URL encodees
        String sSig  = "";          // signature Base64 et URL encodee 
        
        // decodage ...
        byte[] dataBytes = URLCodec.decodeUrl(sData.getBytes());
        byte[] sigBytes = Base64.decodeBase64( URLCodec.decodeUrl(sSig.getBytes()));
        
        // lecture de la cle publique       
        RSAPublicKey pubK = getPubKey("/tmp/pubkey.der");

        // verification signature
        boolean result = verify(dataBytes, sigBytes, "SHA1withRSA", pubK);
        
        // affichage resultat
        System.out.println("Resultat de la verification de signature : " + result);
    }
}
