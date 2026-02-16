import sys
from .keys import main as keys_main

def main():
    # simple CLI router
    if len(sys.argv) >= 2 and sys.argv[1] == "keys":
        sys.argv.pop(1)
        return keys_main()
    print("Usage: python -m inneri keys generate --out priv.pem --pub pub.pem")

if __name__ == "__main__":
    main()
