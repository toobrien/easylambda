class EasyJavaException(Exception):
  def __str__(self):
    return self.msg
  def __init__(self, msg):
    if msg:
      self.msg = msg

class NoPomException(EasyJavaException):
  pass

class InitFunctionException(EasyJavaException):
  pass

class InitProjectException(EasyJavaException):
  pass

class UpdateConfigurationException(EasyJavaException):
  pass

class UpdateCodeException(EasyJavaException):
  pass

class UpdateProjectException(EasyJavaException):
  pass
