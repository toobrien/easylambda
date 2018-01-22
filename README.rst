======
easylambda
======

Easylambda helps you create and update a simple AWS Lambda Java function using a command line interface. AWS' Lambda console provides inline editing for Python and Nodejs, which lets you create test functions very quickly. This package intends to make the Java experience just as easy.

-----
Usage
-----

First, install the package:

  python setup.py install

Next, initialize a project:

  easyjava init-project --project-name demo

This command creates a project directory ("demo") with a template POM and handler file. Edit the handler (src/main/java/<groupId>/Handler.java), change into the project directory, and package your code with

  mvn package

After maven creates your initial jar, initialize the Lambda function:

  easyjava init-function

To add AWS SDK modules to your project, use update-project:

  easyjava update-project --dependencies s3 ec2 dynamodb

After updating your code, repackage and update the function code:

  mvn package && easyjava update-function-code

You can adjust a few configuration options for your Lambda function:

  easyjava update-function-configuration --memory-size 1024 --timeout 120

Altogether, easylambda provides five subcommands:

  * init-project: creates the initial project directory
  * update-project: add new AWS SDK modules to the project dependencies
  * init-function: creates the AWS Lambda function
  * update-function-code: after updating your code, repackage with maven then run this command
  * update-function-configuration: change timeout, memory size, etc.

To read a more complete description of each, run

  easyjava <subcommand> -h
