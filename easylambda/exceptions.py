class EasyJavaException(Exception):
  def __str__(self):
    return self.msg
  def __init__(self, msg):
    self.msg = msg

class NoPomException(EasyJavaException):
  pass

class InitFunctionException(Exception):
  pass

class InitProjectException(Exception):
  pass

class UpdateConfigurationException(Exception):
  pass

class UpdateCodeException(Exception):
  pass

class UpdateProjectException(Exception):
  pass
