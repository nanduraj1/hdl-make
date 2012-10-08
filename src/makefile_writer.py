#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2011 Pawel Szostek (pawel.szostek@cern.ch)
#
#    This source code is free software; you can redistribute it
#    and/or modify it in source code form under the terms of the GNU
#    General Public License as published by the Free Software
#    Foundation; either version 2 of the License, or (at your option)
#    any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA
#
# Modified to allow iSim simulation by Lucas Russo (lucas.russo@lnls.br)

import os
import string

class MakefileWriter(object):
    def __init__(self, filename):
        self._file = None
        self._filename = filename
        self._is_initialized = False

    def __del__(self):
        if self._is_initialized:
            self._file.close()

    def initialize(self):
        if not self._is_initialized:
            self._file = open(self._filename, "w")
            self.writeln("########################################")
            self.writeln("#  This file was generated by hdlmake  #")
            self.writeln("#  http://ohwr.org/projects/hdl-make/  #")
            self.writeln("########################################")
            self.writeln()
            self._is_initialized = True
        else:
            pass

    def write(self, line=None):
        self._file.write(line)

    def writeln(self, text=None):
        if text == None:
            self._file.write("\n")
        else:
            self._file.write(text+"\n")

    def reset_file(self, filename):
        self._file.close()
        self._file = open(filename, "w")

    def generate_remote_synthesis_makefile(self, files, name, cwd, user, server, ise_path):
        import path 
        if name == None:
            import random
            name = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(8))
        user_tmpl = "USER:={0}"
        server_tmpl = "SERVER:={0}"
        port_tmpl = "PORT:=22"
        remote_name_tmpl = "R_NAME:={0}"
        files_tmpl = "FILES := {0}"

        if  user == None:
            user_tmpl = user_tmpl.format("$(HDLMAKE_USER)#take the value from the environment")
            test_tmpl = """__test_for_remote_synthesis_variables:
ifeq (x$(USER),x)
\t@echo "Remote synthesis user is not set. You can set it by editing variable USER in the makefile." && false
endif
ifeq (x$(SERVER),x)
\t@echo "Remote synthesis server is not set. You can set it by editing variable SERVER in the makefile." && false
endif
"""
        else:
            user_tmpl = user_tmpl.format(user)
            test_tmpl = "__test_for_remote_synthesis_variables:\n\t\ttrue #dummy\n"
            
        if server == None:
            server_tmpl = server_tmpl.format("$(HDLMAKE_SERVER)#take the value from the environment")
        else:
            server_tmpl = server_tmpl.format(server)
            
        remote_name_tmpl = remote_name_tmpl.format(name)
        self.initialize()
        self.writeln(user_tmpl)
        self.writeln(server_tmpl)
        self.writeln(remote_name_tmpl)
        self.writeln(port_tmpl)
        self.writeln()
        self.writeln(test_tmpl)
        self.writeln("CWD := $(shell pwd)")
        self.writeln("")
        self.writeln(files_tmpl.format(' \\\n'.join([s.rel_path() for s in files])))
        self.writeln("")
        self.writeln("#target for running simulation in the remote location")
        self.writeln("remote: __test_for_remote_synthesis_variables __send __do_synthesis __send_back")
        self.writeln("__send_back: __do_synthesis")
        self.writeln("__do_synthesis: __send")
        self.writeln("__send: __test_for_remote_synthesis_variables")
        self.writeln("")

        mkdir_cmd = "ssh $(USER)@$(SERVER) 'mkdir -p $(R_NAME)'"
        rsync_cmd = "rsync -e 'ssh -p $(PORT)' -Ravl $(foreach file, $(FILES), $(shell readlink -f $(file))) $(USER)@$(SERVER):$(R_NAME)"
        send_cmd = "__send:\n\t\t{0}\n\t\t{1}".format(mkdir_cmd, rsync_cmd)
        self.writeln(send_cmd)
        self.writeln("")

        tcl = "run.tcl"
        synthesis_cmd = "__do_synthesis:\n\t\t"
        synthesis_cmd += "ssh $(USER)@$(SERVER) 'cd $(R_NAME)$(CWD) && {0}xtclsh {1}'"
        self.writeln(synthesis_cmd.format(ise_path, tcl))

        self.writeln()
 
        send_back_cmd = "__send_back: \n\t\tcd .. && rsync -e 'ssh -p $(PORT)' -avl $(USER)@$(SERVER):$(R_NAME)$(CWD) . && cd $(CWD)"
        self.write(send_back_cmd)
        self.write("\n\n")

        cln_cmd = "cleanremote:\n\t\tssh $(USER)@$(SERVER) 'rm -rf $(R_NAME)'"
        self.writeln("#target for removing stuff from the remote location")
        self.writeln(cln_cmd)
        self.writeln()

    def generate_quartus_makefile(self, top_mod):
        pass

    def generate_ise_makefile(self, top_mod, ise_path):
        import path 
        mk_text = """PROJECT := {1}
ISE_CRAP := \
*.b \
{0}_summary.html \
*.tcl \
{0}.bld \
{0}.cmd_log \
*.drc \
{0}.lso \
*.ncd \
{0}.ngc \
{0}.ngd \
{0}.ngr \
{0}.pad \
{0}.par \
{0}.pcf \
{0}.prj \
{0}.ptwx \
{0}.stx \
{0}.syr \
{0}.twr \
{0}.twx \
{0}.gise \
{0}.unroutes \
{0}.ut \
{0}.xpi \
{0}.xst \
{0}_bitgen.xwbt \
{0}_envsettings.html \
{0}_guide.ncd \
{0}_map.map \
{0}_map.mrp \
{0}_map.ncd \
{0}_map.ngm \
{0}_map.xrpt \
{0}_ngdbuild.xrpt \
{0}_pad.csv \
{0}_pad.txt \
{0}_par.xrpt \
{0}_summary.xml \
{0}_usage.xml \
{0}_xst.xrpt \
usage_statistics_webtalk.html \
webtalk.log \
webtalk_pn.xml \
run.tcl
"""
        mk_text2 = """
#target for performing local synthesis
local:
\t\techo "project open $(PROJECT)" > run.tcl
\t\techo "process run {Generate Programming File} -force rerun_all" >> run.tcl
"""

        mk_text3 = """
#target for cleaing all intermediate stuff
clean:
\t\trm -f $(ISE_CRAP)
\t\trm -rf xst xlnx_auto_*_xdb iseconfig _xmsgs _ngo
    
#target for cleaning final files
mrproper:
\t\trm -f *.bit *.bin *.mcs

"""
        self.initialize()
        self.write(mk_text.format(top_mod.syn_top, top_mod.syn_project))

        xtcl_tmp = "\t\t{0}xtclsh run.tcl"
        self.write(mk_text2)
        self.writeln(xtcl_tmp.format(ise_path))
        self.writeln()
        self.write(mk_text3)
        import global_mod
