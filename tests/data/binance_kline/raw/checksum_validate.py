import hashlib

TARGET = r"tests\data\raw\BTCUSDC-1m-2026-06-13.zip"
CHECKSUM = r"tests\data\raw\BTCUSDC-1m-2026-06-13.zip.CHECKSUM"

# generator for reading data
def read_file_chunks(file_path, chunk_size=4096):
    """Generator that yields chunks of a file in binary mode."""
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk


if __name__ == "__main__":
    # calculate teh sha-256 hash
    sha256_hash = hashlib.sha256()
    for byte_block in read_file_chunks(TARGET):
        sha256_hash.update(byte_block)

    calc_hash = sha256_hash.hexdigest()

    # read the checksum
    with open(CHECKSUM, "r", encoding="utf-8") as f:
        checksum_content = f.read().strip()

    # 3. Clean and format the terminal output
    print("=" * 60)
    print("DATA INTEGRITY VERIFICATION")
    print("=" * 60)
    print(f"Target File:    {TARGET}")
    print(f"Expected Hash:  {checksum_content.split()[0]}")
    print(f"Calculated Hash: {calc_hash}")
    print("-" * 60)

    # 4. Perform validation
    if calc_hash == checksum_content.split()[0]:
        print("Validation SUCCESS: The file integrity is verified.")
    else:
        print("Validation FAILED: The file is corrupted or modified.")
    print("=" * 60)
