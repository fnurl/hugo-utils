#!/usr/bin/env python3

"""Update lastmod in YAML frontmatter of a Hugo markdown file.

TODO: Use watchdog and also watch for file changes.
"""



import sys
import fileinput
from datetime import datetime
from dateutil import tz

debug = False
dryrun = False
verbose = False
output_filename = ""

def get_local_isotime():
    """Return a string with the ISO-formatted local time with timezone info."""
    fmt = "%Y-%m-%dT%H:%M:%S"
    offset = datetime.now(tz.tzlocal()).strftime("%z")
    offset = offset[:3] + ":" + offset[3:]
    return datetime.now(tz.tzlocal()).strftime(fmt) + offset


def get_new_lastmod(timestr):
    """Return a new lastmod string given a time as a string."""
    return "lastmod: " + timestr + "\n"

def output(outputstr, buffer):
    """Cache outputstr to buffer (append)."""
    buffer.append(outputstr)


def update_lastmod():
    """Replace the lastmod YAML property with a current one.

    If no lastmod property is found, one is added to the end of the
    YAML frontmatter block."""

    global verbose, debug, dryrun, output_filename

    new_lastmod = get_new_lastmod(get_local_isotime())
    in_yaml = False
    lastmod_found = False
    filename = None
    output_buffer = []
    
    with fileinput.input() as f_input:
        for line in f_input:

            # save filename if not reading from stdin
            if filename == None:
                if not fileinput.isstdin():
                    filename = fileinput.filename()
                    if verbose:
                        sys.stderr.write("Reading from file: '" + filename + "' ")
                else:
                    if verbose:
                        sys.stderr.write("Reading from stdin: ")
                    filename = False

            if debug:
                sys.stderr.write("\nDEBUG: " + repr(line))
            #else:
            #    sys.stderr.write(".")

            # start/end of YAML block detected
            # in_yaml == None at beginning, True if we are inside a YAML
            # block. set in_yaml to False when we exit the YAML block. 
            # if at end of YAML block and no lastmod was modified, we insert
            # a lastmod before the end of the to YAML block
            if line.startswith("---"):
                if in_yaml:
                    in_yaml = False
                    if not lastmod_found:
                        output(new_lastmod, output_buffer)
                else:
                    in_yaml = True

            # change an existing lastmod line, don't pass original line
            elif in_yaml and line.startswith("lastmod"):
                lastmod_found = True
                output(new_lastmod, output_buffer)
                continue

            # pass original line
            output(line, output_buffer)

    # output time - default is stdout
    save_file = sys.stdout

    # if a file was modified. i.e. filename is a string, not False/None
    if filename and verbose:
        sys.stderr.write("\nRead " + str(len(output_buffer)) + " lines from file '" + filename + "'.\n")
    elif verbose:
        sys.stderr.write("\nRead " + str(len(output_buffer)) + " lines from stdin.\n")

    # if no filename was recieved via the flags -o or --output
    if output_filename == "":
        output_filename = filename

    # output_filename found
    if output_filename:
        # output_filename but dryrun
        if dryrun:
            if verbose:
                sys.stderr.write("Dryrun: Not writing to '" + output_filename + "'\n")
        else:
            if verbose:
                sys.stderr.write("Saving to '" + output_filename + "\n")
            save_file = open(output_filename, 'w')

        # open file to save to

    # output to stdout
    #else:
    #    if verbose:
    #        sys.stderr.write("Output to stdout.")

    if not dryrun:
        for line in output_buffer:
            save_file.write(line)
        if not (save_file is sys.stdout):
            save_file.close()


# run if called from the command line
if __name__ == '__main__':
    # options to remove as not to confuse fileinput.input() later on.
    remove_args = []

    # take care of options
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg == "--verbose" or arg == "-v":
                remove_args.append(arg)
                verbose = True
            elif arg == "--debug" or arg == "-d":
                remove_args.append(arg)
                debug = True
            elif arg == "--dryrun" or arg == "-n":
                remove_args.append(arg)
                dryrun = True
            elif arg.startswith("--watch") or arg.startswith("-w"):
                remove_args.append(arg)
                if arg.find("=") != -1:
                    watch = True
                    watch_dir = arg[arg.find("=")+1]
                    if verbose:
                        sys.stderr.write("Watch dir: " + watch_dir)
                else:
                    sys.stderr.write("No watch dir found.\n")
                    sys.exit(1)
            elif arg.startswith("--output") or arg.startswith("-o"):
                remove_args.append(arg)
                if arg.find("=") != -1:
                    output_filename = arg[arg.find("=")+1]
                    if verbose:
                        sys.stderr.write("Output file: " + output_filename)
                else:
                    sys.stderr.write("No output filename found.\n")
                    sys.exit(1)

    # remove options we have used
    for arg_to_remove in remove_args:
        sys.argv.remove(arg_to_remove)

    try:
        update_lastmod()
    except KeyboardInterrupt:
        sys.stderr.write("\nctrl-c recieved.\n")