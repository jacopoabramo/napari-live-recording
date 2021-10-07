class CameraError(Exception):
    """Wrapper for Exception handling in camera devices errors

    :param Exception: generic Exception class
    :type Exception: Exception
    """

    def __init__(self, error: str) -> None:
        """CameraError constructor

        :param error: error string to print
        :type error: str
        """
        self.error_description = error
    
    def __str__(self) -> str:
        """Returns the error description

        :return: string describing the raised error
        :rtype: str
        """
        return self.error_description