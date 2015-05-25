#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013, 2014 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
# Modified to allow ISim simulation by Lucas Russo (lucas.russo@lnls.br)
# Multi-tool support by Javier D. Garcia-Lasheras (javier@garcialasheras.com) 
#
# This file is part of Hdlmake.
#
# Hdlmake is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hdlmake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Hdlmake.  If not, see <http://www.gnu.org/licenses/>.

import os

from . import fetch


class _StaticClassVariable():
    pass

_m = _StaticClassVariable()
_m.initialized = False


class MakefileWriter(object):
    
    def __init__(self, filename=None):
        self._file = None
        if filename:
            self._filename = filename
        else:
            self._filename = "Makefile"

    def __del__(self):
        if self._file:
            self._file.close()


    def initialize(self):
        if not _m.initialized:
            if os.path.exists(self._filename):
                if os.path.isfile(self._filename):
                    os.remove(self._filename)
                elif os.path.isdir(self._filename):
                    os.rmdir(self._filename)

            self._file = open(self._filename, "a+")
            _m.initialized = True
            self.writeln("########################################")
            self.writeln("#  This file was generated by hdlmake  #")
            self.writeln("#  http://ohwr.org/projects/hdl-make/  #")
            self.writeln("########################################")
            self.writeln()
        elif not self._file:
            self._file = open(self._filename, "a+")


    def write(self, line=None):
        if not _m.initialized:
            self.initialize()
        self._file.write(line)


    def writeln(self, text=None):
        if text is None:
            self.write("\n")
        else:
            self.write(text+"\n")


    def generate_fetch_makefile(self, modules_pool):
        rp = os.path.relpath
        self.write("#target for fetching all modules stored in repositories\n")
        self.write("fetch: ")
        self.write(' \\\n'.join(["__"+m.basename+"_fetch" for m in modules_pool if m.source in (fetch.SVN, fetch.GIT)]))
        self.write("\n\n")

        for module in modules_pool:
            basename = module.basename
            if module.source == fetch.SVN:
                self.write("__"+basename+"_fetch:\n")
                self.write("\t\tmkdir -p %s\n" % rp(module.fetchto))
                self.write("\t\tPWD=$(shell pwd) ")
                self.write("cd " + rp(module.fetchto) + ' && ')
                c = "svn checkout {0}{1}"
                if module.revision:
                    c = c.format(module.url, "@"+module.revision)
                else:
                    c = c.format(module.url, "")
                self.write(c)
                self.write("; cd $(PWD) \n\n")

            elif module.source == fetch.GIT:
                self.write("__"+basename+"_fetch:\n")
                self.write("\t\tmkdir -p %s\n" % rp(module.fetchto))
                self.write("\t\t")
                self.write("PWD=$(shell pwd) ")
                self.write("cd " + rp(module.fetchto) + ' && ')
                self.write("if [ -d " + basename + " ]; then cd " + basename + ' && ')
                self.write("git pull ")
                if module.revision:
                    self.write(" && git checkout " + module.revision + '; ')
                self.write("else git clone " + module.url + ' && ')
                if module.revision:
                    self.write("cd " + basename + " && git checkout " + module.revision + '; fi; ')
                self.write("cd $(PWD) \n\n")

