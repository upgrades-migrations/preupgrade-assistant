import optparse


class CLIKickstart(object):
    """ Class for processing data from commandline """

    def __init__(self, args=None):
        """ parse arguments """
        self.parser = optparse.OptionParser()

        self.add_args()
        if args:
            self.opts, self.args = self.parser.parse_args(args=args)
        else:
            self.opts, self.args = self.parser.parse_args()

    def add_args(self):
        self.parser.add_option(
            "-y",
            "--assumeyes",
            action="store_true",
            default=False,
            help="Suppress user interaction"
        )


if __name__ == '__main__':
    x = CLIKickstart()
    print (x.args.id)
