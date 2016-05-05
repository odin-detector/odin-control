#include <iostream>
#include <map>
#include <vector>

#include "femApi.h"
#include "FemApiError.h"
#include "ExcaliburFemClient.h"

std::map<int, std::vector<int> > int_params;

const unsigned int kClientTimeoutMsecs = 10000;

const char* femErrorMsg(void)
{
    return FemApiError::get_string();
}

int femErrorCode(void)
{
    return FemApiError::get_code();
}

void* femInitialise(void* ctlHandle, const CtlCallbacks* callbacks, const CtlConfig* config)
{
    ExcaliburFemClient* theFem = NULL;
    try {
        theFem = new ExcaliburFemClient(ctlHandle, callbacks, config, kClientTimeoutMsecs);
    }
    catch (FemClientException& e)
    {
        FemApiError().Set(e.which()) << "Error trying to initialise FEM id " << config->femNumber << ": " << e.what();
    }

    return (void*)theFem;
}

int femGetInt(void* femHandle, int chipId, int id, size_t size, int* value)
{
    int rc = FEM_RTN_OK;

    //ExcaliburFemClient* theFem = reinterpret_cast<ExcaliburFemClient*>(femHandle);

    if (int_params.count(id) > 0) {
        for (size_t i = 0; i < size; i++) {
            value[i] = int_params[id][i];
        }
    } else {
        for (size_t i = 0; i < size; i++) {
            value[i] = id + i;
        }
    }

    return rc;
}

int femSetInt(void* femHandle, int chipId, int id, size_t size, int* value)
{
    int rc = FEM_RTN_OK;

    int_params[id] = std::vector<int>(value, value + size);

    return rc;
}

int femCmd(void* femHandler, int chipId, int id)
{
    int rc = FEM_RTN_OK;

    //ExcaliburFemClient* theFem = reinterpret_cast<ExcaliburFemClient*>(femHandle);

    switch (id)
    {
        case FEM_OP_STARTACQUISITION:
        case FEM_OP_STOPACQUISITION:
        case FEM_OP_LOADPIXELCONFIG:
        case FEM_OP_FREEALLFRAMES:
        case FEM_OP_LOADDACCONFIG:
        case FEM_OP_FEINIT:
        case FEM_OP_REBOOT:
            // Do nothing for now
            break;

        default:
            rc = FEM_RTN_UNKNOWNOPID;
            FemApiError().Set() << "femCmd: illegal command ID: " << id;
    }

    return rc;
}

int femGetId(void* femHandle)
{
    ExcaliburFemClient* theFem = reinterpret_cast<ExcaliburFemClient*>(femHandle);

    return theFem->get_id();
}

void femClose(void* femHandle)
{
    ExcaliburFemClient* theFem = reinterpret_cast<ExcaliburFemClient*>(femHandle);

    delete theFem;
}
