#!/usr/bin/env python

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import argparse
import subprocess
import sys

import os_doc_tools


# NOTE(berendt): check_output as provided in Python 2.7.5 to make script
#                usable with Python < 2.7
def check_output(*popenargs, **kwargs):
    """Run command with arguments and return its output as a byte string.

    If the exit code was non-zero it raises a CalledProcessError.  The
    CalledProcessError object will have the return code in the returncode
    attribute and output in the output attribute.
    """
    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, it will be overridden.')
    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise subprocess.CalledProcessError(retcode, cmd, output=output)
    return output


def quote_xml(line):
    """Convert special characters for XML output."""

    return line.replace('&', '&amp;').replace('<', '&lt;')


def generate_heading(os_command, api_name, os_file):
    """Write DocBook file header.

    :param os_command: client command to document
    :param api_name:   string description of the API of os_command
    :param os_file:    open filehandle for output of DocBook file
    """

    print("Documenting '%s help'" % os_command)

    header = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<section xmlns=\"http://docbook.org/ns/docbook\"
    xmlns:xi=\"http://www.w3.org/2001/XInclude\"
    xmlns:xlink=\"http://www.w3.org/1999/xlink\" version=\"5.0\"
    xml:id=\"{0}client_commands\">

    <!-- This file is automatically generated, do not edit -->

    <?dbhtml stop-chunking?>

    <title>{0} commands</title>
    <para>The {0} client is the command-line interface (CLI) for the
         {1} and its extensions.</para>
    <para>For help on a specific <command>{0}</command>
       command, enter:
    </para>
    <screen><prompt>$</prompt> <userinput><command>{0}</command> \
