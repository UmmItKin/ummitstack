---
name: open-android-screen
description: Show the screen of a USB-connected Android phone on this computer and look at it, to debug something on the phone. It checks adb and the phone first, and if the phone is not connected it asks the user to connect the cable. Use when the user types /open-android-screen or wants to see, mirror or debug what is on their Android screen.
---

# Open the Android screen

Arguments: $ARGUMENTS
(Claude Code fills these in. In Codex, or if the line above still shows a placeholder, read them from the user's message.)

Goal: put the phone screen on this computer (a live window for the user) and capture it so you can see it too. The default is view only.

## Steps
1. Run `sh <skill-dir>/scripts/android-check.sh`. It checks that `adb` is installed and that exactly one phone is connected and authorized. It never prints a device serial.
   - Exit 0: go ahead.
   - Exit 1, 2, 3 or 4: stop. The script prints what the user has to do (install adb, connect the cable and turn on USB debugging, tap Allow on the phone, or choose one of several phones). Say it in a few lines, then ask once with a single-select menu (AskUserQuestion, or the same two answers in plain text): "Connected and ready, check again" or "Not now". On "check again", run the check again and go ahead when it exits 0. On "Not now", stop.
2. Open the live window: `sh <skill-dir>/scripts/mirror.sh`. It starts `scrcpy` and prints its pid. If it exits 6, scrcpy is not installed: tell the user (Arch: `sudo pacman -S scrcpy`) and carry on with screenshots.
3. See it: `sh <skill-dir>/scripts/screenshot.sh`. It prints the path of a PNG; open that file with the Read tool and say what is on the screen that matters for the problem. Exit 5 means the screen is off: ask the user to wake and unlock the phone, then run it again.
4. If you cannot see it, say so and why (the capture failed, the screen is off, or the app blocks screenshots and the picture is black), and rely on what the user sees in the live window and tells you. Do not try to get around an app that blocks capture.
5. To debug, use read-only commands and keep them narrow, for example `adb logcat -d -t 200`, `adb shell getprop <name>` or `adb shell dumpsys <service>`, and summarize.

## Rules
- View only. Do not tap, type, swipe, install or remove apps, push or pull files, change settings or reboot the phone (`adb shell input`, `adb install`, `adb uninstall`, `adb push`, `adb pull`, `adb reboot`, `adb shell rm`) unless the user asks for that action.
- A screen can show private things: notifications, messages, accounts. Look only at what the problem needs, save screenshots outside any repository (the default is the temp folder), never commit them or send them to another service, and remove a screenshot by its exact path when you are done.
- Never ask the user to share a phone serial or an unlock code. If several phones are connected, the user chooses.
- Logs can hold personal data too. Quote only the lines that matter.
- Do not stop a process by name. The user closes the live window.
