# Manipulate UEFI variables

The first 4 bytes are flags (little-endian),
followed by a null-terminated string in UTF16-le.


## systemd-boot
UUID: Lo4a67b082-0a4c-41cf-b6c7-440b29bb8c4f
Variable storing default entry: LoaderEntryDefault
Variable storing nextboot (once): LoaderEntryOneShot

Example path: /sys/firmware/efi/efivars/LoaderEntryOneShot-4a67b082-0a4c-41cf-b6c7-440b29bb8c4f

Value is the name of loader entry file without its extension.
e.g. /boot/efi/loader/entries/arch-lts.conf => "arch-lts"


## Read var
raw_val = Path('/sys/firmware/efi/efivars/LoaderEntryDefault-4a67b082-0a4c-41cf-b6c7-440b29bb8c4f').read_bytes()
# flags, = struct.unpack('<L', raw_val[:4])
flags = int.from_bytes(raw_val[:4], byteorder='little')
val = raw_val[4:].decode('utf_16_le')[:-1]


## Common flags

#define EFI_VARIABLE_NON_VOLATILE       0x0000000000000001  # Value is not cleared on reboot/poweroff
#define EFI_VARIABLE_BOOTSERVICE_ACCESS 0x0000000000000002  # Requirement for EFI_VARIABLE_RUNTIME_ACCESS
#define EFI_VARIABLE_RUNTIME_ACCESS     0x0000000000000004  # Accessible by the booted OS 

More variables in [3]
Detailed description in [4]


[1] https://firmware.intel.com/blog/accessing-uefi-variables-linux
[2] https://blog.fpmurphy.com/2012/12/efivars-and-efivarfs.html
[3] https://github.com/torvalds/linux/blob/c4db9c1e8c70bc60e392da8a485bcfb035d559c2/include/linux/efi.h#L1192
[4] http://wiki.phoenix.com/wiki/index.php/EFI_RUNTIME_SERVICES
