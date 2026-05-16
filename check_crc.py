import zlib

# перепроверка crc для душевного спокойствия :,)
def get_crc32(filepath):
    with open(filepath, "rb") as f:
        checksum = 0
        while chunk := f.read(8192):
            checksum = zlib.crc32(chunk, checksum)
    return f"0x{checksum & 0xffffffff:08x}"

file_hash = get_crc32("data.txt")
print(f"CRC32 файла: {file_hash}")

if file_hash == "0x2c083a45":
    print("Всё отлично! Файл оригинальный.")
else:
    print("Внимание! Файл изменен или поврежден.")
    sys.exit(1)