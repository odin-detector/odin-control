/*
 * femapi.h
 *
 *  Created on: 2 Feb 2011
 *      Author: fgz73762
 */

/* This file defines the API of the library that is used to communicate with the FEM hardware */

#ifndef FEMAPI_H_
#define FEMAPI_H_

#include "string.h"
#include "time.h"

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Image dimension constants
 */
#define FEM_PIXELS_PER_CHIP_X 256
#define FEM_PIXELS_PER_CHIP_Y 256
#define FEM_CHIPS_PER_BLOCK_X 4
#define FEM_BLOCKS_PER_STRIPE_X 2
#define FEM_CHIPS_PER_STRIPE_X 8
#define FEM_CHIPS_PER_STRIPE_Y 1
#define FEM_STRIPES_PER_MODULE 2
#define FEM_STRIPES_PER_IMAGE 6
#define FEM_CHIP_GAP_PIXELS_X 3
#define FEM_CHIP_GAP_PIXELS_Y_LARGE 125
#define FEM_CHIP_GAP_PIXELS_Y_SMALL 3
#define FEM_PIXELS_PER_STRIPE_X ((FEM_PIXELS_PER_CHIP_X+FEM_CHIP_GAP_PIXELS_X)*FEM_CHIPS_PER_STRIPE_X-FEM_CHIP_GAP_PIXELS_X)
#define FEM_TOTAL_PIXELS_Y (FEM_PIXELS_PER_CHIP_Y*FEM_CHIPS_PER_STRIPE_Y*FEM_STRIPES_PER_IMAGE +\
                (FEM_STRIPES_PER_IMAGE/2-1)*FEM_CHIP_GAP_PIXELS_Y_LARGE +\
                (FEM_STRIPES_PER_IMAGE/2)*FEM_CHIP_GAP_PIXELS_Y_SMALL)
#define FEM_TOTAL_PIXELS_X FEM_PIXELS_PER_STRIPE_X

/*
 * Edge pixel ratio (Note: don't put parentheses around this so that integer arithmetic works).
 */
#define FEM_EDGE_PIXEL_RATIO_NUM 2
#define FEM_EDGE_PIXEL_RATIO_DEN 5
#define FEM_EDGE_PIXEL_RATIO 2/5

/*
 * Bits per pixel constants
 */
#define FEM_BITS_PER_PIXEL_1 0
#define FEM_BITS_PER_PIXEL_4 1
#define FEM_BITS_PER_PIXEL_12 2
#define FEM_BITS_PER_PIXEL_24 3

/* The frame buffer structure.  These are used to carry frame pixels and their
 * associated metadata.
 */
typedef struct CtlFrame
{
    void* buffer;
    size_t bufferLength;
    unsigned int sizeX;
    unsigned int sizeY;
    unsigned int sizeZ;
    int bitsPerPixel;
    time_t timeStamp;
    void* internalArray;
    struct CtlFrame* internalNext;
    unsigned int frameCounter;
    int referenceCount;
} CtlFrame;

/* A structure used to pass the call back functions to the library by
 * the femInitialise function.
 */
typedef struct CtlCallbacks
{
    CtlFrame* (*ctlAllocate)(void* ctlHandle);
    void (*ctlFree)(void* ctlHandle, CtlFrame* buffer);
    void (*ctlReceive)(void* ctlHandle, CtlFrame* buffer);
    void (*ctlSignal)(void* ctlHandle, int id);
    void (*ctlReserve)(void* ctlHandle, CtlFrame* buffer);
} CtlCallbacks;

/* A structure that contains fem configuration data.
*/
typedef struct CtlConfig
{
    int femNumber;
    const char* femAddress;
    int femPort;
    const char* dataAddress;
} CtlConfig;

/* The functions provided by the library.
*/
const char* femErrorMsg(void);
int femErrorCode(void);
int femGetId(void* femHandle);

void* femInitialise(void* ctlHandle, const CtlCallbacks* callbacks, const CtlConfig* config);
int femSetInt(void* femHandle, int chipId, int id, size_t size, int* value);
int femSetShort(void* femHandle, int chipId, int id, size_t size, short* value);
int femSetFloat(void* femHandle, int chipId, int id, size_t size, double* value);
int femGetInt(void* femHandle, int chipId, int id, size_t size, int* value);
int femGetShort(void* femHandle, int chipId, int id, size_t size, short* value);
int femGetFloat(void* femHandle, int chipId, int id, size_t size, double* value);
int femCmd(void* femHandle, int chipId, int id);
void femClose(void* femHandle);

void femDummy(void);

/* An identifier that indicates 'all chips'.
*/
#define FEM_CHIP_ALL 0