#        for m in global_mod.mod_pool:
        for f in global_mod.top_module.incl_makefiles:
            if os.path.exists(f):
                self.write("include " + f + "\n")

    def generate_fetch_makefile(self, modules_pool):
        rp = os.path.relpath
        self.initialize()
        self.write("#target for fetching all modules stored in repositories\n")
        self.write("fetch: ")
        self.write(' \\\n'.join(["__"+m.basename+"_fetch" for m in modules_pool if m.source in ["svn","git"]]))
        self.write("\n\n")

        for module in modules_pool:
            basename = module.basename
            if module.source == "svn":
                self.write("__"+basename+"_fetch:\n")
                self.write("\t\t")
                self.write("PWD=$(shell pwd); ")
                self.write("cd " + rp(module.fetchto) + '; ')
                c = "svn checkout {0}{1} {2};"
                if module.revision:
                    c=c.format(module.url, "@"+module.revision, module.basename)
                else:
                    c=c.format(module.url, "", module.basename)
                self.write(c)
                self.write("cd $(PWD) \n\n")

            elif module.source == "git":
                self.write("__"+basename+"_fetch:\n")
                self.write("\t\t")
                self.write("PWD=$(shell pwd); ")
                self.write("cd " + rp(module.fetchto) + '; ')
                self.write("if [ -d " + basename + " ]; then cd " + basename + '; ')
                self.write("git pull; ")
                if module.revision:
                    self.write("git checkout " + module.revision +';')
                self.write("else git clone "+ module.url + '; fi; ')
                if module.revision:
                    self.write("git checkout " + module.revision + ';')
                self.write("cd $(PWD) \n\n")

