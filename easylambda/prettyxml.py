# need to support empty tags

from cStringIO import StringIO
from enum import Enum

class States(Enum):
  entering_tag = 0 
  in_tag = 1
  in_attribute = 2
  exiting_tag = 3

def entering_tag(token):
  state_data['state'] = States.in_tag
  if token == '/':
    to_return = '<' + token
    state_data['indent'] -= 1
    if state_data['last_tag_was_close']:
      to_return = (2 * ' ' * state_data['indent']) + '<' + token
    state_data['last_tag_was_close'] = True
    return to_return
  else:
    to_return = (2 * ' ' * state_data['indent']) + '<' + token
    if not state_data['last_tag_was_close']:
      to_return = '\n' + to_return
    state_data['last_tag_was_close'] = False
    state_data['indent'] += 1
    return to_return
    
def in_tag(token):
  if token == '\'':
    state_data['state'] = States.in_attribute
    return token
  elif token == '>':
    state_data['state'] = States.exiting_tag
    if state_data['last_tag_was_close']:
      return token + '\n'
    else:
      return token
  else:
    return token

def in_attribute(token):
  if token == '\'':
    state_data['state'] = States.in_tag
  return token

def exiting_tag(token):
  if token.isspace():
    return ''
  elif token != '<':
    return token
  else:
    state_data['state'] = States.entering_tag
    return ''

state_actions = {
  States.entering_tag: entering_tag,
  States.in_tag: in_tag,
  States.in_attribute: in_attribute,
  States.exiting_tag: exiting_tag
}

state_data = {}

def pretty_print(xml):
  state_data['indent'] = 0
  state_data['last_tag_was_close'] = False 
  state_data['state'] = States.exiting_tag
  
  pointer = 0
  output = StringIO()

  while pointer < len(xml):
    token = xml[pointer]

    # treat escape and escaped character as one
    if token == '\\':
      pointer += 1
      token += xml[pointer]

    result = state_actions[state_data['state']](token)
    
    output.write(result)
    pointer += 1

  pretty = output.getvalue()
  output.close()

  return pretty
