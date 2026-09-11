#include "anp_number_as.h"
#include "anp_module.h"
#include "anp_exception.h"

#include <stdio.h>
#include <string.h>

#ifdef _WIN32
#  define anp_strcasecmp _stricmp
#else
#  include <strings.h>
#  define anp_strcasecmp strcasecmp
#endif

#define ANP_NUMBER_ERR_TEXT_PREVIEW 120

static void anpFormatNumberConvertError(char *message, size_t messageSize,
                                        const char *text, const char *targetType)
{
    size_t textLen;

    if (text == NULL) {
        text = "";
    }
    textLen = strlen(text);
    if (textLen > ANP_NUMBER_ERR_TEXT_PREVIEW) {
        snprintf(message, messageSize,
                 "cannot convert NUMBER value '%.*s...' to %s when number_as='%s'",
                 ANP_NUMBER_ERR_TEXT_PREVIEW, text, targetType, targetType);
    } else {
        snprintf(message, messageSize,
                 "cannot convert NUMBER value '%s' to %s when number_as='%s'",
                 text, targetType, targetType);
    }
}

int anpParseNumberAs(PyObject *obj, AnpNumberAs *out)
{
    const char *value;

    if (obj == NULL || obj == Py_None) {
        *out = ANP_NUMBER_AS_DECIMAL;
        return 0;
    }

    if (!PyUnicode_Check(obj)) {
        PyErr_SetString(PyExc_TypeError,
                        "number_as must be a string "
                        "('decimal', 'float', 'int', or 'str')");
        return -1;
    }

    value = PyUnicode_AsUTF8(obj);
    if (value == NULL) {
        return -1;
    }

    /* Case-insensitive: decimal/Decimal/DECIMAL, float/float64/FLOAT, etc. */
    if (anp_strcasecmp(value, "decimal") == 0) {
        *out = ANP_NUMBER_AS_DECIMAL;
        return 0;
    }
    if (anp_strcasecmp(value, "float") == 0 ||
        anp_strcasecmp(value, "float64") == 0) {
        *out = ANP_NUMBER_AS_FLOAT;
        return 0;
    }
    if (anp_strcasecmp(value, "int") == 0 ||
        anp_strcasecmp(value, "int64") == 0) {
        *out = ANP_NUMBER_AS_INT;
        return 0;
    }
    if (anp_strcasecmp(value, "str") == 0 ||
        anp_strcasecmp(value, "string") == 0) {
        *out = ANP_NUMBER_AS_STR;
        return 0;
    }

    anpRaiseExceptionFromString(
        anpProgrammingErrorException,
        "invalid number_as value; expected one of: "
        "'decimal', 'float', 'int', 'str' "
        "(aliases: float64, int64, string; case-insensitive)");
    return -1;
}

const char *anpNumberAsToString(AnpNumberAs mode)
{
    switch (mode) {
        case ANP_NUMBER_AS_FLOAT:
            return "float";
        case ANP_NUMBER_AS_INT:
            return "int";
        case ANP_NUMBER_AS_STR:
            return "str";
        case ANP_NUMBER_AS_DECIMAL:
        default:
            return "decimal";
    }
}

static PyObject *anpConvertNumberTextToDecimal(const char *text)
{
    PyObject *stringObj;
    PyObject *result;

    stringObj = PyUnicode_Decode(text, (Py_ssize_t)strlen(text), NULL, NULL);
    if (stringObj == NULL) {
        return NULL;
    }
    result = PyObject_CallFunctionObjArgs((PyObject *)anpPyTypeDecimal, stringObj, NULL);
    Py_DECREF(stringObj);
    return result;
}

static PyObject *anpRaiseNumberConvertDataError(const char *text, const char *targetType)
{
    char message[256];

    anpFormatNumberConvertError(message, sizeof(message), text, targetType);
    return anpRaiseExceptionFromString(anpDataErrorException, message);
}

static PyObject *anpConvertNumberTextToFloat(const char *text)
{
    PyObject *stringObj;
    PyObject *result;
    double value;

    stringObj = PyUnicode_Decode(text, (Py_ssize_t)strlen(text), NULL, NULL);
    if (stringObj == NULL) {
        return NULL;
    }
    result = PyFloat_FromString(stringObj);
    Py_DECREF(stringObj);
    if (result == NULL) {
        PyErr_Clear();
        return anpRaiseNumberConvertDataError(text, "float");
    }

    value = PyFloat_AsDouble(result);
    if (Py_IS_INFINITY(value) || Py_IS_NAN(value)) {
        Py_DECREF(result);
        return anpRaiseNumberConvertDataError(text, "float");
    }
    return result;
}

static PyObject *anpConvertNumberTextToInt(const char *text)
{
    PyObject *dec;
    PyObject *integral;
    int cmp;
    PyObject *result;

    dec = anpConvertNumberTextToDecimal(text);
    if (dec == NULL) {
        PyErr_Clear();
        return anpRaiseNumberConvertDataError(text, "int");
    }

    /*
     * Prefer to_integral_value equality over remainder:
     * accepts 12.00 / 1E+2, rejects 12.34, avoids silent truncation.
     */
    integral = PyObject_CallMethod(dec, "to_integral_value", NULL);
    if (integral == NULL) {
        Py_DECREF(dec);
        PyErr_Clear();
        return anpRaiseNumberConvertDataError(text, "int");
    }

    cmp = PyObject_RichCompareBool(dec, integral, Py_EQ);
    Py_DECREF(integral);
    if (cmp < 0) {
        Py_DECREF(dec);
        PyErr_Clear();
        return anpRaiseNumberConvertDataError(text, "int");
    }
    if (cmp == 0) {
        Py_DECREF(dec);
        return anpRaiseNumberConvertDataError(text, "int");
    }

    result = PyNumber_Long(dec);
    Py_DECREF(dec);
    if (result == NULL) {
        PyErr_Clear();
        return anpRaiseNumberConvertDataError(text, "int");
    }
    return result;
}

PyObject *anpConvertNumberText(AnpNumberAs mode, const char *text)
{
    if (text == NULL) {
        return anpRaiseExceptionFromString(anpInternalErrorException,
                                           "NUMBER text buffer is NULL");
    }

    switch (mode) {
        case ANP_NUMBER_AS_FLOAT:
            return anpConvertNumberTextToFloat(text);
        case ANP_NUMBER_AS_INT:
            return anpConvertNumberTextToInt(text);
        case ANP_NUMBER_AS_STR:
            return PyUnicode_FromString(text);
        case ANP_NUMBER_AS_DECIMAL:
        default:
            return anpConvertNumberTextToDecimal(text);
    }
}
