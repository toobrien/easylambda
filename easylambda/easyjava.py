#!/usr/bin/python

from easylambda import __path__
from easylambda.exceptions import \
  NoPomException, InitProjectException,\
  InitFunctionException
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from os import makedirs, getcwd, chdir
from os.path import isfile
from shutil import copyfile
from xml.etree.ElementTree import \
  fromstring, tostring, parse, SubElement
from urllib2 import urlopen
from easylambda.prettyxml import pretty_print
import boto3
from botocore.exceptions import ClientError, ParamValidationError
import sys

# The BOM provides a list of modules in the AWS SDK.
BOM_URL='https://raw.githubusercontent.com/aws/aws-sdk-java/master/aws-java-sdk-bom/pom.xml'

# for parsing BOM, POM
NS = {'pom':'http://maven.apache.org/POM/4.0.0'}
BOM_PATH='./pom:dependencyManagement/pom:dependencies/pom:dependency'
POM_PATH='./pom:dependencies/pom:dependency'

def read_xml(filename):
  xml_string = ''
  with open(filename) as f:
    xml_string = f.read()
    root = fromstring(xml_string)
    return root

def write_xml(root, filename):
  xml_string = tostring(root)
  cleaned = xml_string.replace('ns0:','')
  cleaned = cleaned.replace('xmlns:ns0','xmlns')
  pretty = pretty_print(cleaned)
  with open(filename,'w') as f:
    f.write(pretty)
  return root

def update_ids(root, groupId, artifactId):
  root.find('pom:groupId',NS).text = groupId
  root.find('pom:artifactId',NS).text = artifactId
  return root

def get_ids(root):
  groupId = root.find('pom:groupId',NS).text
  artifactId = root.find('pom:artifactId',NS).text
  return {
    'groupId': groupId,
    'artifactId': artifactId
  }

# reads the list of AWS SDK dependencies from an xml ElementTree
def get_aws_dependencies(root,path):
  dependency_list = []

  for dependency in root.findall(path,NS):
    try:
      dependency_list.append(
          (dependency.find('pom:artifactId',NS).text.split('aws-java-sdk-')[1])
      )
    except IndexError:
      # Not an AWS SDK module.
      pass
  
  return dependency_list

# Assumes dependency_list is valid. Validation occurs in arg parser.
def add_project_dependencies(root, to_add):
  deps = root.find('pom:dependencies',NS)
  project_dependencies = get_project_dependencies()

  try:
    for dependency in to_add:
      if dependency not in project_dependencies:
        artifactIdString = 'aws-java-sdk-' + dependency
        dep = SubElement(deps,"dependency")
        artifactId = SubElement(dep,"artifactId")
        artifactId.text = artifactIdString
        groupId = SubElement(dep,"groupId")
        groupId.text = "com.amazonaws"
  except TypeError:
    # if no supplieddependencies, for loop will raise TypeError
    pass

  return root 

def get_lambda_client(args):
  session_args = {}

  if ('profile' in args):
    session_args['profile_name'] = args.profile
  if ('region' in args):
    session_args['region_name'] = args.region

  session = boto3.Session(**session_args)
  lda = session.client('lambda')

  return lda

def get_zip_file_bytes(artifactId):
  try:
    with open('target/' + artifactId +\
                  '-1.0-SNAPSHOT.jar', 'rb')\
            as f:
      return f.read()
  except:
    # should be to stderr?
    print("Unable to read jar. Did you run 'mvn package' first?")
    raise

def init_function(args):
  project_name = get_project_name()

  lda = get_lambda_client(args) 

  # prepare arguments for create_function()
  root = read_xml('pom.xml')
  ids = get_ids(root)

  create_function_args = {}
  # Handler is <groupId>.Handler::handleRequest. Not flexible
  # but easy to use
  create_function_args['Handler'] = ids['groupId'] +\
                                    '.' +\
                                    'Handler::handleRequest'
  create_function_args['Code'] = { 
    'ZipFile': get_zip_file_bytes(ids['artifactId']) 
  }
  create_function_args['FunctionName'] = project_name
  create_function_args['Runtime'] = 'java8'

  if ('role' in args):
    create_function_args['Role'] = args.role
  else:
    raise InitFunctionException(
            "No role found. Please supply a role using --role."
          )
  create_function_args['Timeout'] = 40
  create_function_args['MemorySize'] = 512

  # arguments ready, create the function
  try:
    lda.create_function(**create_function_args)
  except (ClientError, ParamValidationError) as e:
    raise InitFunctionException("Function not created: " + e.__str__())

