#!/bin/sh
# Usage: sh tests/run.sh
set -u
here=$(cd "$(dirname "$0")" && pwd)
s=$here/../scripts
T=$(mktemp -d)
pass=0
fail=0
ok() { pass=$((pass + 1)); echo "PASS $1"; }
bad() { fail=$((fail + 1)); echo "FAIL $1"; }
mk() {
  d=$T/$1; mkdir -p "$d"
  for tool in sh awk grep head od tr date cat sleep dirname rm nohup; do ln -s "$(command -v $tool)" "$d/$tool"; done
}
fakeadb() {
  cat > "$T/$1/adb" <<'SH'
#!/bin/sh
case "$1" in
  devices) printf 'List of devices attached\n'; [ -n "${FAKE_DEVS:-}" ] && printf '%b' "$FAKE_DEVS" ;;
  shell) printf 'mWakefulness=%s\n' "${FAKE_WAKE:-Awake}" ;;
  exec-out) if [ -n "${FAKE_BADPNG:-}" ]; then printf 'not a png'; else printf '\211PNG\r\n\032\nfakebytes'; fi ;;
esac
SH
  chmod +x "$T/$1/adb"
}
fakescrcpy() {
  printf '#!/bin/sh\nprintf "%%s\\n" "$*" >> "$FAKE_LOG"\n[ -n "${FAKE_QUIT:-}" ] && exit 0\nexec sleep 30\n' > "$T/$1/scrcpy"; chmod +x "$T/$1/scrcpy"
}
run() { d=$1; shift; env PATH="$T/$d" TMPDIR="$T/tmp" FAKE_LOG="$T/log" "$@"; }
mkdir -p "$T/tmp"
DEV='SECRETSERIAL1\tdevice\n'

mk none
run none sh "$s/android-check.sh" >"$T/o" 2>&1; c=$?
[ "$c" -eq 1 ] && grep -q "android-tools" "$T/o" && ok "no adb: exit 1 and how to install it" || bad "no adb is wrong (exit $c)"
mk a; fakeadb a
run a sh "$s/android-check.sh" >"$T/o" 2>&1; c=$?
[ "$c" -eq 2 ] && grep -q "connect it with a USB cable first" "$T/o" && ok "no phone: exit 2 and the user is asked to connect the cable first" || bad "no phone is wrong (exit $c)"
FAKE_DEVS='SECRETSERIAL1\tunauthorized\n' run a sh "$s/android-check.sh" >"$T/o" 2>&1; c=$?
[ "$c" -eq 3 ] && grep -q "tap Allow" "$T/o" && ok "unauthorized: exit 3 and the user is asked to tap Allow" || bad "unauthorized is wrong (exit $c)"
FAKE_DEVS='SECRETSERIAL1\toffline\n' run a sh "$s/android-check.sh" >"$T/o" 2>&1; c=$?
[ "$c" -eq 3 ] && grep -q "replug" "$T/o" && ok "offline: exit 3 and the user is asked to replug the cable" || bad "offline is wrong (exit $c)"
FAKE_DEVS="$DEV" run a sh "$s/android-check.sh" >"$T/o" 2>&1; c=$?
[ "$c" -eq 0 ] && grep -q "^ready" "$T/o" && ok "one authorized phone: exit 0" || bad "a ready phone is wrong (exit $c)"
! grep -q SECRETSERIAL "$T/o" && ok "the device serial is never printed" || bad "the serial leaked"
FAKE_DEVS='AAA\tdevice\nBBB\tdevice\n' run a sh "$s/android-check.sh" >"$T/o" 2>&1; c=$?
[ "$c" -eq 4 ] && ok "two phones and no choice: exit 4" || bad "two phones are wrong (exit $c)"
FAKE_DEVS='AAA\tdevice\nBBB\tdevice\n' ANDROID_SERIAL=AAA run a sh "$s/android-check.sh" >/dev/null 2>&1; [ $? -eq 0 ] && ok "two phones with ANDROID_SERIAL set: exit 0" || bad "ANDROID_SERIAL is not honored"

FAKE_DEVS="$DEV" run a sh "$s/screenshot.sh" >"$T/o" 2>&1; c=$?
p=$(tail -1 "$T/o")
[ "$c" -eq 0 ] && [ -f "$p" ] && [ "$(head -c 4 "$p" | od -An -tx1 | tr -d ' \n')" = 89504e47 ] && ok "screenshot saves a PNG and prints its path" || bad "screenshot is wrong (exit $c, path $p)"
case "$p" in "$T/tmp/"*) ok "the default path is in the temp folder" ;; *) bad "the default path is not in the temp folder: $p" ;; esac
! grep -q SECRETSERIAL "$T/o" && ok "screenshot never prints the serial" || bad "screenshot leaked the serial"
FAKE_DEVS="$DEV" FAKE_WAKE=Asleep run a sh "$s/screenshot.sh" "$T/off.png" >"$T/o" 2>&1; c=$?
[ "$c" -eq 5 ] && [ ! -e "$T/off.png" ] && ok "screen off: exit 5 and no file" || bad "screen off is wrong (exit $c)"
FAKE_DEVS="$DEV" FAKE_BADPNG=1 run a sh "$s/screenshot.sh" "$T/bad.png" >"$T/o" 2>&1; c=$?
[ "$c" -eq 8 ] && [ ! -e "$T/bad.png" ] && ok "a capture that is not a PNG: exit 8 and no file left" || bad "a bad capture is wrong (exit $c)"
run a sh "$s/screenshot.sh" "$T/none.png" >/dev/null 2>&1; [ $? -eq 2 ] && [ ! -e "$T/none.png" ] && ok "screenshot with no phone passes exit 2 through" || bad "screenshot with no phone is wrong"

FAKE_DEVS="$DEV" run a sh "$s/mirror.sh" >"$T/o" 2>&1; c=$?
[ "$c" -eq 6 ] && grep -q "pacman -S scrcpy" "$T/o" && ok "no scrcpy: exit 6 and how to install it" || bad "no scrcpy is wrong (exit $c)"
mk b; fakeadb b; fakescrcpy b
rm -f "$T/log"; FAKE_DEVS="$DEV" run b sh "$s/mirror.sh" >"$T/o" 2>&1; c=$?
pid=$(sed -n 's/.*(pid \([0-9]*\)).*/\1/p' "$T/o")
[ "$c" -eq 0 ] && [ -n "$pid" ] && grep -q -- "--no-audio" "$T/log" && ok "mirror starts scrcpy with --no-audio and prints its pid" || bad "mirror is wrong (exit $c)"
[ -n "$pid" ] && kill "$pid" 2>/dev/null
! grep -q SECRETSERIAL "$T/o" && ok "mirror never prints the serial" || bad "mirror leaked the serial"
rm -f "$T/log"; FAKE_DEVS="$DEV" FAKE_QUIT=1 run b sh "$s/mirror.sh" >"$T/o" 2>&1; [ $? -eq 7 ] && ok "scrcpy quitting at once: exit 7" || bad "a quitting scrcpy is not exit 7"
rm -f "$T/log"; run b sh "$s/mirror.sh" >/dev/null 2>&1; c=$?
[ "$c" -eq 2 ] && [ ! -f "$T/log" ] && ok "no phone: scrcpy is not started" || bad "scrcpy was started without a phone (exit $c)"
echo "passed $pass, failed $fail"
[ "$fail" -eq 0 ]
