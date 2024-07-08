#!/usr/bin/env bash
# Originates from https://gist.github.com/jorgecarleitao/ab6246c86c936b9c55fd
# first argument of the script is Xapian version (e.g. 1.2.19)
VERSION="$1"

# Cleanup env vars for auto discovery mechanism
export CPATH=
export LIBRARY_PATH=
export CFLAGS=
export LDFLAGS=
export CCFLAGS=
export CXXFLAGS=
export CPPFLAGS=

# prepare
rm -rf "$VIRTUAL_ENV/packages"
mkdir -p "$VIRTUAL_ENV/packages" && cd "$VIRTUAL_ENV/packages" || exit 1

CORE=xapian-core-$VERSION
BINDINGS=xapian-bindings-$VERSION

# download
echo "Downloading source..."
curl -O "https://oligarchy.co.uk/xapian/$VERSION/${CORE}.tar.xz"
curl -O "https://oligarchy.co.uk/xapian/$VERSION/${BINDINGS}.tar.xz"

# extract
echo "Extracting source..."
tar xf "${CORE}.tar.xz"
tar xf "${BINDINGS}.tar.xz"

# install
echo "Installing Xapian-core..."
cd "$VIRTUAL_ENV/packages/${CORE}" || exit 1
./configure --prefix="$VIRTUAL_ENV" && make && make install

PYTHON_FLAG=--with-python3

echo "Installing Xapian-bindings..."
cd "$VIRTUAL_ENV/packages/${BINDINGS}" || exit 1
./configure --prefix="$VIRTUAL_ENV" $PYTHON_FLAG XAPIAN_CONFIG="$VIRTUAL_ENV/bin/xapian-config" && make && make install

# clean
rm -rf "$VIRTUAL_ENV/packages"

# test
python -c "import xapian"