def init_project(args):
  module_path = __path__[0]
  project_path = args.project_name
  src_path = 'src/main/java/%s' %\
              args.group_id.replace('.','/')

  try:
    makedirs('/'.join(['.',project_path,src_path]))
  except OSError as e:
    raise InitProjectException(
            "Unable to create project directory: " +\
            e.__str__() +\
            "\n Project not initialized."
          )

  try:
    copyfile(
      '/'.join([module_path,"resources/handler_template"]), 
      '/'.join(['.',project_path,src_path,'Handler.java'])
    )
    copyfile(
      '/'.join([module_path,"resources/pom_template"]), 
      '/'.join(['.',project_path,'pom.xml'])
    ) 
  except IOError as e:
    raise InitProjectException(
            "Unable to copy template POM or Handler from " +\
            module_path +\
            "/resources/: " +\
            e.__str__() +\
            "\nProject not initialized"
          )
 
  # change into project directory
  # add_project_dependencies() assumes working directory = project directory
  try:
    chdir('/'.join(['.',project_path]))
  except:
    # ???
    raise
 
  # Update template POM with supplied dependencies
  try:
    root = read_xml('pom.xml')
    root = update_ids(
             root,
             groupId=args.group_id,
             artifactId=args.artifact_id
           )
    root = add_project_dependencies(root, args.dependencies)
    write_xml(root, 'pom.xml')
  except Exception as e:
    print(e)
    raise InitProjectException(
            "Unable to modify project pom.xml: " +\
            e.__str__() +\
            "\nProject not initialized."
          )

  # Update template Handler with groupId as package name
  try:
    handler = '/'.join(['.',src_path,'Handler.java'])
    with open(handler, 'r+') as f:
      f.readline() # seek past existing package name
      package_line = 'package ' + args.group_id + ';\n'
      remainder = f.read()
      f.seek(0)
      f.write(package_line + remainder)
      f.truncate()
  except Exception as e:
    raise InitProjectException(
            "Unable to modify template Handler: " +\
            e.__str__() +\
            "\nProject not initialized."
          )

def update_function_configuration(args):
  project_name = get_project_name()

  lda = get_lambda_client(args)

  update_function_configuration_args = {
    'FunctionName': project_name
  }

  if memory_size in args:
    update_function_configuration_args['MemorySize'] = args.memory_size
  if timeout in args:
    update_function_configuration_args['Timeout'] = args.timeout
  if tracing_config in args:
    update_function_configuration_args['TracingConfig'] = {
        'Mode': args.tracing_config
    }
  
  lda.update_function_configuration(**update_function_configuration_args)  

def update_function_code(args):
  project_name = get_project_name()
  root = read_xml('pom.xml')
  ids = get_ids(root)
  lda = get_lambda_client(args)

  update_function_code_args = {
    'FunctionName': project_name,
    'ZipFile': get_zip_file_bytes(ids['artifactId'])
  }

  lda.update_function_code(**update_function_code_args)

def update_project(args):
  try:
    root = read_xml('pom.xml')
    root = add_project_dependencies(root,args.dependencies)
    write_xml(root, 'pom.xml')
  except:
    raise Exception(
            "Unable to modify project pom.xml. " +\
            "Dependencies not added."
          )

def get_project_name():
  if isfile("pom.xml"):
    return getcwd().split("/")[-1]
  else:
    raise NoPomException

def get_project_dependencies():
  project_dependencies = []
  
  if isfile("pom.xml"):
    pom = read_xml("pom.xml")
    project_dependencies = get_aws_dependencies(pom,POM_PATH)

  return project_dependencies

def get_valid_aws_sdk_dependencies():
  bom = urlopen(BOM_URL).read()
  bom = fromstring(bom)
  valid_dependencies = get_aws_dependencies(bom,BOM_PATH)
  return valid_dependencies

