#include <Python.h>

#include "liblj92/lj92.h"

void demosaic(
    float** rawData,    /* holds preprocessed pixel values, rawData[i][j] corresponds to the ith row and jth column */
    float** red,        /* the interpolated red plane */
    float** green,      /* the interpolated green plane */
    float** blue,       /* the interpolated blue plane */
    int winx, int winy, /* crop window for demosaicing */
    int winw, int winh,
    int cfa 
);

static PyObject*
bitunpack_demosaic14(PyObject* self, PyObject *args)
{
    unsigned const char* input = 0;
    int length = 0;
    int width = 0;
    int height = 0;
    int black = 2000;
    int byteSwap = 0;
    if (!PyArg_ParseTuple(args, "t#iiii", &input, &length, &width, &height, &black, &byteSwap))
        return NULL;
    //printf("width %d height %d\n",width,height);
    PyObject* ba = PyByteArray_FromStringAndSize("",0);
    int elements = length*8/14;
    PyByteArray_Resize(ba,elements*12); // Demosaiced as RGB 32bit float data

    // Convert 14bit packed to data to 32bit RAW float data, not demosaiced
    float* raw = (float*)malloc(elements*sizeof(float));
    float** rrows = (float**)malloc(height*sizeof(float*));
    int rr = 0;
    for (;rr<height;rr++) {
        rrows[rr] = raw + rr*width;
    }

    int i = 0;
    int sparebits = 0;
    unsigned int acc = 0;
    unsigned int out = 0;
    short unsigned int* read = (short unsigned int*)input;
    float* write = raw;
    //printf("Decoding frame\n");

    while (i<elements) {
        if (sparebits<14) {
            short unsigned int r = *read++;
            if (byteSwap)
                r = (r&0xFF00)>>8 | ((r&0x00FF)<<8);
            acc |= r;
            sparebits += 2;
            out = (acc>>sparebits)&0x3FFF;
        } else {
            sparebits += 2;
            out = (acc>>sparebits)&0x3FFF;
            sparebits = 0;
            acc = 0;
        }
        if (out==0) { // Dead pixel masking
            float old = *(write-2);
            *write++ = old;
        } else {
            int ival = out-black;
            // To avoid artifacts from demosaicing at low levels
            ival += 15.0;
            if (ival<15) ival=15; // Don't want log2(0)

            float val = (float)ival;//64.0*log2((float)ival);
            *write++ = val;
        }
        acc = (acc&((1<<sparebits)-1))<<16;
        i++;
    }

    // Now demosaic with CPU
    float* red = malloc(elements*sizeof(float));
    float** redrows = (float**)malloc(height*sizeof(float*));
    for (rr=0;rr<height;rr++) {
        redrows[rr] = red + rr*width;
    }
    float* green = malloc(elements*sizeof(float));
    float** greenrows = (float**)malloc(height*sizeof(float*));
    for (rr=0;rr<height;rr++) {
        greenrows[rr] = green + rr*width;
    }
    float* blue = malloc(elements*sizeof(float));
    float** bluerows = (float**)malloc(height*sizeof(float*));
    for (rr=0;rr<height;rr++) {
        bluerows[rr] = blue + rr*width;
    }

    demosaic(rrows,redrows,greenrows,bluerows,0,0,width,height,0);

    // Now interleave into final RGB float array
    float* outptr = (float*)PyByteArray_AS_STRING(ba);
    float* rptr = red;
    float* gptr = green;
    float* bptr = blue;
    for (rr=0;rr<elements;rr++) {
           *outptr++ = (*rptr++);
           *outptr++ = (*gptr++);
           *outptr++ = (*bptr++);
    }
    free(raw);
    free(rrows);
    free(red);
    free(redrows);
    free(green);
    free(greenrows);
    free(blue);
    free(bluerows);

    return ba;
}

