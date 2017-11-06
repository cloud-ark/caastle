import os

from cliff.command import Command

class AWSSetup(Command):
    "Set up aws. Run ./restart-cloudark.sh after cld setup aws has finished."

    def take_action(self, parsed_args):
        os.system("pip install awscli")
        os.system("aws configure")