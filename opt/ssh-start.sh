#!/bin/sh
# Credentials are data, never sourced as shell code.
set -eu
TCEDIR=$(readlink -f /etc/sysconfig/tcedir)
case "$TCEDIR" in /mnt/*) ;; *) exit 0 ;; esac
SETTINGS="$TCEDIR/tdm"
[ -f "$SETTINGS/ssh-mode" ] || exit 0
[ -x /usr/local/sbin/dropbear ] || exit 1
MODE=$(cat "$SETTINGS/ssh-mode")
umask 077
case "$MODE" in
  key)
    [ -s "$SETTINGS/authorized_keys" ] || exit 1
    mkdir -p /home/tc/.ssh
    cp "$SETTINGS/authorized_keys" /home/tc/.ssh/authorized_keys
    chown -R tc:staff /home/tc/.ssh
    chmod 700 /home/tc/.ssh
    chmod 600 /home/tc/.ssh/authorized_keys
    # Give the account an unusable but unlocked password; passwords are disabled.
    printf 'tc:*\n' | chpasswd -e
    set -- -s
    ;;
  password)
    HASH=$(cat "$SETTINGS/password.hash")
    case "$HASH" in '$6$'*) ;; *) exit 1 ;; esac
    [ "$(printf '%s' "$HASH" | wc -l)" -eq 0 ] || exit 1
    printf 'tc:%s\n' "$HASH" | chpasswd -e
    set --
    ;;
  *) exit 1 ;;
esac
mkdir -p /usr/local/etc/dropbear
HOSTKEY=/usr/local/etc/dropbear/tdm_host_key
if [ -s "$SETTINGS/hostkey" ]; then
  cp "$SETTINGS/hostkey" "$HOSTKEY"
else
  /usr/local/bin/dropbearkey -t ed25519 -f "$HOSTKEY"
  cp "$HOSTKEY" "$SETTINGS/hostkey.new"
  mv "$SETTINGS/hostkey.new" "$SETTINGS/hostkey"
  sync
fi
chmod 600 "$HOSTKEY"
/usr/local/sbin/dropbear -E -w -r "$HOSTKEY" -p 22 "$@"
echo '[ssh] Zugang für tc auf Port 22 gestartet'