<<<<<<< HEAD
    def generate_iverilog_makefile(self, fileset, top_module, modules_pool):
        from srcfile import VerilogFile, VHDLFile, SVFile
        #open the file and write the above preambule (part 1)
        self.initialize()
        rp = os.path.relpath
        import global_mod
#        for m in global_mod.mod_pool:
        for f in global_mod.top_module.incl_makefiles:
            if os.path.exists(f):
                self.writeln("include " + f)
        libs = set(f.library for f in fileset)
        target_list = []
        for vl in fileset.filter(VerilogFile):
            rel_dir_path = os.path.dirname(vl.rel_path())
            if rel_dir_path:
                rel_dir_path = rel_dir_path + '/'
            target_name = os.path.join(rel_dir_path+vl.purename)
            target_list.append(target_name)
#            dependencies_string = ' '.join([f.rel_path() for f in vl.dep_depends_on if (f.name != vl.name) and not f.name
            dependencies_string = ' '.join([f.rel_path() for f in vl.dep_depends_on if (f.name != vl.name)])
            include_dirs = list(set([os.path.dirname(f.rel_path()) for f in vl.dep_depends_on if f.name.endswith("vh")]))
            while "" in include_dirs:
                include_dirs.remove("")
            include_dir_string=" -I".join(include_dirs)
            if include_dir_string:
                include_dir_string = ' -I'+include_dir_string
                self.writeln("VFLAGS_"+target_name+"="+include_dir_string)
            self.writeln(target_name+"_deps = "+dependencies_string)
            # self.write(target_name+': ')
            # self.write(vl.rel_path() + ' ')
            # self.writeln("$("+target_name+"_deps)")
            # self.write("\t\t$(VERILOG_COMP) -y"+vl.library)
            # if isinstance(vl, SVFile):
            #     self.write(" -sv ")
            # incdir = " "
            # incdir += " -I"
            # incdir += ' -I'.join(vl.include_dirs)
            # self.writeln(include_dir_string)
        sim_only_files = []
        for m in global_mod.mod_pool:
            for f in m.sim_only_files:
                sim_only_files.append(f.name)
        top_name = global_mod.top_module.syn_top
        top_name_syn_deps = []

        bit_targets = []
        for m in global_mod.mod_pool:
            bit_targets = bit_targets + m.bit_file_targets
        for bt in bit_targets:
            bt = bt.purename
            bt_syn_deps = []
            # This can perhaps be done faster (?)
            for vl in fileset.filter(VerilogFile):
                if vl.purename == bt:
                    for f in vl.dep_depends_on:
                        if (f.name != vl.name and f.name not in sim_only_files):
                            bt_syn_deps.append(f)
            self.writeln(bt+'syn_deps = '+ ' '.join([f.rel_path() for f in bt_syn_deps]))
            if not os.path.exists(bt+".ucf"):
                print "WARNING: The file " +bt+".ucf doesn't exist!"
            self.writeln(bt+".bit:\t"+bt+".v $("+bt+"syn_deps) "+bt+".ucf")
            part=(global_mod.top_module.syn_device+'-'+
                  global_mod.top_module.syn_package+
                  global_mod.top_module.syn_grade)
            self.writeln("\tPART="+part+" $(SYNTH) "+bt+" $^")
            self.writeln("\tmv _xilinx/"+bt+".bit $@")

        self.writeln("clean:")
        self.writeln("\t\trm -f "+" ".join(target_list)+"\n\t\trm -rf _xilinx")


    def generate_modelsim_makefile(self, fileset, top_module):
=======
    def generate_vsim_makefile(self, fileset, top_module):
