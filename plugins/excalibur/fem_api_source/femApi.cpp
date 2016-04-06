#include <iostream>
#include <string>
#include <sstream>

#include "femApi.h"
#include "ExcaliburFemClient.h"

static std::string error_string;
static FemErrorCode error_code = 0;

const char* femErrorMsg(void)
{
    return error_string.c_str();
}

int femErrorCode(void)
{
    return (int)error_code;
}

void* femInitialise(int id)
{
    ExcaliburFemClient* theFem = NULL;
    try {
        theFem = new ExcaliburFemClient(id);
    }
    catch (FemClientException& e)
    {
        error_code = e.which();
        std::stringstream ss;
        ss << "Error trying to initialise FEM id " << id << ": " << e.what();
        error_string = ss.str();
    }

    return (void*)theFem;
}

int femGetInt(void* femHandle, int chipId, int id, size_t size, int* value)
{
    int rc = FEM_RTN_OK;

    //ExcaliburFemClient* theFem = reinterpret_cast<ExcaliburFemClient*>(femHandle);

    for (int i = 0; i < size; i++) {
        value[i] = id + i;
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