def main():
  parser = ArgumentParser(formatter_class=RawDescriptionHelpFormatter)
  subparsers = parser.add_subparsers(
      help='Add -h after subcommand for more detailed help.'
    )
  
  valid_aws_sdk_dependencies = get_valid_aws_sdk_dependencies()

  #################
  # INIT_FUNCTION #
  #################
  # Create the AWS Lambda function.

  parser_init_function = subparsers.add_parser(
      'init-function',
      help='Create a Lambda function, using target jar.'
    )
  parser_init_function.add_argument(
      '--role',
      help='Lambda execution role.'
    )
  parser_init_function.add_argument(
      '--profile',
      help='Configuration profile (as defined in the shared\
            credentials file) for Lambda operations.'
    )
  parser_init_function.add_argument(
      '--region',
      help='Custom region for Lambda operations.'
    )
  parser_init_function.set_defaults(process=init_function)

  ################
  # INIT_PROJECT #
  ################
  # Create the project directory with template POM and handler source.

  parser_init_project = subparsers.add_parser(
      'init-project',
      help='Create a project directory with template POM and handler class.'
    )
  parser_init_project.add_argument(
      '--project-name',
      help='Name of the project.',
      default='easylambda_demo'
    )

  # The default group-id and artifact-id match those in the template POM
  # distributed with easylambda.
  parser_init_project.add_argument(
      '--group-id',
      help='Used as package name.',
      default='com.example'
    )
  parser_init_project.add_argument(
      '--artifact-id',
      help='Used as jar name, and should be same as project name.',
      default='demo'
    )
  parser_init_project.add_argument(
      '--dependencies',
      help='A list of AWS SDK dependencies, e.g.\
             \'s3\', \'dynamodb\', \'kinesis\'.',
      nargs='*', 
      choices=valid_aws_sdk_dependencies,
      default=[]
    )
  parser_init_project.set_defaults(process=init_project)

  #################################
  # UPDATE_FUNCTION_CONFIGURATION #
  #################################
  # Update properties of the function, e.g. memory-size.  

  parser_update_function_configuration = \
    subparsers.add_parser(
      'update-function-configuration', 
      help='Conveniently update several function parameters.\
          for more complete customization, use the AWS CLI.'
    )
  parser_update_function_configuration.add_argument(
      '--memory-size', 
      help='The function\'s memory and CPU, 0 to 3008.', default=512
    )
  parser_update_function_configuration.add_argument(
      '--timeout',
      help='Function timeout, in seconds (0-300).',
      default=45
    )
  parser_update_function_configuration.add_argument(
      '--tracing-config',
      help='X-ray tracing option.',
      choices=['Active','PassThrough']
    )
  parser_update_function_configuration.add_argument(
      '--profile',
      help='Configuration profile (as defined in the shared\
            credentials file) for lambda operations.'
    )
  parser_update_function_configuration.add_argument(
      '--region',
      help='Custom region for lambda operations.'
    )
  parser_update_function_configuration.set_defaults(
      process=update_function_configuration
    )

  ########################
  # UPDATE_FUNCTION_CODE #
  ########################
  # Rebuild jar (with mvn) and upload function code (with boto).
  
  parser_update_function_code = subparsers.add_parser(
      'update-function-code',
      help='Upload the latest jar (target/<artifactId>-SNAPSHOT-1.0.jar).'
    )
  parser_update_function_code.add_argument(
      '--profile',
      help='Configuration profile (as defined in the shared\
            credentials file) for Lambda operations.'
    )
  parser_update_function_code.add_argument(
      '--region',
      help='Custom region for lambda operations.'
    )
  parser_update_function_code.set_defaults(process=update_function_code)


  ##################
  # UPDATE_PROJECT #
  ##################
  # Add AWS SDK dependencies

  parser_update_project = subparsers.add_parser(
      'update-project',
      help='Add new AWS SDK dependencies to the project.'
    )
  parser_update_project.add_argument(
      '--dependencies',
      help='A list of AWS SDK dependencies e.g.\
             \'s3\', \'dynamodb\', \'kinesis\'.',
      nargs='*',
      choices=valid_aws_sdk_dependencies
    )
  parser_update_project.set_defaults(process=update_project)

  # Parse and execute command.

  args = parser.parse_args()
  args.process(args)

if __name__=="__main__":
  main()
