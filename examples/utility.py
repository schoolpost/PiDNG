from pidng import RPICAM2DNG
import sys, getopt

#=========================================================================================================
helptext = '''utility.py - Command line converter from raspberry pi camera JPEG+RAW format to DNG format. 

Usage:
    utility.py <options> <inputFilename> 

Options:
 --help      Display this help message
 --compress  Use Lossless-JPEG compression scheme ( smaller file-size )  
   
Examples:
    utility.py imx477.jpg
    utility.py -compress imx477.jpg
'''


def main():

    inputFilename = None
    compress = False
    
    try:
        options, args = getopt.getopt(sys.argv[1:], 'hc', ['help','compress'])
    except getopt.error:
        print('Error: You tried to use an unknown option.\n')
        print(helptext)
        sys.exit(0)
            
    if len(sys.argv[1:]) == 0:
        sys.exit(0)

    for opt, arg in options:
        if opt in ('-c', '--compress'):
            compress = True
        elif opt in ('-h', '--help'):
            print(helptext)
            sys.exit(0)

    if len(args) < 1:
        print("Incorrect Input")
        sys.exit(0)    
    elif len(args) == 1:
        inputFilename = args[0]
    else:
        inputFilename = args[0]

    d = RPICAM2DNG()
    d.convert(inputFilename, compress=compress)

if __name__ == "__main__":
    main()