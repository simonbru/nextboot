# Nextboot
Choose which OS to boot on next restart from a simple terminal UI. Works on Windows and Linux.

![Screenshot of Nextboot](resources/screenshot.png?raw=true)

## How it works
OS entries are retrieved using `efibootmgr` on Linux and `bcdedit` on Windows.

The `BootNext` UEFI variable is set to selected entry. The firmware resets `BootNext` after booting.


## Requirements
* pick (install with pip)
* efibootmgr
* ncurses (optional)

Windows users can install ncurses [from these wheels](https://www.lfd.uci.edu/~gohlke/pythonlibs/#curses).
A fallback UI is used when ncurses is missing.
