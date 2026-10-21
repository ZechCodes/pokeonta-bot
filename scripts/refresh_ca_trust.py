"""Replace the stock container CA bundle and hashed directory with certifi trust."""
import re
import shutil
import subprocess
from pathlib import Path


def rebuild_ca_store(bundle, directory):
    """Remove every old anchor before rebuilding OpenSSL's default trust store."""
    certificates = re.findall(
        r"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----",
        bundle,
        re.DOTALL,
    )
    if not certificates:
        raise ValueError("Refusing to replace trust with an empty CA bundle")
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)
    for index, certificate in enumerate(certificates):
        (directory / ("root-%04d.pem" % index)).write_text(certificate + "\n")
    subprocess.run(["openssl", "rehash", str(directory)], check=True)
    (directory / "ca-certificates.crt").write_text(bundle)


if __name__ == "__main__":
    import certifi

    rebuild_ca_store(Path(certifi.where()).read_text(), Path("/etc/ssl/certs"))
