"""
讓使用者安裝後可以：
    isd-py-framework-sdk -V
    isd-py-framework-sdk --version
"""
from ._version import __version__


def main():
    import argparse

    parser = argparse.ArgumentParser(description="isd-py-framework-sdk CLI")
    parser.add_argument("-V", "--version", action="store_true", help="Show version")
    args = parser.parse_args()

    if args.version:
        print(__version__)
        return

    print(f"isd-py-framework-sdk v{__version__}")
