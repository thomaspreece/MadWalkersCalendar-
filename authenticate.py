from parseMADWalks import get_credentials

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

if __name__ == "__main__":
    get_credentials(False)
