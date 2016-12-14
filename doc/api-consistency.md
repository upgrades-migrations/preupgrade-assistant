API consistency guidelines
==========================

Preupgrade Assistant provides two separate APIs for writing modules:
Python API and Bash API.  These languages are very different, so are
common patterns and methods of solving programming problems.

Yet, we want to keep both APIs retain similar "look & feel" so that
module developers and maintainers that will need to switch get as little
surprise as possible.

In order to help developers of both APIs prevent diverging the behaviors
too much, this document attempts to set interface guidelines that make
maximum use of both language's common features.


Functions
---------

 *  Python: all functions live under `preupg` module:

        preupgm.myfun()

 *  Bash: all functions are prefixed by `preupgm_`:

        preupgm_myfun


Variables
---------

 *  Python: all global variables are under `preupg` module:

        preupgm.MYVAR

 *  Bash: all global variables are prefixed by `PREUPGM_`:

        PREUPGM_MYVAR


Arguments
---------

In general, positional parameters are preferred over key/value pairs as
this is easier to do in Bash.

In Python, only allowed types are strings, integers or lists of strings
where a joint string would be equivalent.  It's recommended to avoid
integers in Python since they don't have Bash equivalent (everything is
string in Bash).


### Scalars ###

 *  Python:

        preupgm.myfun('8', 'foo', 's/bar/baz/')

 *  Bash: Bash only knows strings so this is obvious:

        preupgm_myfun 8 foo s/bar/baz/


### Pairs ###

 *  Python:

        preupgm.myfun('foo', bar=2)

 *  Bash:

        preupgm_myfun --bar 2 foo


### Lists ###

A long list may be passed as list of strings (or file-like objects,
assuming the content is a valid UTF-8).  Equivalent of doing this in
Bash is passing a filename parameter or accepting standard input:

 *  Python:

        preupgm.myfun(open('foo.conf'))
        preupgm.myfun(sys.stdin)
        preupgm.myfun2(['foo', 'bar'])

 *  Bash:

        preupgm_myfun foo.conf
        preupgm_myfun <foo.conf


Error handling
--------------

 *  Python: In case of error, `preupgm.PreupgException` is thrown:

        def myfun(foo):
            if foo.startswith('/'):
                raise PreupgException('Absolute paths are not allowed: %s' % foo)
                # note: logging is not necessary as it is expected to
                #       be handled by preupg framework (wrapper...)
            else:
                # do something

 *  Bash: In case of error, function must log error condition and return
    with status 2 on usage errors, 3 on external errors and 4 if an internal
    bug is detected:

        preupgm_myfun() {
            local foo=$1
            case $foo in
                /*)     preupgm_error('Absolute paths are not allowed: $foo')
                        return 2 ;;
            esac
            # do something
        }


Results
-------

### Output - boolean functions ###

 *  Python:

        def is_ok(foo):
            if foo ...:
                return True
            return False

 *  Bash:

        is_ok() {
            local foo=$1
            test ... $foo && return 0
            return 1
        }

    (Note that higher statuses are reserved for errors; this is not
    illustrated here for sake of brevity.)


### Output - listing ###


 *  Python: just list of strings without newlines:

        def list_foo(bar):
            return ['baz', 'qux', 'quux']

 *  Bash:

        def list_foo(bar):
            echo baz
            echo qux
            echo quux

