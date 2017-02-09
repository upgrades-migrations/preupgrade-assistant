import optparse


class CLICreator(object):

    """Class for processing data from commandline"""

    def __init__(self, args=None):
        """parse arguments"""
        self.parser = optparse.OptionParser()

        self.add_args()
        if args:
            self.opts, self.args = self.parser.parse_args(args=args)
        else:
            self.opts, self.args = self.parser.parse_args()

    def add_args(self):
        self.parser.add_option(
            "-m",
            "--main-directory",
            dest="maindir",
            help="Specify main directory for content",
        )
        self.parser.add_option(
            "-v",
            "--validate",
            action='store_true',
            help="Validate content(s)"
        )
        self.parser.add_option(
            "-d",
            "--debug",
            action='store_true',
            help="Turn on debugging mode"
        )

if __name__ == '__main__':
    x = CLICreator()
    print (x.args.id)