static PyObject*
bitunpack_demosaic16(PyObject* self, PyObject *args)
{
    unsigned const char* input = 0;
    int length = 0;
    int width = 0;
    int height = 0;
    int black = 2000;
    int byteSwap = 0;
    if (!PyArg_ParseTuple(args, "t#iiii", &input, &length, &width, &height, &black, &byteSwap))
        return NULL;
    //printf("width %d height %d\n",width,height);
    PyObject* ba = PyByteArray_FromStringAndSize("",0);
    int elements = length/2;
    PyByteArray_Resize(ba,elements*12); // Demosaiced as RGB 32bit float data

    // Convert 14bit packed to data to 32bit RAW float data, not demosaiced
    float* raw = (float*)malloc(elements*sizeof(float));
    float** rrows = (float**)malloc(height*sizeof(float*));
    int rr = 0;
    for (;rr<height;rr++) {
        rrows[rr] = raw + rr*width;
    }

    int i = 0;
    unsigned int out = 0;
    short unsigned int* read = (short unsigned int*)input;
    float* write = raw;
    //printf("Decoding frame\n");

    while (i<elements) {
        short unsigned int r = *read++;
        if (byteSwap)
            r = (r&0xFF00)>>8 | ((r&0x00FF)<<8);
        out = r;
        if (out==0) { // Dead pixel masking
            float old = *(write-2);
            *write++ = old;
        } else {
            int ival = out-black;
            // To avoid artifacts from demosaicing at low levels
            ival += 15.0;
            if (ival<15) ival=15; // Don't want log2(0)

            float val = (float)ival;//64.0*log2((float)ival);
            *write++ = val;
        }
        i++;
    }

    // Now demosaic with CPU
    float* red = malloc(elements*sizeof(float));
    float** redrows = (float**)malloc(height*sizeof(float*));
    for (rr=0;rr<height;rr++) {
        redrows[rr] = red + rr*width;
    }
    float* green = malloc(elements*sizeof(float));
    float** greenrows = (float**)malloc(height*sizeof(float*));
    for (rr=0;rr<height;rr++) {
        greenrows[rr] = green + rr*width;
    }
    float* blue = malloc(elements*sizeof(float));
    float** bluerows = (float**)malloc(height*sizeof(float*));
    for (rr=0;rr<height;rr++) {
        bluerows[rr] = blue + rr*width;
    }

    Py_BEGIN_ALLOW_THREADS;
    demosaic(rrows,redrows,greenrows,bluerows,0,0,width,height,0);
    Py_END_ALLOW_THREADS;

    // Now interleave into final RGB float array
    float* outptr = (float*)PyByteArray_AS_STRING(ba);
    float* rptr = red;
    float* gptr = green;
    float* bptr = blue;
    for (rr=0;rr<elements;rr++) {
           *outptr++ = (*rptr++);
           *outptr++ = (*gptr++);
           *outptr++ = (*bptr++);
    }
    free(raw);
    free(rrows);
    free(red);
    free(redrows);
    free(green);
    free(greenrows);
    free(blue);
    free(bluerows);

    return ba;
}

typedef struct _demosaicer {
    int width;
    int height;
    float* raw;
    float** rrows;
    float* red;
    float** redrows;
    float* green;
    float** greenrows;
    float* blue;
    float** bluerows;
} demosaicer;

const char* DEMOSAICER_NAME = "demosaicer";
static void
bitunpack_freedemosaicer(PyObject* self)
{
    demosaicer* dem = (demosaicer*)PyCapsule_GetPointer(self,DEMOSAICER_NAME);
    if (dem == NULL)
        return;
    free(dem->raw);
    free(dem->rrows);
    free(dem->red);
    free(dem->redrows);
    free(dem->green);
    free(dem->greenrows);
    free(dem->blue);
    free(dem->bluerows);
    free(dem);
}

