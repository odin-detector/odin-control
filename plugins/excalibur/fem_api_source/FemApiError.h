#include <iostream>
#include <string>
#include <sstream>

class FemApiError
{
public:
    FemApiError();
    virtual ~FemApiError();
    std::ostringstream& Set();
    std::ostringstream& Set(const int error_code);
    static const char* get_string(void);
    static const int get_code(void);

protected:
    std::ostringstream os;

private:
    FemApiError(const FemApiError&);
    FemApiError& operator =(const FemApiError&);
    static std::string error_string_;
    static int error_code_;

};
