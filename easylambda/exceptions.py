class NoPomException(Exception):
  msg = 'No POM found in working directory. Are you in a project directory?'
  def __str__(self):
    return self.msg
  def __init__(self):
    pass

class ProjectInitException(Exception):
  def __str__(self):
    return self.msg
  def __init__(self, msg):
    self.msg = msg
