{ pkgs, python3 }:

let
  version = "2.1.0";

  pythonEnv = python3.withPackages (ps: [
    ps.sphinx
  ]);

  xapianCore = pkgs.stdenv.mkDerivation rec {
    pname = "xapian-core";
    inherit version;

    src = pkgs.fetchurl {
      url = "https://oligarchy.co.uk/xapian/${version}/xapian-core-${version}.tar.xz";
      sha256 = "8e1259586d342e3d12b5e1f772e9185a10f2ba16e541566b5c3c239f71b8aacc"; 
    };

    nativeBuildInputs = [ pkgs.pkg-config ];
    buildInputs = [ pkgs.zlib pkgs.util-linux ]; 

    configureFlags = [ "--enable-shared" ];
  };

  xapianBindings = pkgs.stdenv.mkDerivation rec {
    pname = "xapian-bindings";
    inherit version;

    src = pkgs.fetchurl {
      url = "https://oligarchy.co.uk/xapian/${version}/xapian-bindings-${version}.tar.xz";
      sha256 = "f52ec189f13b4fa66ea625a6eb94bb32dd651b9ec806be6a911dda54cbe3875c"; 
    };

    nativeBuildInputs = [ pkgs.pkg-config pythonEnv ];
    buildInputs = [ xapianCore pythonEnv ];

    # Create the output site-packages directory before configuring
    preConfigure = ''
      mkdir -p "$out/lib/python3.14/site-packages"
    '';

    # Tell Autotools exactly where to put the Python binding files
    configureFlags = [
      "--with-python3"
      "XAPIAN_CONFIG=${xapianCore}/bin/xapian-config"
      "PYTHON3_LIB=$(out)/lib/python3.14/site-packages"
    ];

    installPhase = ''
      make install
    '';
  };
in
{
  inherit xapianCore xapianBindings;
}