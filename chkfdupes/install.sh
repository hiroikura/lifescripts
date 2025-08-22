#!/bin/sh
PROG=chkfdupes
SRC=$PROG.py
DEST=$HOME/bin
INTERP=/usr/bin/python3

# flags
#TEMPINSTALL=yes

if [ "$TEMPINSTALL" = 'yes' ]; then
	SRCPATH="`pwd`/$SRC"
	DESTPATH="$DEST/$PROG"
	rm -f $DESTPATH
	cat > $DESTPATH << EOF
#!/bin/sh
$INTERP $SRCPATH \$@
EOF
	chmod +x $DESTPATH
	exit 0
fi

/usr/bin/install $SRC $DEST/$PROG
