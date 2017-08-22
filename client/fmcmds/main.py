import sys

from cliff.app import App
from cliff.commandmanager import CommandManager


class FirstMileApp(App):

    def __init__(self):
        super(FirstMileApp, self).__init__(
            description='CloudARK command-line tool to create and manage cloud environments for containerized applications.',
            version='0.0.1',
            command_manager=CommandManager('cld.cmds'),
            deferred_help=True,
            )

    def initialize_app(self, argv):
        self.LOG.debug('initialize_app %s' % argv)

    def prepare_to_run_command(self, cmd):
        self.LOG.debug('prepare_to_run_command %s', cmd.__class__.__name__)

    def clean_up(self, cmd, result, err):
        self.LOG.debug('clean_up %s', cmd.__class__.__name__)
        if err:
            self.LOG.debug('got an error: %s', err)


def main(argv=sys.argv[1:]):
    myapp = FirstMileApp()
    return myapp.run(argv)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
