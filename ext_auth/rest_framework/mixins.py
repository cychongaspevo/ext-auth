from .exceptions import APIErrorException

class ErrorMixin(object):
    #error
    def error_missing_field(self, err_msg='missing fields'):
        error = {'code':101, 'description':err_msg}
        raise APIErrorException(error)

    def error_object_not_found(self, err_msg='object not found'):
        error = {'code':102, 'description':err_msg}
        raise APIErrorException(error)

    def error_exists(self, err_msg='object is exists'):
        error = {'code':106, 'description':err_msg}
        raise APIErrorException(error)
    
    def error_basic_requirement(self, err_msg='basic require not reach'):
        error = {'code':104, 'description':err_msg}
        raise APIErrorException(error)

    def error_firebase_admin(self, err_msg='firebase admin error', details=None):
        error = {
            'code':121,
            'description':err_msg}
        if details:
            error['details'] = details
        raise APIErrorException(error)