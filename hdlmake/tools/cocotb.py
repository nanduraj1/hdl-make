#!/usr/bin/env python3

"""Module providing support for cocotb"""

from __future__ import absolute_import


from .makefilesim import MakefileSim
from ..sourcefiles.srcfile import VerilogFile, SVFile


def _check_simulation_manifest(top_manifest):
    """Check if the simulation keys are provided by the top manifest"""
    if top_manifest.manifest_dict.get("sim_top") is None:
        raise Exception("sim_top variable must be set in the top manifest.")


class ToolCocotb(MakefileSim):

    """Class providing the interface for Cocotb"""

    TOOL_INFO = {
        'name': 'Cocotb',
        'id': 'cocotb',
        'windows_bin': None,
        'linux_bin': 'cocotb-config'}

    HDL_FILES = {VerilogFile: '', SVFile: ''}

    def _add_wpwd(self, path):
        if not path.startswith('/'):
            return '$(WPWD)/' + path

    def write_makefile(self, top_manifest, fileset, filename=None):
        """Execute the simulation action"""
        _check_simulation_manifest(top_manifest)
        self.makefile_setup(top_manifest, fileset, filename=filename)
        self.makefile_check_tool('sim_path')
        self._makefile_sim_top()
        self._makefile_sim_options()
        self._makefile_sim_sources()
        self._makefile_sim_compilation()
        self.makefile_close()

    def _makefile_sim_sources_lang(self, name, klass):
        """Generic method to write the simulation Makefile HDL sources"""
        fileset = self.fileset
        self.write("{}_SOURCES += ".format(name))
        for vlog in fileset.filter(klass).sort():
            self.writeln(self._add_wpwd(vlog.rel_path()) + " \\")

        if name == 'VERILOG':
            extra_srcs = self.manifest_dict.get('extra_srcs', None)
            if extra_srcs:
                for src in extra_srcs:
                    self.writeln(self._add_wpwd(src) + " \\")
        self.writeln()

    def __init__(self):
        super(ToolCocotb, self).__init__()
        # These are variables that will be set in the makefile
        # The key is the variable name, and the value is the variable value
        self.custom_variables = {}
        # Additional sim dependencies (e.g. modelsim.ini)
        self.additional_deps = []
        # These are files copied into your working directory by a make rule
        # The key is the filename, the value is the file source path
        self.copy_rules = {}

    def _makefile_sim_options(self):
        self.write("""
PWD=$(shell pwd)

ifeq ($(OS),Msys)
WPWD=$(shell sh -c 'pwd -W')
else
WPWD=$(shell pwd)
endif

""")

    def _makefile_sim_compilation(self):
        """Write a properly formatted Makefile for the simulator.
        The Makefile format is shared, but flags, dependencies, clean rules,
        etc are defined by the specific tool.
        """
        self.writeln("TOPLEVEL_LANG=verilog")

        cocotb_sim = self.manifest_dict.get('cocotb_sim', '')
        self.writeln("SIM ?= %s" % cocotb_sim)

        py_paths = self.manifest_dict.get('py_paths', None)
        py_paths = [self._add_wpwd(path) for path in py_paths]
        if py_paths:
            self.writeln('PYTHONPATH := {}:$(PYTHONPATH)'.format(':'.join(py_paths)))
        else:
            raise Exception("Need proper py_paths in Manifest.py\nGot {}".format(py_paths))

        self.writeln("TOPLEVEL := $(TOP_MODULE)")
        self.writeln("MODULE := $(TOP_MODULE)")
        self.writeln("EXTRA_ARGS += $(MORE_ARGS)")
        extra_args = self.manifest_dict.get('extra_args', None)
        if extra_args:
            self.writeln("EXTRA_ARGS += {}".format(extra_args))

        if self.manifest_dict.get("include_dirs") is not None:
            inc_dirs = self.manifest_dict.get("include_dirs")
            inc_dirs = [self._add_wpwd(path) for path in inc_dirs]
            inc_dirs_verilator = ("-I%s" % ' -I'.join(inc_dirs))
            inc_dirs_vsim = ("+incdir+%s" % ' +incdir+'.join(inc_dirs))

        else:
            inc_dirs_verilator = ''
            inc_dirs_vsim = ''

        self.write("""\n
ifeq ($(SIM), modelsim)
    ARCH=i686
    EXTRA_ARGS += {vsim}
else ifeq ($(SIM), verilator)
    EXTRA_ARGS += {verilator}
endif

include $(shell cocotb-config --makefiles)/Makefile.inc
include $(shell cocotb-config --makefiles)/Makefile.sim
\n""".format(vsim=inc_dirs_vsim, verilator=inc_dirs_verilator))