static PyObject*
bitunpack_demosaicer(PyObject* self, PyObject *args)
{
    int width = 0;
    int height = 0;
    if (!PyArg_ParseTuple(args, "ii", &width, &height))
        return NULL;

    int elements = width*height;

    demosaicer* dem = (demosaicer*)calloc(1,sizeof(demosaicer));
    dem->width = width;
    dem->height = height;
    dem->raw = (float*)malloc(elements*sizeof(float));
    dem->rrows = (float**)malloc(dem->height*sizeof(float*));
    int rr = 0;
    for (;rr<dem->height;rr++) {
        dem->rrows[rr] = dem->raw + rr*dem->width;
    }
    dem->red = malloc(elements*sizeof(float));
    dem->redrows = (float**)malloc(dem->height*sizeof(float*));
    for (rr=0;rr<dem->height;rr++) {
        dem->redrows[rr] = dem->red + rr*dem->width;
    }
    dem->green = malloc(elements*sizeof(float));
    dem->greenrows = (float**)malloc(dem->height*sizeof(float*));
    for (rr=0;rr<dem->height;rr++) {
        dem->greenrows[rr] = dem->green + rr*dem->width;
    }
    dem->blue = malloc(elements*sizeof(float));
    dem->bluerows = (float**)malloc(dem->height*sizeof(float*));
    for (rr=0;rr<dem->height;rr++) {
        dem->bluerows[rr] = dem->blue + rr*dem->width;
    }

    return PyCapsule_New(dem,DEMOSAICER_NAME,bitunpack_freedemosaicer);
}

static PyObject*
bitunpack_predemosaic12(PyObject* self, PyObject *args)
{
    unsigned const char* input = 0;
    int length = 0;
    int width = 0;
    int height = 0;
    int black = 2000;
    int byteSwap = 0;
    PyObject* demosaicerobj;
    if (!PyArg_ParseTuple(args, "Ot#iiii", &demosaicerobj, &input, &length, &width, &height, &black, &byteSwap))
        return NULL;
    demosaicer* dem = (demosaicer*)PyCapsule_GetPointer(demosaicerobj,DEMOSAICER_NAME);
    if (dem == NULL)
        return NULL;
    if (dem->width != width || dem->height != height)
        return NULL;

    int elements = (width*height*3)/2;
    int i = 0;
    unsigned int out = 0;
    unsigned char* read = (unsigned char*)input;
    float* write = dem->raw;

    Py_BEGIN_ALLOW_THREADS;
    while (i<elements) {
        unsigned int r1 = *read++;
        unsigned int r2 = *read++;
        unsigned int r3 = *read++;
        out = (r1<<4)|(r2>>4);
        if (out==0) { // Dead pixel masking
            float old = *(write-2);
            *write++ = old;
        } else {
            int ival = out-black;
            // To avoid artifacts from demosaicing at low levels
            ival += 15.0;
            if (ival<15) ival=15; // Don't want log2(0)

            float val = (float)ival;//64.0*log2((float)ival);
            *write++ = val;
        }
        out = ((r2&0xF)<<8)|r3;
        if (out==0) { // Dead pixel masking
            float old = *(write-2);
            *write++ = old;
        } else {
            int ival = out-black;
            // To avoid artifacts from demosaicing at low levels
            ival += 15.0;
            if (ival<15) ival=15; // Don't want log2(0)

            float val = (float)ival;//64.0*log2((float)ival);
            *write++ = val;
        }
        i+=3;
    }
    Py_END_ALLOW_THREADS;
    Py_RETURN_NONE;
}

static PyObject*
bitunpack_predemosaic14(PyObject* self, PyObject *args)
{
    unsigned const char* input = 0;
    int length = 0;
    int width = 0;
    int height = 0;
    int black = 2000;
    int byteSwap = 0;
    PyObject* demosaicerobj;
    if (!PyArg_ParseTuple(args, "Ot#iiii", &demosaicerobj, &input, &length, &width, &height, &black, &byteSwap))
        return NULL;
    demosaicer* dem = (demosaicer*)PyCapsule_GetPointer(demosaicerobj,DEMOSAICER_NAME);
    if (dem == NULL)
        return NULL;
    if (dem->width != width || dem->height != height)
        return NULL;

    int elements = width * height;
    int i = 0;
    int sparebits = 0;
    unsigned int acc = 0;
    unsigned int out = 0;
    short unsigned int* read = (short unsigned int*)input;
    float* write = dem->raw;

    Py_BEGIN_ALLOW_THREADS;
    while (i<elements) {
        if (sparebits<14) {
            short unsigned int r = *read++;
            if (byteSwap) 
                r = (r&0xFF00)>>8 | ((r&0x00FF)<<8);
            acc |= r;
            sparebits += 2;
            out = (acc>>sparebits)&0x3FFF;
        } else {
            sparebits += 2;
            out = (acc>>sparebits)&0x3FFF;
            sparebits = 0;
            acc = 0;
        }
        if (out==0) { // Dead pixel masking
            float old = *(write-2);
            *write++ = old;
        } else {
            int ival = out-black;
            // To avoid artifacts from demosaicing at low levels
            ival += 15.0;
            if (ival<15) ival=15; // Don't want log2(0)

            float val = (float)ival;//64.0*log2((float)ival);
            *write++ = val;
        }
        acc = (acc&((1<<sparebits)-1))<<16;
        i++;
    }
    Py_END_ALLOW_THREADS;
    Py_RETURN_NONE;
}

