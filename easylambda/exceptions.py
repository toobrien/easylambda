class NoPomException(Exception):
  msg = 'No POM found in working directory. Are you in a project directory?'
  def __str__(self):
    return self.msg
  def __init__(self):
    if msg:
      slf.msg = msg 

class InitFunctionException(Exception):
  def __str__(self):
    return self.msg
  def __init__(self, msg):
    self.msg = msg

class InitProjectException(Exception):
  def __str__(self):
    return self.msg
  def __init__(self, msg):
    self.msg = msg