/* The return codes used by various functions.
*/
#define FEM_RTN_OK 0
#define FEM_RTN_UNKNOWNOPID 1
#define FEM_RTN_ILLEGALCHIP 2
#define FEM_RTN_BADSIZE 3
#define FEM_RTN_INITFAILED 4

/* Operation mode constants
*/
#define FEM_OPMODE_NORMAL 0
#define FEM_OPMODE_BURST 1
#define FEM_OPMODE_HISTOGRAM 2
#define FEM_OPMODE_DACSCAN 3
#define FEM_OPMODE_MATRIXREAD 4

/* Trigger mode constants
*/
#define FEM_TRIGMODE_INTERNAL 0
#define FEM_TRIGMODE_EXTERNAL 1
#define FEM_TRIGMODE_SYNC 2

/* Counter select constants
*/
#define FEM_CTRSELECT_A 0
#define FEM_CTRSELECT_B 1
#define FEM_CTRSELECT_AB 2

/* The operation identifiers for the get, set, cmd and signal functions.
*/
/* Commands */
#define FEM_OP_STARTACQUISITION 1
#define FEM_OP_STOPACQUISITION 2
#define FEM_OP_LOADPIXELCONFIG 3
#define FEM_OP_FREEALLFRAMES 4
#define FEM_OP_LOADDACCONFIG 5
#define FEM_OP_FEINIT 6
#define FEM_OP_REBOOT 7


/* Medipix III global registers */
#define FEM_OP_MPXIII_COLOURMODE 1000
#define FEM_OP_MPXIII_COUNTERDEPTH 1001
#define FEM_OP_MPXIII_EXTERNALTRIGGER 1002
#define FEM_OP_MPXIII_OPERATIONMODE 1003
#define FEM_OP_MPXIII_COUNTERSELECT 1004
#define FEM_OP_MPXIII_NUMTESTPULSES 1005
#define FEM_OP_MPXIII_READWRITEMODE 1006 /* Added for MPXIII-RX support */
#define FEM_OP_MPXIII_DISCCSMSPM 1007 /* Added for MPXIII-RX support */
#define FEM_OP_MPXIII_EQUALIZATIONMODE 1008 /* Added for MPXIII-RX support */
#define FEM_OP_MPXIII_CSMSPMMODE 1009 /* Added for MPXIII-RX support */
#define FEM_OP_MPXIII_GAINMODE 1010 /* Added for MPXIII-RX support */
#define FEM_OP_MPXIII_TRIGGERPOLARITY 1011 /* Added for MPXIII-RX support */
#define FEM_OP_MPXIII_LFSRBYPASS 1012 /* Added for MPXIII-RX support */

