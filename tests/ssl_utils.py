"""
Utility class to generate temporary SSL certificate and key files for testing HTTPS support in
odin_control.

NOTE: THIS IS A SELF-SIGNED CERTIFICATE and KEY FOR TESTING ONLY. DO NOT USE IN PRODUCTION

Tim Nicholls, STFC Detector Systems Software Group
"""

from tempfile import NamedTemporaryFile


class SslTestCert:
    SSL_CERTIFICATE = """-----BEGIN CERTIFICATE-----
MIID0zCCArugAwIBAgIUfB/44KsQus8pZWBZep6LeE9v8k4wDQYJKoZIhvcNAQEL
BQAwazELMAkGA1UEBhMCVUsxFDASBgNVBAgMC094Zm9yZHNoaXJlMQ8wDQYDVQQH
DAZEaWRjb3QxEjAQBgNVBAoMCVVLUkkgU1RGQzENMAsGA1UECwwEVGVjaDESMBAG
A1UEAwwJbG9jYWxob3N0MB4XDTIzMDkyNjA5Mzk0OVoXDTMzMDkyMzA5Mzk0OVow
azELMAkGA1UEBhMCVUsxFDASBgNVBAgMC094Zm9yZHNoaXJlMQ8wDQYDVQQHDAZE
aWRjb3QxEjAQBgNVBAoMCVVLUkkgU1RGQzENMAsGA1UECwwEVGVjaDESMBAGA1UE
AwwJbG9jYWxob3N0MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAus5Y
wSgq9jx42uXxcvAVGh6jn/YYJwr51sks9rtTpcKe5GoNpA2i8OKeQB6Uwwb2jroK
y9L2neLqVyRruAoiccKGvbSQCeiyS45c02pQmHAvdbNNmPUEOfRszxorhV/EWw5V
obxGft9RucZN/l+8FiFwFLIS/TqtTnCTeWRre0Zvl5mzXAISZ7cT5AQ7bUCAYnoh
tACwHI1b3g+bnNRxMkl3VE7IjyKlP0MuXoamp0yNJofJhKu9x6HRo/UyQVae7Zy9
9imOuWq/WGuIysprIXQXbwAzBV43oIgYb/ifWbDQGGIEeQRsWWkMduBpC5EtN9uM
YKA+hXLOfc3zRvUkDQIDAQABo28wbTAdBgNVHQ4EFgQUl6nAO+KZcHkrZ0lCaNwx
B8nP3LwwHwYDVR0jBBgwFoAUl6nAO+KZcHkrZ0lCaNwxB8nP3LwwDwYDVR0TAQH/
BAUwAwEB/zAaBgNVHREEEzARgglsb2NhbGhvc3SHBH8AAAEwDQYJKoZIhvcNAQEL
BQADggEBADUfh6l6lX0o37T9txtb/CQz5uGHndghPn1QtVFBc9ma6U/5FYDH4PqU
vRf/pKte+BdbyvbjF4e8HRH5/9jB259yOtve+zj6j1nU1vkiAuu16wLT9CHhI5ev
z4xH0VobE+9gc8iQCzHzp2svo567jQO5UvOIJlYLUkf4Ugq+cxcYTk/XpO04nqLu
j2DnwtpXUGtE+22dI7oj/QhUI5G8A0mepYg49k7s56vg4VWujsBlnV58H6JWUFjN
2D2AX+UKRiW19Esjek95Lj1jXEoPHWAUI3lK3/ZDe9L2BZemNdA5apCNA0o7/bvK
vYiNxUyKe/Y4AYpMfz1FQsixdHMj/gY=
-----END CERTIFICATE-----
"""

    SSL_KEY = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC6zljBKCr2PHja