>>>>>>> generate_modelsim_makefile call: fix name calling throughout the program
        from srcfile import VerilogFile, VHDLFile, SVFile
        from flow import ModelsiminiReader
        make_preambule_p1 = """## variables #############################
PWD := $(shell pwd)

MODELSIM_INI_PATH := """ + ModelsiminiReader.modelsim_ini_dir() + """

VCOM_FLAGS := -quiet -modelsimini modelsim.ini
VSIM_FLAGS :=
VLOG_FLAGS := -quiet -modelsimini modelsim.ini """ + self.__get_rid_of_incdirs(top_module.vlog_opt) + """
""" 
        make_preambule_p2 = """## rules #################################
sim: modelsim.ini $(LIB_IND) $(VERILOG_OBJ) $(VHDL_OBJ)
$(VERILOG_OBJ): $(VHDL_OBJ) 
$(VHDL_OBJ): $(LIB_IND) modelsim.ini

modelsim.ini: $(MODELSIM_INI_PATH)/modelsim.ini
\t\tcp $< .
clean:
\t\trm -rf ./modelsim.ini $(LIBS)
.PHONY: clean

"""
        #open the file and write the above preambule (part 1)
        self.initialize()
        self.write(make_preambule_p1)

        rp = os.path.relpath
        self.write("VERILOG_SRC := ")
        for vl in fileset.filter(VerilogFile):
            self.write(vl.rel_path() + " \\\n")
        self.write("\n")

        self.write("VERILOG_OBJ := ")
        for vl in fileset.filter(VerilogFile):
            #make a file compilation indicator (these .dat files are made even if
            #the compilation process fails) and add an ending according to file's
            #extension (.sv and .vhd files may have the same corename and this
            #causes a mess
            self.write(os.path.join(vl.library, vl.purename, "."+vl.purename+"_"+vl.extension()) + " \\\n")
        self.write('\n')

        libs = set(f.library for f in fileset)

        self.write("VHDL_SRC := ")
        for vhdl in fileset.filter(VHDLFile):
            self.write(vhdl.rel_path() + " \\\n")
        self.writeln()

        #list vhdl objects (_primary.dat files)
        self.write("VHDL_OBJ := ")
        for vhdl in fileset.filter(VHDLFile):
            #file compilation indicator (important: add _vhd ending)
            self.write(os.path.join(vhdl.library, vhdl.purename,"."+vhdl.purename+"_"+vhdl.extension()) + " \\\n")
        self.write('\n')

        self.write('LIBS := ')
        self.write(' '.join(libs))
        self.write('\n')
        #tell how to make libraries
        self.write('LIB_IND := ')
        self.write(' '.join([lib+"/."+lib for lib in libs]))
        self.write('\n')
        self.write(make_preambule_p2)

        for lib in libs:
            self.write(lib+"/."+lib+":\n")
            self.write(' '.join(["\t(vlib",  lib, "&&", "vmap", "-modelsimini modelsim.ini", 
            lib, "&&", "touch", lib+"/."+lib,")"]))

            self.write(' '.join(["||", "rm -rf", lib, "\n"]))
            self.write('\n')

        #rules for all _primary.dat files for sv
        for vl in fileset.filter(VerilogFile):
            self.write(os.path.join(vl.library, vl.purename, '.'+vl.purename+"_"+vl.extension())+': ')
            self.write(vl.rel_path() + ' ')
            self.writeln(' '.join([f.rel_path() for f in vl.dep_depends_on]))
            self.write("\t\tvlog -work "+vl.library)
            self.write(" $(VLOG_FLAGS) ")
            if isinstance(vl, SVFile):
                self.write(" -sv ")
            incdir = "+incdir+"
            incdir += '+'.join(vl.include_dirs)
            incdir += " "
            self.write(incdir)
            self.writeln(vl.vlog_opt+" $<")
            self.write("\t\t@mkdir -p $(dir $@)")
            self.writeln(" && touch $@ \n\n")
        self.write("\n")

        #list rules for all _primary.dat files for vhdl
        for vhdl in fileset.filter(VHDLFile):
            lib = vhdl.library
            purename = vhdl.purename 
            #each .dat depends on corresponding .vhd file
            self.write(os.path.join(lib, purename, "."+purename+"_"+ vhdl.extension()) + ": " + vhdl.rel_path())
            for dep_file in vhdl.dep_depends_on:
                name = dep_file.purename
                self.write(" \\\n"+ os.path.join(dep_file.library, name, "."+name+"_vhd"))
            self.writeln()
            self.writeln(' '.join(["\t\tvcom $(VCOM_FLAGS)", vhdl.vcom_opt, "-work", lib, "$< "]))
            self.writeln("\t\t@mkdir -p $(dir $@) && touch $@\n")
            self.writeln()

