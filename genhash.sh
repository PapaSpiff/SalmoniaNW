#!/bin/sh

FNAME=hash.py
#HASHREF=https://raw.githubusercontent.com/nintendoapis/splatnet3-types/main/src/generated/latest.ts
#HASHREF=https://gitlab.fancy.org.uk/samuel/splatnet3-types/-/raw/main/src/generated/latest.ts
HASHREF=https://raw.githubusercontent.com/misenhower/splatoon3.ink/main/app/splatnet/queryHashes.json

cat > $FNAME <<EOF
from enum import Enum

# See $HASHREF
# generated by $0

class SHA256Hash(Enum):
EOF

#curl -s $HASHREF | cut -f5,8 -d ' ' | sed s,.\./,\ =\ \", | sed 's/\.js../\"/' | sed 's,queries/,,' |  sed 's/^/        /' >> $FNAME
curl -s $HASHREF | grep "^      " | sed 's/^\( *\)\"\([^\"]*\)\"/\1\2/' | sed 'y/:/=/' | sed 's/,$//' | sed 's/^/  /' >> $FNAME

cat >> $FNAME <<EOF

EOF

