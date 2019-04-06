import numpy as np
import math

def pack10(data):
    out = np.zeros((data.shape[0], data.shape[1]*(5//4)), dtype=np.uint8)
    out[:,::5] = data[:,::4] >> 2
    out[:,1::5] = ((data[:,::4] & 0b0000000000000011 ) << 6)
    out[:,1::5] += data[:,1::4] >> 4
    out[:,2::5] = ((data[:,1::4] & 0b0000000000001111 ) << 4)
    out[:,2::5] += data[:,2::4] >> 6
    out[:,3::5] = ((data[:,2::4] & 0b0000000000111111 ) << 2)
    out[:,3::5] += data[:,3::4] >> 8
    out[:,4::5] = data[:,3::4] & 0b0000000011111111 
    return out


def pack12(data):
    out = np.zeros((data.shape[0], int(data.shape[1]*(1.5)) ), dtype=np.uint8)
    out[:,::3] = data[:,::2] >> 4
    out[:,1::3] = ((data[:,::2] & 0b0000000000001111 ) << 4)
    out[:,1::3] += data[:,1::2] >> 8
    out[:,2::3] = data[:,1::2] & 0b0000001111111111 
    return out

# TODO
def pack14(data):
    pass





