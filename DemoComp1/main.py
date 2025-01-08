import sys
import src.RTD_Logger as greeter

def main():
    args = sys.argv[1:]
    print(greeter.get_greeting(" ".join(args)))

if __name__ == "__main__":
    main()
