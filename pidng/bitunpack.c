#include <Python.h>
#include "liblj92/lj92.h"

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

    if (!PyArg_ParseTuple(args, "y#iiiiiis#i", &input, &inlen,
        &width, &height, &bitdepth,
        &inindex, &inread, &inskip, &delin, &delinlen, &ljPredictor))
        return NULL;

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

    if (ret != LJ92_ERROR_NONE) return NULL;
    Py_END_ALLOW_THREADS;
    PyObject* ba = PyByteArray_FromStringAndSize((char*)encoded,encodedLength);
    free(encoded);
    return ba;
}

static PyMethodDef methods[] = {

    { "unpackljto16", bitunpack_unpackljto16, METH_VARARGS, "Unpack a string of LJPEG values to 16bit values" },
    { "pack16tolj", bitunpack_pack16tolj, METH_VARARGS, "Pack a string of 16bit values to LJPEG" },
    { NULL, NULL, 0, NULL }
};

static struct PyModuleDef ljpegCompress =
{
    PyModuleDef_HEAD_INIT,
    "ljpegCompress", 
    "",          
    -1,          
    methods
};

PyMODINIT_FUNC PyInit_ljpegCompress(void)
{
    return PyModule_Create(&ljpegCompress);
}
