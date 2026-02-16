import argparse
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

def generate_keypair(out_priv: str, out_pub: str):
    priv = Ed25519PrivateKey.generate()
    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub = priv.public_key()
    pub_pem = pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    with open(out_priv, "wb") as f:
        f.write(priv_pem)
    with open(out_pub, "wb") as f:
        f.write(pub_pem)

def main():
    p = argparse.ArgumentParser(prog="python -m inneri.keys")
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate", help="Generate Ed25519 keypair")
    g.add_argument("--out", required=True, help="Private key PEM path")
    g.add_argument("--pub", required=True, help="Public key PEM path")
    args = p.parse_args()

    if args.cmd == "generate":
        generate_keypair(args.out, args.pub)
        print(f"Wrote {args.out} and {args.pub}")

if __name__ == "__main__":
    main()
