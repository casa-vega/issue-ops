from base64 import b64encode
from nacl import encoding, public

def encrypt(public_key: str, secret_value: str) -> str:
  """Encrypt a Unicode string using the public key."""
  public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
  sealed_box = public.SealedBox(public_key)
  encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
  return b64encode(encrypted).decode("utf-8")

def parse_arguments() -> argparse.Namespace:
    """
    Parses command-line arguments.

    Returns
    -------
    argparse.Namespace
        The parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Encrypt a secret using a public key."
    )
    parser.add_argument(
        "--public-key",
        required=True,
        help="The public key to use for encryption.",
    )
    parser.add_argument(
        "--secret-value",
        required=True,
        help="The secret value to encrypt.",
    )
    return parser.parse_args()

def main():
    args = parse_arguments()
    args.func(args)
    print(encrypt(args.public_key, args.secret_value))

if __name__ == "__main__":
    main()