# Modification here
    def generate_isim_makefile(self, fileset, top_module):
        from srcfile import VerilogFile, VHDLFile, SVFile
        from flow import XilinxsiminiReader
        make_preambule_p1 = """## variables #############################
PWD := $(shell pwd)
TOP_MODULE := 
FUSE_OUTPUT ?= isim_proj

XILINX_INI_PATH := """ + XilinxsiminiReader.xilinxsim_ini_dir() + """

VHPCOMP_FLAGS := -intstyle default -incremental -initfile xilinxsim.ini
ISIM_FLAGS :=
VLOGCOMP_FLAGS := -intstyle default -incremental -initfile xilinxsim.ini """ + self.__get_rid_of_incdirs(top_module.vlog_opt) + """
""" 
        make_preambule_p2 = """## rules #################################
sim: xilinxsim.ini $(LIB_IND) $(VERILOG_OBJ) $(VHDL_OBJ)
$(VERILOG_OBJ): $(VHDL_OBJ) 
$(VHDL_OBJ): $(LIB_IND) xilinxsim.ini

xilinxsim.ini: $(XILINX_INI_PATH)/xilinxsim.ini
\t\tcp $< .
fuse: ;
ifeq ($(TOP_MODULE),)
\t\t@echo \"Environment variable TOP_MODULE not set!\"
else
\t\tfuse work.$(TOP_MODULE) -intstyle ise -incremental -o $(FUSE_OUTPUT)
endif
clean:
\t\trm -rf ./xilinxsim.ini $(LIBS) fuse.xmsgs fuse.log fuseRelaunch.cmd isim isim.log \
isim.wdb 
.PHONY: clean

"""
        #open the file and write the above preambule (part 1)
        self.initialize()
        self.write(make_preambule_p1)

        rp = os.path.relpath
        self.write("VERILOG_SRC := ")
        for vl in fileset.filter(VerilogFile):
            self.write(vl.rel_path() + " \\\n")
        self.write("\n")

        self.write("VERILOG_OBJ := ")
        for vl in fileset.filter(VerilogFile):
            #make a file compilation indicator (these .dat files are made even if
            #the compilation process fails) and add an ending according to file's
            #extension (.sv and .vhd files may have the same corename and this
            #causes a mess
            self.write(os.path.join(vl.library, vl.purename, "."+vl.purename+"_"+vl.extension()) + " \\\n")
        self.write('\n')

        libs = set(f.library for f in fileset)

        self.write("VHDL_SRC := ")
        for vhdl in fileset.filter(VHDLFile):
            self.write(vhdl.rel_path() + " \\\n")
        self.writeln()

        #list vhdl objects (_primary.dat files)
        self.write("VHDL_OBJ := ")
        for vhdl in fileset.filter(VHDLFile):
            #file compilation indicator (important: add _vhd ending)
            self.write(os.path.join(vhdl.library, vhdl.purename,"."+vhdl.purename+"_"+vhdl.extension()) + " \\\n")
        self.write('\n')

        self.write('LIBS := ')
        self.write(' '.join(libs))
        self.write('\n')
        #tell how to make libraries
        self.write('LIB_IND := ')
        self.write(' '.join([lib+"/."+lib for lib in libs]))
        self.write('\n')
        self.write(make_preambule_p2)

        # ISim does not have a vmap command to insert additional libraries in 
        #.ini file. 
        for lib in libs:
            self.write(lib+"/."+lib+":\n")
            self.write(' '.join(["\t(mkdir", lib, "&&", "touch", lib+"/."+lib+" "]))
            #self.write(' '.join(["&&", "echo", "\""+lib+"="+lib+"/."+lib+"\" ", ">>", "xilinxsim.ini) "]))
            self.write(' '.join(["&&", "echo", "\""+lib+"="+lib+"\" ", ">>", "xilinxsim.ini) "]))
            self.write(' '.join(["||", "rm -rf", lib, "\n"]))
            self.write('\n')

            # Modify xilinxsim.ini file by including the extra local libraries
            #self.write(' '.join(["\t(echo """, lib+"="+lib+"/."+lib, ">>", "${XILINX_INI_PATH}/xilinxsim.ini"]))

        #rules for all _primary.dat files for sv
        #incdir = ""
        objs = []
        for vl in fileset.filter(VerilogFile):
            comp_obj = os.path.join(vl.library, vl.purename)
            objs.append(comp_obj)
            #self.write(os.path.join(vl.library, vl.purename, '.'+vl.purename+"_"+vl.extension())+': ')
            #self.writeln(".PHONY: " + os.path.join(comp_obj, '.'+vl.purename+"_"+vl.extension()))
            self.write(os.path.join(comp_obj, '.'+vl.purename+"_"+vl.extension())+': ')
            self.write(vl.rel_path() + ' ')
            self.writeln(' '.join([f.rel_path() for f in vl.dep_depends_on]))
            self.write("\t\tvlogcomp -work "+vl.library+"=./"+vl.library)
            self.write(" $(VLOGCOMP_FLAGS) ")
            #if isinstance(vl, SVFile):
            #    self.write(" -sv ")
            incdir = "-i "
            incdir += " -i ".join(vl.include_dirs)
            incdir += " "
            self.write(incdir)
            self.writeln(vl.vlog_opt+" $<")
            self.write("\t\t@mkdir -p $(dir $@)")
            self.writeln(" && touch $@ \n\n")
        self.write("\n")

        #list rules for all _primary.dat files for vhdl
        for vhdl in fileset.filter(VHDLFile):
            lib = vhdl.library
            purename = vhdl.purename 
            comp_obj = os.path.join(lib, purename)
            objs.append(comp_obj)
            #each .dat depends on corresponding .vhd file and its dependencies
            #self.write(os.path.join(lib, purename, "."+purename+"_"+ vhdl.extension()) + ": "+ vhdl.rel_path()+" " + os.path.join(lib, purename, "."+purename) + '\n')
            #self.writeln(".PHONY: " + os.path.join(comp_obj, "."+purename+"_"+ vhdl.extension()))
            self.write(os.path.join(comp_obj, "."+purename+"_"+ vhdl.extension()) + ": "+ vhdl.rel_path()+" " + os.path.join(lib, purename, "."+purename) + '\n')
            self.writeln(' '.join(["\t\tvhpcomp $(VHPCOMP_FLAGS)", vhdl.vcom_opt, "-work", lib+"=./"+lib, "$< "]))
            self.writeln("\t\t@mkdir -p $(dir $@) && touch $@\n")
            self.writeln()
            # dependency meta-target. This rule just list the dependencies of the above file
            #if len(vhdl.dep_depends_on) != 0:
            #self.writeln(".PHONY: " + os.path.join(lib, purename, "."+purename))
