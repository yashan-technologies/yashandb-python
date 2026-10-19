
#ifndef ANCHOR_ANP_CONNECTION_H
#define ANCHOR_ANP_CONNECTION_H

#include "Python.h"
#include "anp_cli.h"

struct StAnpCursor;

typedef struct {
    PyObject_HEAD
    YapiConnect *hConn;
    YapiConnectPool *hConnPool;
    PyObject *username;
    PyObject *dsn;

    bool autocommit;
    AnpNumberAs numberAs;
    /* Intrusive list of open cursors (not a Python ref; broken on close/free). */
    struct StAnpCursor *openCursors;
} AnpConnection;

YapiResult anpRegistConnection(PyObject* module);
int        anpGetModule(PyTypeObject* type, PyObject** module, PyObject** name);
bool       anpConnectionIsConnected(AnpConnection* conn);
PyObject*  anpNewConnection(PyTypeObject* type, PyObject* args, PyObject* keywordArgs);

void anpConnectionRegisterCursor(AnpConnection *conn, struct StAnpCursor *cursor);
void anpConnectionUnregisterCursor(AnpConnection *conn, struct StAnpCursor *cursor);
/* Release stmts and null hStmt on all open cursors before GiveBack/Disconnect. */
void anpConnectionInvalidateCursors(AnpConnection *conn);

extern PyTypeObject anchorPyTypeConnection;

#endif //ANCHOR_ANP_CONNECTION_H