static PyObject*
bitunpack_predemosaic16(PyObject* self, PyObject *args)
{
    unsigned const char* input = 0;
    int length = 0;
    int width = 0;
    int height = 0;
    int black = 2000;
    int byteSwap = 0;
    PyObject* demosaicerobj;
    if (!PyArg_ParseTuple(args, "Ot#iiii", &demosaicerobj, &input, &length, &width, &height, &black, &byteSwap))
        return NULL;
    demosaicer* dem = (demosaicer*)PyCapsule_GetPointer(demosaicerobj,DEMOSAICER_NAME);
    if (dem == NULL)
        return NULL;
    if (dem->width != width || dem->height != height)
        return NULL;

    int elements = width*height;
    int i = 0;
    unsigned int out = 0;
    short unsigned int* read = (short unsigned int*)input;
    float* write = dem->raw;
    //printf("Decoding frame\n");

    Py_BEGIN_ALLOW_THREADS;
    while (i<elements) {
        short unsigned int r = *read++;
        if (byteSwap)
            r = (r&0xFF00)>>8 | ((r&0x00FF)<<8);
        out = r;
        if (out==0) { // Dead pixel masking
            float old = *(write-2);
            *write++ = old;
        } else {
            int ival = out-black;
            // To avoid artifacts from demosaicing at low levels
            ival += 15.0;
            if (ival<15) ival=15; // Don't want log2(0)

            float val = (float)ival;//64.0*log2((float)ival);
            *write++ = val;
        }
        i++;
    }
    Py_END_ALLOW_THREADS;
    Py_RETURN_NONE;
}

static PyObject*
bitunpack_demosaic(PyObject* self, PyObject *args)
{
    PyObject* demosaicerobj;
    int x;
    int y;
    int width;
    int height;
    int cfa = 0;
    if (!PyArg_ParseTuple(args, "Oiiiii", &demosaicerobj, &x, &y, &width, &height, &cfa))
        return NULL;
    demosaicer* dem = (demosaicer*)PyCapsule_GetPointer(demosaicerobj,DEMOSAICER_NAME);
    if (dem == NULL)
        return NULL;

    Py_BEGIN_ALLOW_THREADS;
    demosaic(dem->rrows,dem->redrows,dem->greenrows,dem->bluerows,x,y,width,height,cfa);
    Py_END_ALLOW_THREADS;
    Py_RETURN_NONE;
}

static PyObject*
bitunpack_postdemosaic(PyObject* self, PyObject *args)
{
    PyObject* demosaicerobj;
    if (!PyArg_ParseTuple(args, "O", &demosaicerobj))
        return NULL;
    demosaicer* dem = (demosaicer*)PyCapsule_GetPointer(demosaicerobj,DEMOSAICER_NAME);
    if (dem == NULL)
        return NULL;

    PyObject* ba = PyByteArray_FromStringAndSize("",0);
    int elements = dem->width * dem->height;
    int resres = PyByteArray_Resize(ba,elements*12); // Demosaiced as RGB 32bit float data
    if (resres < 0) return NULL;
    // Now interleave into final RGB float array
    float* outptr = (float*)PyByteArray_AS_STRING(ba);
    float* rptr = dem->red;
    float* gptr = dem->green;
    float* bptr = dem->blue;
    int rr;
    for (rr=0;rr<elements;rr++) {
           *outptr++ = (*rptr++);
           *outptr++ = (*gptr++);
           *outptr++ = (*bptr++);
    }
    return ba;
}

