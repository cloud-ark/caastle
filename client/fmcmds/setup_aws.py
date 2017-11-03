import os

from cliff.command import Command

class AWSSetup(Command):

    def take_action(self, parsed_args):
        os.system("pip install awscli")
        os.system("aws configure")