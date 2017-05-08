from titanembeds import Titan
import gc

def main():
    print("Starting...")
    te = Titan()
    te.run()
    gc.collect()

if __name__ == '__main__':
    main()
