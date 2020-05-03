from pydng.core import DNGConverter
import time, sys, os, getopt

def main():

    inputFilename = None
    width = None
    length = None
    shade = None
    dark = None
    
    try:
        options, args = getopt.getopt(sys.argv[1:], 'CMpw:l:h:s:d:',
            ['help', 'color', 'packed', 'mono', 'width', 'length', 'height', 'oldpack'])
    except getopt.error:
        print('Error: You tried to use an unknown option.\n\n')
        sys.exit(0)
        
    if len(sys.argv[1:]) == 0:
        sys.exit(0)

    for o, a in options:
        if o in ('--help'):
            sys.exit(0)
        
        elif o in ('-l', '-h', '--length', '--height'):
            length = int(a)

        elif o in ('-w', '--width'):
            width = int(a)

        elif o in ('-s', '--shade'):
            shade = str(a)
        
        elif o in ('-d', '--dark'):
            dark = str(a)

    if len(args) < 1:
        print("help me")
        sys.exit(0)

    elif len(args) == 1:
        inputFilename = args[0]
    else:
        inputFilename = args[0]

    d = DNGConverter()
    d.convert(inputFilename, process=True)

if __name__ == "__main__":
    start_time = time.time()
    main()
    print("--- %s seconds ---" % (time.time() - start_time))