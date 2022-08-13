#!/usr/bin/env python3
"""Display UEFI boot entries and choose which one will be the next temporary default"""

import re
import os
import sys
from collections import OrderedDict
from contextlib import suppress
from subprocess import call, check_output

if os.name == 'nt':
    import winreg as reg


class BCDBackend():

    entries = None
    boot_next = None
    boot_default = None

    # constant GUID of {fwbootmgr}
    _FWBOOTMGR = '{a5a30fa2-3d06-4e9f-b5f4-a01df9d1fcba}'

    def __init__(self):
        self._load_entries()

    def _load_entries(self):
        # gather every boot entries
        self.entries = OrderedDict()
        with reg.OpenKey(reg.HKEY_LOCAL_MACHINE, r'BCD00000000\Objects') as objects:
            nb_objects = reg.QueryInfoKey(objects)[0]
            for i in range(nb_objects):
                boot_id = reg.EnumKey(objects, i)
                # skip if this isn't an UEFI Firmware entry
                with reg.OpenKey(objects, boot_id + r'\Description') as desc:
                    # 0x10100002 => {bootmgr} (Windows Boot Manager)
                    # 0x101fffff => other uefi entries
                    if reg.QueryValueEx(desc, 'Type')[0] not in (0x101fffff, 0x10100002):
                        continue
                # 12000004: 'description' field
                with reg.OpenKey(objects, boot_id + r'\Elements\12000004') as namekey:
                    name, _ = reg.QueryValueEx(namekey, r'Element')
                    self.entries[boot_id] = name

        # get boot_default and boot_next if possible
        with reg.OpenKey(reg.HKEY_LOCAL_MACHINE,
                         r'BCD00000000\Objects\\' + self._FWBOOTMGR) as fwkey:
            def try_get_field_value(field):
                with suppress(FileNotFoundError):
                    with reg.OpenKey(fwkey, r'Elements\\' + field) as key:
                        values, _ = reg.QueryValueEx(key, 'Element')
                        return values[0]
            # 24000001 => 'displayorder' and 24000002 => 'bootsequence'
            self.boot_default = try_get_field_value('24000001')
            self.boot_next = try_get_field_value('24000002')

    def set_boot_next(self, boot_id):
        print(r'bcdedit.exe /set {fwbootmgr} bootsequence ' + boot_id)
        return call(r'bcdedit.exe /set {fwbootmgr} bootsequence ' + boot_id)


class EfibootmgrBackend():

    entries = None
    boot_next = None
    boot_default = None

    def __init__(self):
        self._load_entries()

    def _load_entries(self):
        output = (check_output("efibootmgr")
                  .decode(errors='ignore')
                  .splitlines())
        self.entries = OrderedDict()
        for line in output:
            m = re.search(r'Boot([0-9A-F]+)[*] +(.*)\t.*', line)
            if m:
                boot_id, name = m.groups()
                self.entries[boot_id] = name
            elif line.startswith("BootOrder:"):
                self.boot_default = line.split(": ")[1].split(",")[0]
            elif line.startswith("BootNext:"):
                self.boot_next = line.split(": ")[1]

    def set_boot_next(self, boot_id):
        status = call('efibootmgr -q -n'.split() + [boot_id])
        return status


def choose_entry_legacy(efi):
    """Interactive menu to choose the new default entry"""
    print("-- List of entries --")
    entries = sorted(
        efi.entries.items(),
        key=lambda x: x[1].lower()
    )
    for i, (boot_id, entry) in enumerate(entries):
        print("{:2}. {}".format(i+1, entry))

    if efi.boot_next:
        current = efi.entries.get(efi.boot_next)
    elif efi.boot_default:
        current = efi.entries.get(efi.boot_default)
    else:
        current = "none (fallback entry ?)"
    print("\nCurrent entry:", current)

    while 1:
        choice = input("Type the number of the entry you want as default: ")
        try:
            choice = int(choice)
        except ValueError:
            print("You must type the number of the entry.")
            continue
        else:
            if choice < 1 or choice > len(entries):
                print("There is no entry {}.".format(choice))
                continue
            break
    return entries[choice-1][0]


def choose_entry(efi):
    """Interactive menu to choose the new default entry using `pick`"""
    entries = sorted(
        efi.entries.items(),
        key=lambda x: x[1].lower()
    )
    entries_ids = [boot_id for boot_id, _ in entries]

    if efi.boot_next:
        current_index = entries_ids.index(efi.boot_next)
    elif efi.boot_default:
        current_index = entries_ids.index(efi.boot_default)
    else:
        current_index = 0

    import pick
    picker = pick.Picker(
        options=[entry_name for _, entry_name in entries],
        title="Choose next boot entry (press 'q' to abort)",
        indicator='=>',
        default_index=current_index,
    )
    abort_keys = [
        ord('q'),
        27,  # Escape
        3,  # CTRL + C
    ]
    for key in abort_keys:
        picker.register_custom_handler(key, lambda picker: (None, None))
    _, index = picker.start()
    if index is None:
        sys.exit(0)
    return entries_ids[index]


def choose_reboot():
    """Ask the user if he wants to reboot and use adhoc reboot command"""
    while True:
        choice = input("Would you like to reboot now ? [y\\N] ")
        if choice.lower() == 'n' or choice == '':
            return
        elif choice.lower() == 'y':
            break
        else:
            continue

    if os.name == 'nt':
        call('shutdown /r /t 00')
    else:
        call('reboot')


def main():
    if os.name == 'nt':
        efi = BCDBackend()
    else:
        efi = EfibootmgrBackend()

    try:
        boot_next = choose_entry(efi)
    except ImportError:
        boot_next = choose_entry_legacy(efi)
    exit_code = efi.set_boot_next(boot_next)
    if exit_code == 0:
        print(
            "Default entry successfully set to '{}'"
            .format(efi.entries[boot_next])
        )
    else:
        print("\nWarning: an unexpected error occurred, the bootnext entry might not be set.")
    choose_reboot()
    # input("Press ENTER to continue...")


if __name__ == "__main__":
    main()
