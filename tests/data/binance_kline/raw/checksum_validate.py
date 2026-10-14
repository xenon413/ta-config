"""Validate every downloaded archive; a mismatch fails the command."""
import hashlib
from pathlib import Path


def main() -> None:
    for checksum in sorted(Path(__file__).parent.glob("*.CHECKSUM")):
        archive = checksum.with_suffix("")
        expected = checksum.read_text().split()[0]
        actual = hashlib.sha256(archive.read_bytes()).hexdigest()
        if actual != expected:
            raise SystemExit(f"Checksum mismatch: {archive.name}")
        print(f"Verified {archive.name}")


if __name__ == "__main__":
    main()
