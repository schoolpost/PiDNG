import numpy as np

def pack10(data : np.ndarray) -> np.ndarray:
    out = np.zeros((data.shape[0], int(data.shape[1]*(1.25))), dtype=np.uint8)
    out[:, ::5] = data[:, ::4] >> 2
    out[:, 1::5] = ((data[:, ::4] & 0b0000000000000011) << 6)
    out[:, 1::5] += data[:, 1::4] >> 4
    out[:, 2::5] = ((data[:, 1::4] & 0b0000000000001111) << 4)
    out[:, 2::5] += data[:, 2::4] >> 6
    out[:, 3::5] = ((data[:, 2::4] & 0b0000000000111111) << 2)
    out[:, 3::5] += data[:, 3::4] >> 8
    out[:, 4::5] = data[:, 3::4] & 0b0000000011111111
    return out

def pack12(data : np.ndarray) -> np.ndarray:
    out = np.zeros((data.shape[0], int(data.shape[1]*(1.5))), dtype=np.uint8)
    out[:, ::3] = data[:, ::2] >> 4
    out[:, 1::3] = ((data[:, ::2] & 0b0000000000001111) << 4)
    out[:, 1::3] += data[:, 1::2] >> 8
    out[:, 2::3] = data[:, 1::2] & 0b0000001111111111
    return out

def pack14(data : np.ndarray) -> np.ndarray:
    out = np.zeros((data.shape[0], int(data.shape[1]*(1.75))), dtype=np.uint8)
    out[:, ::7] = data[:, ::6] >> 6
    out[:, 1::7] = ((data[:, ::6] & 0b0000000000000011) << 6)
    out[:, 1::7] += data[:, 1::6] >> 8
    out[:, 2::7] = ((data[:, 1::6] & 0b0000000000001111) << 4)
    out[:, 2::7] += data[:, 2::6] >> 6
    out[:, 3::7] = ((data[:, 2::6] & 0b0000000000111111) << 2)
    out[:, 3::7] += data[:, 3::6] >> 8
    out[:, 4::7] = ((data[:, 3::6] & 0b0000000000001111) << 4)
    out[:, 4::7] += data[:, 4::6] >> 6
    out[:, 5::7] = ((data[:, 4::6] & 0b0000000000111111) << 2)
    out[:, 5::7] += data[:, 5::6] >> 8
    out[:, 6::7] = data[:, 5::6] & 0b0000000011111111
    return out