#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import msg as p
import global_mod
import path


class ModuleFetcher:

    def __init__(self):
        pass

    def fetch_single_module(self, module):
        involved_modules = []
        p.vprint("Fetching manifest: " + str(module.manifest))

        if(module.source == "local"):
            p.vprint("ModPath: " + module.path);
            module.parse_manifest()
        
        if module.root_module != None:
            root_module = module.root_module
            p.vprint("Encountered root manifest: " + str(root_module))
            new_modules = self.fetch_recursively(root_module)
            involved_modules.extend(new_modules)

        for i in module.local:
            p.vprint("Modules waiting in fetch queue:"+
            ' '.join([str(module.git), str(module.svn), str(module.local)]))

        for module in module.svn:
            p.vprint("[svn] Fetching to " + module.fetchto)
            path = self.__fetch_from_svn(module)
            module.path = path
            module.source = "local"
            module.isparsed = False
            p.vprint("[svn] Local path " + module.path)
            involved_modules.append(module)

        for module in module.git:
            p.vprint("[git] Fetching to " + module.fetchto)
            path = self.__fetch_from_git(module)
            module.path = path
            module.source = "local"
            module.isparsed = False
            module.manifest = module.search_for_manifest();
            p.vprint("[git] Local path " + module.path);
            involved_modules.append(module)

        for module in modle.local:
            involved_modules.append(module)

        return involved_modules

    def __fetch_from_svn(self, module):
        fetchto = module.fetchto
        if not os.path.exists(fetchto):
            os.mkdir(fetchto)

        cur_dir = os.getcwd()
        os.chdir(fetchto)
        url, rev = __parse_repo_url(module.url)

        basename = path.url_basename(url)

        cmd = "svn checkout {0} " + basename
        if rev:
            cmd = cmd.format(url + '@' + rev)
        else:
            cmd = cmd.format(url)

        rval = True

        p.vprint(cmd)
        if os.system(cmd) != 0:
            rval = False
        os.chdir(cur_dir)

        module.isfetched = True
        module.path = os.path.join(fetchto, basename)
        return rval

    def __fetch_from_git(self, module):
        fetchto = module.fetchto
        if not os.path.exists(fetchto):
            os.mkdir(fetchto)

        cur_dir = os.getcwd()
        os.chdir(fetchto)
        url, rev = __parse_repo_url(module.url)

        basename = path.url_basename(url)

        if basename.endswith(".git"):
            basename = basename[:-4] #remove trailing .git

        if not os.path.exists(os.path.join(fetchto, basename)):
            update_only = False
        else:
            update_only = True

        if update_only:
            cmd = "git --git-dir="+basename+"/.git pull"
        else:
            cmd = "git clone " + url

        rval = True

        p.vprint(cmd)
        if os.system(cmd) != 0:
            rval = False

        if rev and rval:
            os.chdir(basename)
            if os.system("git checkout " + revision) != 0:
                rval = False

        os.chdir(cur_dir)
        module.isfetched = True
        module.path = os.path.join(fetchto, basename)
        return rval

    def __parse_repo_url(self, url) :
        """
        Check if link to a repo seems to be correct. Filter revision number
        """
        import re
        url_pat = re.compile("[ \t]*([^ \t]+)[ \t]*(@[ \t]*(.+))?[ \t]*")
        url_match = re.match(url_pat, url)

        if url_match == None:
            p.echo("Not a correct repo url: {0}. Skipping".format(url))
        if url_match.group(3) != None: #there is a revision given 
            ret = (url_match.group(1), url_match.group(3))
        else:
            ret = (url_match.group(1), None)

class ModulePool:
    def __init__(self, top_module):
        self.top_module = top_module
        self.modules = []

    def __iter__(self):
        return self.modules.__iter__()
        
    def __len__(self):
        return len(self.modules)
        
    def __contains__(self,v):
        return v in self.files
        
    def __getitem__(self,v):
        return self.files(v)
    
    def __str__(self):
        return str([str(m) for m in self.modules])
    
    def add(self, module):
        if not isinstance(module, Module):
            raise RuntimeError("Expecting a Module instance")
        for mod in self.modules:
            if mod.url == module.url:
                return False
        self.modules.append(module)
        return True

    def fetch_all(self):
        fetcher = ModuleFetcher()
        fetch_queue = [self.top_module]

        while len(fetch_queue) > 0:
            cur_mod = fetch_queue.pop()
            new_modules = fetcher.fetch_single_module(cur_mod)
            for mod in new_modules:
                ret = self.add(mod)
                if ret == True:
                    fetch_queue.append(mod)
                else:
                    pass

    def is_everything_fetched(self):
        for mod in self.modules:
            if mod.is_fetched_recursively() == False:
                return False
        return True
