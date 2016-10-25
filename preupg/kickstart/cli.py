import optparse

from preupg.constants import *


class CLIKickstart(object):
    """ Class for processing data from commandline """

    def __init__(self, args=None):
        """ parse arguments """
        self.parser = optparse.OptionParser(usage=USAGE, description=PROGRAM_DESCRIPTION)

        #self.parser.usage = "%%prog [-v] <content_file>"

        #self.add_args()
        if args:
            self.opts, self.args = self.parser.parse_args(args=args)
        else:
            self.opts, self.args = self.parser.parse_args()


if __name__ == '__main__':
    x = CLIKickstart()
    print (x.args.id)

