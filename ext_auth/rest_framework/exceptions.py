from rest_framework.exceptions import APIException, ValidationError
from rest_framework import status

class APIErrorException(APIException):
    status_code = 400
    default_detail = 'A server error occurred.'

    def __init__(self, detail=None, status_code=None, field="error"):
        if status_code is not None:
            self.status_code = status_code

        if detail is not None:
            self.detail = {field: detail}

        print ("exception:", self.status_code, self.detail)