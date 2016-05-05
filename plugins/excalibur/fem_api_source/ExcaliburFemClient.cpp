#include <iostream>

#include "ExcaliburFemClient.h"

ExcaliburFemClient::ExcaliburFemClient(void* aCtlHandle, const CtlCallbacks* aCallbacks,
			const CtlConfig* aConfig, unsigned int aTimeoutInMsecs) :
    id_(aConfig->femNumber)
{
    // Dummy exception thrown by negative ID
    if (id_ < 0) {
        throw FemClientException((FemClientErrorCode)30000, "Illegal ID specified");
    }
    //std::cout << "ExcaliburFemClient constructor with id=" << id_ << std::endl;
}

ExcaliburFemClient::~ExcaliburFemClient()
{
    //std::cout << "ExcaliburFemClient destructor for id=" << id_ << std::endl;
}

int ExcaliburFemClient::get_id() {
    return id_;
}
