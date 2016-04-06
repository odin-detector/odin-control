/*
 * FemException.h
 *
 *  Created on: Nov 22, 2011
 *      Author: tcn45
 */

#ifndef FEMEXCEPTION_H_
#define FEMEXCEPTION_H_

#include <exception>
#include <iostream>
#include <sstream>
#include <string>

#define FEM_EXCEPTION_LOCATION __FUNCTION__,__FILE__,__LINE__

typedef int FemErrorCode;

class FemException: public std::exception
{

public:

    FemException(const std::string aExText) throw() :
        mExCode(-1),
        mExText(aExText),
        mExFunc("unknown"),
        mExFile("unknown"),
        mExLine(-1)
        { };

    FemException(const FemErrorCode aExCode, const std::string aExText) throw() :
        mExCode(aExCode),
        mExText(aExText),
        mExFunc("unknown"),
        mExFile("unknown"),
        mExLine(-1)
        { };

    FemException(const FemErrorCode aExCode, const std::string aExText, const std::string aExFunc,
                             const std::string aExFile, const int aExLine) throw() :
        mExCode(aExCode),
        mExText(aExText),
        mExFunc(aExFunc),
        mExFile(aExFile),
        mExLine(aExLine)
        { };

    virtual ~FemException(void) throw() { };

    virtual const char * what() const throw() {
        return mExText.c_str();
    };

    virtual const char * where() const throw() {
        std::ostringstream ostr;
        ostr << "function: " << mExFunc << " file: " << mExFile << " line: " << mExLine;
        return (ostr.str()).c_str();
    };

    virtual FemErrorCode which() const throw()
    {
        return mExCode;
    };

private:

        const FemErrorCode mExCode;
        const std::string  mExText;
        const std::string  mExFunc;
        const std::string  mExFile;
        const int          mExLine;

};

#endif /* FEMEXCEPTION_H_ */
