#ifndef ANCHOR_ANP_NUMBER_AS_H
#define ANCHOR_ANP_NUMBER_AS_H

#include "Python.h"
#include "anp_cli.h"

int anpParseNumberAs(PyObject *obj, AnpNumberAs *out);
const char *anpNumberAsToString(AnpNumberAs mode);
PyObject *anpConvertNumberText(AnpNumberAs mode, const char *text);

#endif //ANCHOR_ANP_NUMBER_AS_H
