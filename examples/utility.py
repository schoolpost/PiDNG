from pydng.core import RPICAM2DNG
import time, sys, os, getopt

#=========================================================================================================
helptext = '''utility.py - Command line converter from raspberry pi camera JPEG+RAW format to DNG format. 

utility.py <options> <inputFilename> 
Options:
 --help      Display this help message
 --compress  Use Lossless-JPEG compression scheme ( smaller file-size )  
 --dark      Dark frame file location ( only applied if --process )
 --shade     Lens shade frame file location ( only applied if --process )
 --process   Apply dark frame / lens shade processing to the output. ( default false )
   
Examples:
  utility.py color.jpg
  utility.py --process --dark /extras/dark/dark_frame --shade /extras/shade/shade_sun color.jpg
'''


def main():

    inputFilename = None
    width = None
    length = None
    shade = None
    dark = None
    process = False
    compress = False
    
    try:
        options, args = getopt.getopt(sys.argv[1:], '',
            ['help', 'dark', 'shade', 'process', 'compress'])
    except getopt.error:
        print('Error: You tried to use an unknown option.\n')
        print(helptext)
        sys.exit(0)
        
    if len(sys.argv[1:]) == 0:
        sys.exit(0)

    for o, a in options:
        if o in ('--help'):
            print(helptext)
            sys.exit(0)
        
        elif o in ('-s', '--shade'):
            shade = str(a)
            if not isinstance(shade, str) and not os.path.exists(shade):
                print("Invalid file or location!". shade)
                sys.exit(0)

        
        elif o in ('-d', '--dark'):
            dark = str(a)
            if not isinstance(dark, str) and not os.path.exists(dark):
                print("Invalid file or location!". dark)
                sys.exit(0)

        elif o in ('-p', '--process'):
            process=True

        elif o in ('-c', '-compress'):
            compress = True

    if len(args) < 1:
        print("Incorrect Input")
        sys.exit(0)

    elif len(args) == 1:
        inputFilename = args[0]
    else:
        inputFilename = args[0]

    d = RPICAM2DNG()
    d.convert(inputFilename, process=process, compress=compress)

if __name__ == "__main__":
    main()