<option>help</option> <replaceable>COMMAND</replaceable></userinput></screen>

    <section xml:id=\"{0}client_command_usage\">
       <title>{0} usage</title>\n"""

    os_file.write(header.format(os_command, api_name))


def generate_command(os_command, os_file):
    """Convert os_command --help to DocBook.

    :param os_command: client command to document
    :param os_file:    open filehandle for output of DocBook file
    """

    help_lines = check_output([os_command, "--help"]).split('\n')

    ignore_next_lines = False
    next_line_screen = True
    for line in help_lines:
        xline = quote_xml(line)
        if len(line) > 0 and line[0] != ' ':
            if '<subcommand>' in line:
                ignore_next_lines = False
                continue
            if 'Positional arguments' in line:
                ignore_next_lines = False
                next_line_screen = True
                continue
            if line.startswith(('Optional arguments:', 'Optional:',
                                'Options:')):
                os_file.write("</computeroutput></screen>\n")
                os_file.write("    </section>\n")
                os_file.write("    <section ")
                os_file.write("xml:id=\"%sclient_command_optional\">\n"
                              % os_command)
                os_file.write("        <title>%s optional arguments</title>\n"
                              % os_command)
                next_line_screen = True
                ignore_next_lines = False
                continue
            # swift
            if line.startswith('Examples:'):
                os_file.write("</computeroutput></screen>\n")
                os_file.write("    </section>\n")
                os_file.write("    <section ")
                os_file.write("xml:id=\"%sclient_command_examples\">\n"
                              % os_command)
                os_file.write("        <title>%s examples</title>\n"
                              % os_command)
                next_line_screen = True
                continue
            continue
        if '<subcommand> ...' in line:
            os_file.write("%s</computeroutput></screen>\n" % xline)
            os_file.write("    </section>\n")
            os_file.write("    <section xml:id=\"%sclient_command_pos\">\n"
                          % os_command)
            os_file.write("        <title>%s positional arguments</title>\n"
                          % os_command)
            ignore_next_lines = True
            continue
        if not ignore_next_lines:
            if next_line_screen:
                os_file.write("        <screen><computeroutput>%s\n" % xline)
                next_line_screen = False
            elif len(line) > 0:
                os_file.write("%s\n" % (xline))

    os_file.write("</computeroutput></screen>\n")
    os_file.write("    </section>\n")


def generate_subcommand(os_command, os_subcommand, os_file):
    """Convert os_command help os_subcommand to DocBook.

    :param os_command: client command to document
    :param os_subcommand: client subcommand to document
    :param os_file:    open filehandle for output of DocBook file
    """

    if os_command == "swift":
        help_lines = check_output([os_command, os_subcommand,
                                   "--help"]).split('\n')
    else:
        help_lines = check_output([os_command, "help",
                                   os_subcommand]).split('\n')

    os_file.write("    <section xml:id=\"%sclient_subcommand_%s\">\n"
                  % (os_command, os_subcommand))
    os_file.write("        <title>%s %s command</title>\n"
                  % (os_command, os_subcommand))

    next_line_screen = True
    for line in help_lines:
        xline = quote_xml(line)
        if next_line_screen:
            os_file.write("        <screen><computeroutput>%s\n" % xline)
            next_line_screen = False
        else:
            os_file.write("%s\n" % (xline))

    os_file.write("</computeroutput></screen>\n")
    os_file.write("    </section>\n")


def generate_subcommands(os_command, os_file, blacklist, only_subcommands):
    """Convert os_command help subcommands for all subcommands to DocBook.

    :param os_command: client command to document
    :param os_file:    open filehandle for output of DocBook file
    :param blacklist:  list of elements that will not be documented
    :param only_subcommands: if not empty, list of subcommands to document
    """

    print("Documenting '%s' subcommands..." % os_command)
    blacklist.append("bash-completion")
    blacklist.append("complete")
    blacklist.append("help")
    if not only_subcommands:
        all_options = check_output([os_command,
                                    "bash-completion"]).strip().split()
    else:
        all_options = only_subcommands

    subcommands = [o for o in all_options if not
                   (o.startswith('-') or o in blacklist)]
    for subcommand in sorted(subcommands):
        generate_subcommand(os_command, subcommand, os_file)
    print ("%d subcommands documented." % len(subcommands))


def generate_end(os_file):
    """Finish writing file.

    :param os_file:    open filehandle for output of DocBook file
    """

    print("Finished.\n")
    os_file.write("</section>\n")


def document_single_project(os_command):
    """Create documenation for os_command."""

    print ("Documenting '%s'" % os_command)

    blacklist = []
    subcommands = []
    if os_command == 'ceilometer':
        api_name = "OpenStack Telemetry API"
        blacklist = ["alarm-create"]
    elif os_command == 'cinder':
        api_name = "OpenStack Block Storage API"
    elif os_command == 'glance':
        api_name = 'OpenStack Image Service API'
        # Does not know about bash-completion yet, need to specify
        # subcommands manually
        subcommands = ["image-create", "image-delete", "image-list",
                       "image-show", "image-update", "member-create",
                       "member-delete", "member-list"]
    elif os_command == 'heat':
        api_name = "OpenStack Orchestration API"
        blacklist = ["create", "delete", "describe", "event",
                     "gettemplate", "list", "resource",
                     "update", "validate"]
    elif os_command == 'keystone':
        api_name = "OpenStack Identity API"
    elif os_command == 'neutron':
        api_name = "OpenStack Networking API"
    elif os_command == 'nova':
        api_name = "OpenStack Compute API"
        blacklist = ["add-floating-ip", "remove-floating-ip"]
    elif os_command == 'swift':
        api_name = "OpenStack Object Storage API"
        # Does not know about bash-completion yet, need to specify
        # subcommands manually
        subcommands = ["delete", "download", "list", "post",
                       "stat", "upload"]
    elif os_command == 'trove':
        api_name = "OpenStack Database API"
    else:
        print("Not yet handled command")
        sys.exit(-1)

    os_file = open("section_cli_" + os_command + "_commands.xml",
                   'w')
    generate_heading(os_command, api_name, os_file)
    generate_command(os_command, os_file)
    generate_subcommands(os_command, os_file, blacklist,
                         subcommands)
    generate_end(os_file)
    os_file.close()


def main():
    print("OpenStack Auto Documenting of Commands (using "
          "openstack-doc-tools version %s)\n"
          % os_doc_tools.__version__)

    parser = argparse.ArgumentParser(description="Generate DocBook XML files "
                                     "to document python-PROJECTclients")
    parser.add_argument('client', nargs='?',
                        help="OpenStack command to document")
    parser.add_argument("--all", help="Document all clients ",
                        action="store_true")
    prog_args = parser.parse_args()

    if prog_args.all:
        document_single_project("ceilometer")
        document_single_project("cinder")
        document_single_project("glance")
        document_single_project("heat")
        document_single_project("keystone")
        document_single_project("nova")
        document_single_project("neutron")
        document_single_project("swift")
        document_single_project("trove")
    elif prog_args.client is None:
        print("Pass the name of the client to document as argument.")
        sys.exit(1)
    else:
        document_single_project(prog_args.client)


if __name__ == "__main__":
    sys.exit(main())