/* Medipix III per chip registers */
#define FEM_OP_MPXIII_DACSENSE 2000
#define FEM_OP_MPXIII_DACEXTERNAL 2001
#define FEM_OP_MPXIII_THRESHOLD0DAC 2002
#define FEM_OP_MPXIII_THRESHOLD1DAC 2003
#define FEM_OP_MPXIII_THRESHOLD2DAC 2004
#define FEM_OP_MPXIII_THRESHOLD3DAC 2005
#define FEM_OP_MPXIII_THRESHOLD4DAC 2006
#define FEM_OP_MPXIII_THRESHOLD5DAC 2007
#define FEM_OP_MPXIII_THRESHOLD6DAC 2008
#define FEM_OP_MPXIII_THRESHOLD7DAC 2009
#define FEM_OP_MPXIII_PREAMPDAC 2010
#define FEM_OP_MPXIII_IKRUMDAC 2011
#define FEM_OP_MPXIII_SHAPERDAC 2012
#define FEM_OP_MPXIII_DISCDAC 2013
#define FEM_OP_MPXIII_DISCLSDAC 2014
#define FEM_OP_MPXIII_SHAPERTESTDAC 2015 /* Modified name for MPXIII-RX support */
#define FEM_OP_MPXIII_DISCLDAC 2016 /* Modified name for MPXIII-RX support */
#define FEM_OP_MPXIII_DELAYDAC 2017
#define FEM_OP_MPXIII_TPBUFFERINDAC 2018
#define FEM_OP_MPXIII_TPBUFFEROUTDAC 2019
#define FEM_OP_MPXIII_RPZDAC 2020
#define FEM_OP_MPXIII_GNDDAC 2021
#define FEM_OP_MPXIII_TPREFDAC 2022
#define FEM_OP_MPXIII_FBKDAC 2023
#define FEM_OP_MPXIII_CASDAC 2024
#define FEM_OP_MPXIII_TPREFADAC 2025
#define FEM_OP_MPXIII_TPREFBDAC 2026
#define FEM_OP_MPXIII_TESTDAC 2027 /* Added for MPXIII-RX support */
#define FEM_OP_MPXIII_DISCHDAC 2028 /* Added for MPXIII-RX support */
#define FEM_OP_MPXIII_EFUSEID 2029 /* Modified value for MPIII-RX support */
#define FEM_OP_MPXIII_TESTPULSE_ENABLE 2030 /* Added for workaround to allow test pulse operation with standlone code */
/* Medipix III per pixel registers */
#define FEM_OP_MPXIII_PIXELMASK 3000
#define FEM_OP_MPXIII_PIXELDISCL 3001 /* Modified name for MPXIII-RX support */
#define FEM_OP_MPXIII_PIXELDISCH 3002 /* Modified name for MPXIII-RX support */
/*#define FEM_OP_MPXIII_PIXELGAINMODE 3003 Removed for MPXIII-RX */
#define FEM_OP_MPXIII_PIXELTEST 3004
/* Ids 4000..4999 are FEM registers */
#define FEM_OP_NUMFRAMESTOACQUIRE 4000
#define FEM_OP_ACQUISITIONTIME 4001
#define FEM_OP_ACQUISITIONPERIOD 4002
#define FEM_OP_P5V_A_VMON 4003
#define FEM_OP_P5V_B_VMON 4004
#define FEM_OP_P5V_FEMO0_IMON 4005
#define FEM_OP_P5V_FEMO1_IMON 4006
#define FEM_OP_P5V_FEMO2_IMON 4007
#define FEM_OP_P5V_FEMO3_IMON 4008
#define FEM_OP_P5V_FEMO4_IMON 4009
#define FEM_OP_P5V_FEMO5_IMON 4010
#define FEM_OP_P48V_VMON 4011
#define FEM_OP_P48V_IMON 4012
#define FEM_OP_P5VSUP_VMON 4013
#define FEM_OP_P5VSUP_IMON 4014
#define FEM_OP_HUMIDITY_MON 4015
#define FEM_OP_AIR_TEMP_MON 4016
#define FEM_OP_COOLANT_TEMP_MON 4017
#define FEM_OP_COOLANT_FLOW_MON 4018
#define FEM_OP_P3V3_IMON 4019
#define FEM_OP_P1V8_IMON_A 4020
#define FEM_OP_BIAS_IMON 4021
#define FEM_OP_P3V3_VMON 4022
#define FEM_OP_P1V8_VMON_A 4023
#define FEM_OP_BIAS_VMON 4024
#define FEM_OP_P1V8_IMON_B 4025
#define FEM_OP_P1V8_VMON_B 4026
#define FEM_OP_COOLANT_TEMP_STATUS 4027
#define FEM_OP_HUMIDITY_STATUS 4028
#define FEM_OP_COOLANT_FLOW_STATUS 4029
#define FEM_OP_AIR_TEMP_STATUS 4030
#define FEM_OP_BIAS_ON_OFF 4031
#define FEM_OP_LV_ON_OFF 4032
#define FEM_OP_FAN_FAULT 4033
#define FEM_OP_BIAS_LEVEL 4034
#define FEM_OP_VDD_ON_OFF 4035
#define FEM_OP_P1V5_AVDD_1_POK 4036
#define FEM_OP_P1V5_AVDD_2_POK 4037
#define FEM_OP_P1V5_AVDD_3_POK 4038
#define FEM_OP_P1V5_AVDD_4_POK 4039
#define FEM_OP_P1V5_VDD_1_POK 4040
#define FEM_OP_P2V5_DVDD_1_POK 4041
#define FEM_OP_DAC_IN_TO_MEDIPIX 4042
#define FEM_OP_DAC_OUT_FROM_MEDIPIX 4043
#define FEM_OP_MOLY_TEMPERATURE 4044
#define FEM_OP_LOCAL_TEMP 4045
#define FEM_OP_REMOTE_DIODE_TEMP 4046
#define FEM_OP_MOLY_HUMIDITY 4047
#define FEM_OP_MEDIPIX_CHIP_DISABLE 4048
#define FEM_OP_SCAN_DAC 4049
#define FEM_OP_SCAN_START 4050
#define FEM_OP_SCAN_STOP 4051
#define FEM_OP_SCAN_STEP 4052
#define FEM_OP_BURST_SUBMIT_PERIOD 4053

/* Ids 5000..5999 are signals */
#define FEM_OP_ACQUISITIONCOMPLETE 5000
#define FEM_OP_CORRUPTIMAGE 5001

#ifdef __cplusplus
}  /* Closing brace for extern "C" */
#endif

#endif /* FEMAPI_H_ */