static PyObject*
bitunpack_unpack12to16(PyObject* self, PyObject *args)
{
    unsigned const char* input = 0;
    int length = 0;
    int byteSwap = 0;
    if (!PyArg_ParseTuple(args, "t#i", &input, &length, &byteSwap))
        return NULL;
    PyObject* ba = PyByteArray_FromStringAndSize("",0);
    int elements = length;
    PyByteArray_Resize(ba,(elements*4)/3);
    unsigned char* baptr = (unsigned char*)PyByteArray_AS_STRING(ba);
    int i = 0;
    unsigned int out = 0;
    unsigned char* read = (unsigned char*)input;
    short unsigned int* write = (short unsigned int*)baptr;
    Py_BEGIN_ALLOW_THREADS;
    while (i<elements) {
        unsigned char r1 = *read++;
        unsigned char r2 = *read++;
        unsigned char r3 = *read++;
        out = (r1<<4)|(r2>>4);
        if (out==0) out = *(write-2); // Dead pixel masking
        *write++ = out;
        out = ((r2&0xF)<<8)|r3;
        if (out==0) out = *(write-2); // Dead pixel masking
        *write++ = out;
        i+=3;
    }
    Py_END_ALLOW_THREADS;
    PyObject *stat = Py_BuildValue("II",0,0);
    PyObject *rslt = PyTuple_New(2);
    PyTuple_SetItem(rslt, 0, ba);
    PyTuple_SetItem(rslt, 1, stat);
    return rslt;
}

static PyObject*
bitunpack_unpack14to16(PyObject* self, PyObject *args)
{
    unsigned const char* input = 0;
    int length = 0;
    int byteSwap = 0;
    if (!PyArg_ParseTuple(args, "t#i", &input, &length, &byteSwap))
        return NULL;
    PyObject* ba = PyByteArray_FromStringAndSize("",0);
    int elements = length*8/14;
    PyByteArray_Resize(ba,elements*2);
    unsigned char* baptr = (unsigned char*)PyByteArray_AS_STRING(ba);
    int i = 0;
    int sparebits = 0;
    unsigned int acc = 0;
    unsigned int out = 0;
    short unsigned int* read = (short unsigned int*)input;
    short unsigned int* write = (short unsigned int*)baptr;
    //printf("Decoding frame\n");

    Py_BEGIN_ALLOW_THREADS;
    while (i<elements) {
        if (sparebits<14) {
            short unsigned int r = *read++;
            if (byteSwap) 
                r = (r&0xFF00)>>8 | ((r&0x00FF)<<8);
            acc |= r;
            sparebits += 2;
            out = (acc>>sparebits)&0x3FFF;
        } else {
            sparebits += 2;
            out = (acc>>sparebits)&0x3FFF;
            sparebits = 0;
            acc = 0;
        }
        if (out==0) out = *(write-2); // Dead pixel masking
        *write++ = out;
        acc = (acc&((1<<sparebits)-1))<<16;
        i++;
    }
    Py_END_ALLOW_THREADS;
    PyObject *stat = Py_BuildValue("II",0,0);
    PyObject *rslt = PyTuple_New(2);
    PyTuple_SetItem(rslt, 0, ba);
    PyTuple_SetItem(rslt, 1, stat);
    return rslt;
}

static PyObject*
bitunpack_unpackljto16(PyObject* self, PyObject *args)
{
    unsigned const char* input = 0;
    int inlen = 0;
    char* output;
    int outlen = 0;
    int outindex = 0;
    int outwrite = 0;
    int outskip = 0;
    unsigned const char* lin = 0;
    int linlen = 0;

    if (!PyArg_ParseTuple(args, "t#w#iiit#", &input, &inlen, &output, &outlen,
        &outindex, &outwrite, &outskip, &lin, &linlen))
        return NULL;
    //printf("ljpeg decode inlen=%d,outlen=%d,outindex=%d,outwrite=%d,outskip=%d,linlen=%d\n",inlen,outlen,outindex,outwrite,outskip,linlen);
    int ret = 0;
    lj92 ljp;
    int iw,ih,ib;
    Py_BEGIN_ALLOW_THREADS;
    ret = lj92_open(&ljp,(uint8_t*)input,inlen,&iw,&ih,&ib);
    //printf("JPEG w:%d,h:%d,bits:%d\n",iw,ih,ib);
    if (ret==LJ92_ERROR_NONE) {
        if (linlen>0) {
            lj92_decode(ljp,(uint16_t*)(output+outindex),outwrite,outskip,(uint16_t*)lin,linlen);
        } else {
            lj92_decode(ljp,(uint16_t*)(output+outindex),outwrite,outskip,NULL,0);
        }
        //printf("Decoding complete\n");
    }
    Py_END_ALLOW_THREADS;
    PyObject *stat = Py_BuildValue("I",ret);
    return stat;
}