# Touch the dependency file as well. In this way, "make" will recompile only what is needed (out of date)
            self.write(os.path.join(lib, purename, "."+purename) +":")
            for dep_file in vhdl.dep_depends_on:
                name = dep_file.purename
                self.write(" \\\n"+ os.path.join(dep_file.library, name, "."+name+ "_" + vhdl.extension()))
            #self.write('\n\n')
            self.write('\n')
            self.writeln("\t\t@mkdir -p $(dir $@) && touch $@\n")

            # Fuse rule
            #self.write("fuse:")
            #self.write("ifeq ($(TOP_DESIGN),)")
            #self.write("\t\techo \"Environment variable TOP_DESIGN not set!\"")
            #self.write("else")
            #self.write("\t\tfuse -intstyle ise -incremental")
            #self.write(".PHONY: $(FUSE_PROJ)")

    def __get_rid_of_incdirs(self, vlog_opt):
        vlog_opt_vsim = self.__get_rid_of_vsim_incdirs(vlog_opt)
        return self.__get_rid_of_isim_incdirs(vlog_opt_vsim)

    def __get_rid_of_vsim_incdirs(self, vlog_opt):
        vlog_opt = self.__emit_string(vlog_opt)
        vlogs = vlog_opt.split(' ')
        ret = []
        for v in vlogs:
            if not v.startswith("+incdir+"):
                ret.append(v)
        return ' '.join(ret)

    # FIX. Make it more robust
    def __get_rid_of_isim_incdirs(self, vlog_opt):
        vlog_opt = self.__emit_string(vlog_opt)
        vlogs = vlog_opt.split(' ')
        ret = []
        skip = False
        for v in vlogs:
            if skip:
                skip = False
                continue

            if not v.startswith("-i"):
                ret.append(v)
            else:
                skip = True
        return ' '.join(ret)

    def __emit_string(self, s):
        if not s:
            return ""
        else:
            return s

    def __modelsim_ini_path(self):
        vsim_path = os.popen("which vsim").read().strip()
        bin_path = os.path.dirname(vsim_path)
        return os.path.abspath(bin_path+"/../")
