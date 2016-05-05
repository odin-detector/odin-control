#include "femApi.h"
#include "FemException.h"

typedef enum
{
        femClientOK = 0,                    ///< OK
        femClientDisconnected = 10000,      ///< Client disconnected by peer
        femClientTimeout,                   ///< Timeout occurred on a socket operation
        femClientResponseMismatch,           ///< Mismatch between requested command and response
        femClientMissingAck,                ///< Transaction command was not acknowledged in reponse
        femClientSendMismatch,              ///< Mismatch in length of send operation
        femClientReadMismatch,              ///< Mismatch in requested versus received access in read transaction
        femClientWriteMismatch,             ///< Mismatch in requested versus acknowledged access in write transaction
        femClientIllegalSensor,             ///< Illegal sensor specified in tempSensorRead call
        femClientNextEnumRange = 20000      ///< Next enum range to use for derived class exceptions
} FemClientErrorCode;

class FemClientException: public FemException
{
public:
        FemClientException(const std::string aExText): FemException(aExText) { };
        FemClientException(const FemClientErrorCode aExCode, const std::string aExText) :
                FemException((FemErrorCode)aExCode, aExText) { };
};

typedef enum
{
        excaliburFemClientIllegalDacId = femClientNextEnumRange,
        excaliburFemClientIllegalConfigId,
        excaliburFemClientIllegalChipId,
        excaliburFemClientIllegalConfigSize,
        excaliburFemClientIllegalCounterDepth,
        excaliburFemClientOmrTransactionTimeout,
        excaliburFemClientUdpSetupFailed,
        excaliburFemClientDataReceviverSetupFailed,
        excaliburFemClientIllegalOperationMode,
        excaliburFemClientIllegalCounterSelect,
        excaliburFemClientBufferAllocateFailed,
        excaliburFemClientPersonalityStatusError,
        excaliburFemClientBadDacScanParameters,
        excaliburFemClientMissingScanFunction,
        excaliburFemClientIllegalTriggerMode,
        excaliburFemClientIllegalTriggerPolarity,
        excaliburFemClientIllegalReadWriteMode,

} ExcaliburFemClientErrorCode;


class ExcaliburFemClient{
public:

    ExcaliburFemClient(void* aCtlHandle, const CtlCallbacks* aCallbacks,
			const CtlConfig* aConfig, unsigned int aTimeoutInMsecs = 0);
    ~ExcaliburFemClient();

    int get_id();

private:
    int id_;

};