static PyObject*
bitunpack_pack16tolj(PyObject* self, PyObject *args)
{
    unsigned const char* input = 0;
    int inlen = 0;
    int width = 0;
    int height = 0;
    int bitdepth = 0;
    int inindex = 0;
    int inread = 0;
    int inskip = 0;
    unsigned const char* delin = 0;
    int delinlen = 0;
    int ljPredictor = 6;

    if (!PyArg_ParseTuple(args, "t#iiiiiit#i", &input, &inlen,
        &width, &height, &bitdepth,
        &inindex, &inread, &inskip, &delin, &delinlen, &ljPredictor))
        return NULL;

    //printf("width=%d,height=%d,inlen=%d\n",width,height,inlen);
    if (width*height*sizeof(uint16_t) > inlen) return NULL;

    int ret = 0;
    uint8_t* encoded;
    int encodedLength;
    Py_BEGIN_ALLOW_THREADS;
    if (delinlen == 0) {
        ret = lj92_encode((uint16_t*)&input[inindex],width,height,bitdepth,
                inread,inskip,NULL,0,&encoded,&encodedLength,ljPredictor);
    } else {
        ret = lj92_encode((uint16_t*)&input[inindex],width,height,bitdepth,
                inread,inskip,(uint16_t*)delin,delinlen,&encoded,&encodedLength,ljPredictor);
    }
    //printf("lj92_encode ret=%d\n",ret);
    if (ret != LJ92_ERROR_NONE) return NULL;
    Py_END_ALLOW_THREADS;
    PyObject* ba = PyByteArray_FromStringAndSize((char*)encoded,encodedLength);
    free(encoded);
    return ba;
}

static PyMethodDef methods[] = {
    { "unpack14to16", bitunpack_unpack14to16, METH_VARARGS, "Unpack a string of 14bit values to 16bit values" },
    { "unpack12to16", bitunpack_unpack12to16, METH_VARARGS, "Unpack a string of 12bit values to 16bit values" },
    { "unpackljto16", bitunpack_unpackljto16, METH_VARARGS, "Unpack a string of LJPEG values to 16bit values" },
    { "pack16tolj", bitunpack_pack16tolj, METH_VARARGS, "Pack a string of 16bit values to LJPEG" },
    { "demosaic14", bitunpack_demosaic14, METH_VARARGS, "Demosaic a 14bit RAW image into RGB float" },
    { "demosaic16", bitunpack_demosaic16, METH_VARARGS, "Demosaic a 16bit RAW image into RGB float" },
    { "demosaicer", bitunpack_demosaicer, METH_VARARGS, "Create a demosaicer object" },
    { "predemosaic12", bitunpack_predemosaic12, METH_VARARGS, "Prepare to demosaic a 12bit RAW image into RGB float" },
    { "predemosaic14", bitunpack_predemosaic14, METH_VARARGS, "Prepare to demosaic a 14bit RAW image into RGB float" },
    { "predemosaic16", bitunpack_predemosaic16, METH_VARARGS, "Prepare to demosaic a 16bit RAW image into RGB float" },
    { "demosaic", bitunpack_demosaic, METH_VARARGS, "Do a unit of demosaicing work (can be from any thread." },
    { "postdemosaic", bitunpack_postdemosaic, METH_VARARGS, "Complete a demosaicing job. Returns the image." },

    { NULL, NULL, 0, NULL }
};

PyMODINIT_FUNC
initbitunpack(void)
{
    PyObject* m;

    m = Py_InitModule("bitunpack", methods);
    if (m == NULL)
        return;
    PyModule_AddStringConstant(m,"__version__","3.0");
}