5fFy8BUaHqOf9hgnCvnWySz2u1Olwp7kag2kDaLw4p5AHpTDBvaOugrL0vad4upX
JGu4CiJxwoa9tJAJ6LJLjlzTalCYcC91s02Y9QQ59GzPGiuFX8RbDlWhvEZ+31G5
xk3+X7wWIXAUshL9Oq1OcJN5ZGt7Rm+XmbNcAhJntxPkBDttQIBieiG0ALAcjVve
D5uc1HEySXdUTsiPIqU/Qy5ehqanTI0mh8mEq73HodGj9TJBVp7tnL32KY65ar9Y
a4jKymshdBdvADMFXjegiBhv+J9ZsNAYYgR5BGxZaQx24GkLkS0324xgoD6Fcs59
zfNG9SQNAgMBAAECggEAJpivUFtxAvbMHqgvWqjdp0uo0Ypag6iaJcVjn6flOMSt
KTL7VgfGQICGI2feIyyLYUJxrBrOvyDs+6vIANrBMqF3TvdhYla8je1gYwMem1xk
hexRzlZjdOj6WVEGKHS4wHqF+ViJ9TlFbL2bDEFx/l2Sx4ficgU/XQtYARcdOPch
uTc6dukTKHchEgQVHFRMhOBYuHihufBIaoffzy9TNxJ7bUBhDvgBi8B38SfAE71o
PFTqN4ACx7NCVcisj2WmuOeHvp74GjyIEATyRW57cjCVgAYKU8ddijBqyWs3hPEt
A83h9jqxkLMkohqs6uldeDJRH/DUn7TYDonGYccdIQKBgQD5yBvibVlVSB6wwV7i
QoR018tqQDadAvyCiOjZvsNAdxl/EPx2BPbo785IeKeC1dRI0AfLl1BvQnZmDXX7
DXWvzCw6jexrU5DyJm++opvawz/myrxNb/UA+IecK645Srm00taN3SsimqiWAe2e
j/ElhdvB6s7CDO/8ee2qPffVIQKBgQC/dOLIzglI/3f9xzDCC1kGCqFzyW0oaQNQ
DkNSiMQUb4z1XHmND6LDGPIo/OZtsECfZMQvPqvdOjPH3eKrFvewl/XkPrtLB7mq
UoZwpQNB8DffgUY9PoZ6gPZICtXloLFkUKFbJVbGbUI8Zs93Act/ONEBwoQBABhi
ePt/Qs3FbQKBgQCE+QPnOcFqBjfYb0kc+L5dGZh/2ul4EuPsdghICycUxZK8M4XD
KodroGZX7Gt42m7lyGGt/8LhSCeR0q6xVQwG55HQJkfrJxSt5MpuWVDRWEpHijxO
mUB8INLIz/QzKdXNLsTrxwc0p9MB8MrYM9bz29wO0vr5ETwdU6ezjsPGIQKBgGaS
UZmxQKo6K+frWoTrHXOuKFdnF7Mpp5uxOII0QZCNPuCI/ZoEQXfymnI5I56qacS7
cJu7IMpyDyHKD1EICgUzNIpmzWLiLadBdUNONJOUBesZUC8pm1RwWQG5xGS0lbUf
uYKiW34NNQo1LnscnBB5uQgPVTdP/MBs/phsit91AoGANLq/iPBhoGIvLA4Bok2v
diGjDII7NV55JnTVmO3tQc0C7EPdOIVPWg1MimIlsoxZ8OoJInBt0By7iuFLys6A
PBZ1ELX+HaxrA7MJr4gq4uAMpdfIdlXAmTLFBsSLGNw4b0YTbkGBIDzVMmn4bmA8
c7psJdd5G7B1rHg1lQ548EY=
-----END PRIVATE KEY-----
"""

    def __init__(self):
        self._cert_file = NamedTemporaryFile(mode="w+")
        self._cert_file.write(self.SSL_CERTIFICATE)
        self._cert_file.flush()

        self._key_file = NamedTemporaryFile(mode="w+")
        self._key_file.write(self.SSL_KEY)
        self._key_file.flush()

    @property
    def cert_file(self):
        return self._cert_file.name

    @property
    def key_file(self):
        return self._key_file.name
