#include <iostream>

#include "ExcaliburFemClient.h"

ExcaliburFemClient::ExcaliburFemClient(int id) :
    id_(id)
{
    // Dummy exception thrown by negative ID
    if (id < 0) {
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
