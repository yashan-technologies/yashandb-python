#ifndef ANCHOR_ANP_CLI_H
#define ANCHOR_ANP_CLI_H

#include "yacapi.h"

extern YapiEnv* anpEnv;

static inline uint32_t codSizeAlign4(uint32_t size)
{
    uint32_t margin = (size & (uint32_t)0x03);
    return (margin == 0) ? size : size + (4 - margin);
}

#define CONVERT_TO_LOB_SIZE (65534)
#define PROCEDURE_PARAM_LIST_BUFFER_SIZE (512)
#define PROCEDURE_SQL_BUFFER_SIZE (1024)
#define NUMBER_STRING_BUFFER_SIZE (65534)
#define NUMBER_FROM_INTEGER_STRING_FMT ("9999999999999999999999999999999999999999999999999999999999999999")
#define NUMBER_FROM_INTEGER_STRING_FMT_STR_LEN (64)
#define LOB_BUFFER_SIZE (256)

/* NUMBER fetch mapping strategy (connect/SessionPool number_as) */
typedef enum AnpNumberAs {
    ANP_NUMBER_AS_DECIMAL = 0,  /* default */
    ANP_NUMBER_AS_FLOAT   = 1,
    ANP_NUMBER_AS_INT     = 2,
    ANP_NUMBER_AS_STR     = 3
} AnpNumberAs;

#endif  // ANCHOR_ANP_CLI_H
