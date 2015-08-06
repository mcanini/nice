#
# Copyright (c) 2011, EPFL (Ecole Politechnique Federale de Lausanne)
# All rights reserved.
#
# Created by Marco Canini, Daniele Venzano, Dejan Kostic, Jennifer Rexford
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   -  Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#   -  Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#   -  Neither the names of the contributors, nor their associated universities or
#      organizations may be used to endorse or promote products derived from this
#      software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
# SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import ast
import unparse
import os

# modules automatically imported by NOX
NOX_API_MODULES = ['nox.lib.util']

ord_str = """python_ord = ord # make a backup of Python's ord() function
def se_ord(obj):
    __foo = hasattr(obj, '__ord__')
    if __foo:
        whichBranch(True)
        return obj.__ord__()
    else:
        whichBranch(False)
        return python_ord(obj)
ord = se_ord
"""

class SplitBoolOpPass1(ast.NodeTransformer):
    def visit_If(self, node):
        while isinstance(node.test, ast.BoolOp):
            new_node = ast.If(test=node.test.values.pop(), body=node.body, orelse=node.orelse)
            if isinstance(node.test.op, ast.And):
                if len(node.test.values) == 1:
                    node.test = node.test.values[0]
                node.body = [new_node]
                continue
            else:
                if len(node.test.values) == 1:
                    node.test = node.test.values[0]
                node.orelse = [new_node]
        node = self.generic_visit(node) # recusion
        return node

class MoveFunctionCallsPass2(ast.NodeTransformer):
    TYPES_TO_IGNORE = [ast.Num, ast.Str, ast.Name, ast.cmpop]

    def __init__(self):
        ast.NodeTransformer.__init__(self)
        self.counter = 1
        self.funcs = None

    def visit_If(self, node):
        node = self.generic_visit(node) # recusion
        self.funcs = []
        new_node = ast.If(test=self.getFuncs(node.test), body=node.body, orelse=node.orelse)
        exprs = []
        for (var, func) in self.funcs:
            exprs.append(ast.Assign(targets=[ast.Name(id=var, ctx=ast.Store())], value=func))
        exprs.append(new_node)
        return exprs

    def visit_While(self, node):
        node = self.generic_visit(node) # recusion
        self.funcs = []
        new_node = ast.While(test=self.getFuncs(node.test), body=node.body, orelse=node.orelse)
        exprs = []
        for (var, func) in self.funcs:
            exprs.append(ast.Assign(targets=[ast.Name(id=var, ctx=ast.Store())], value=func))
        exprs.append(new_node)
        return exprs

    def getFuncs(self, node):
        if not isinstance(node, ast.expr) and not isinstance(node, list):
            return node

        if isinstance(node, list):
            new_list = []
            for _j, v in enumerate(node):
                new_list.append(self.getFuncs(v))
            return new_list

        for _i, f in enumerate(node._fields):
            setattr(node, f, self.getFuncs(getattr(node, f)))

        if type(node) is ast.Call:
            varname = "__se_tmp_"+str(self.counter)
            self.counter += 1
            self.funcs.append((varname, node))
            newnode = ast.Name(id=varname, ctx=ast.Load())
            return ast.copy_location(newnode, node)
        else:
            return node

class BranchIdentifierPass3(ast.NodeTransformer):
    def __init__(self, import_se_dict=True):
        ast.NodeTransformer.__init__(self)
        self.se_dict = import_se_dict

    def visit_If(self, node):
        node = self.generic_visit(node) # recusion
        call_node_true = ast.Expr(value=ast.Call(func=ast.Name(id='whichBranch', ctx=ast.Load()), args=[ast.Name(id='True', ctx=ast.Load())], keywords=[], starargs=None, kwargs=None))
        call_node_false = ast.Expr(value=ast.Call(func=ast.Name(id='whichBranch', ctx=ast.Load()), args=[ast.Name(id='False', ctx=ast.Load())], keywords=[], starargs=None, kwargs=None))
        new_body = [call_node_true] + node.body
        new_orelse = [call_node_false] + node.orelse
        new_node = ast.If(test=node.test, body=new_body, orelse=new_orelse)
        return ast.copy_location(new_node, node)

    def visit_While(self, node):
        node = self.generic_visit(node) # recusion
        call_node_true = ast.Expr(value=ast.Call(func=ast.Name(id='whichBranch', ctx=ast.Load()), args=[ast.Name(id='True', ctx=ast.Load())], keywords=[], starargs=None, kwargs=None))
        call_node_false = ast.Expr(value=ast.Call(func=ast.Name(id='whichBranch', ctx=ast.Load()), args=[ast.Name(id='False', ctx=ast.Load())], keywords=[], starargs=None, kwargs=None))
        new_body = [call_node_true] + node.body
        new_orelse = [call_node_false] + node.orelse
        new_node = ast.While(test=node.test, body=new_body, orelse=new_orelse)
        return ast.copy_location(new_node, node)

    def visit_Module(self, node):
        """ Add the imports needed to run symbolically """
        node = self.generic_visit(node)
        if self.se_dict:
            import_se_dict = ast.ImportFrom(module="se_dict", names=[ast.alias(name="SeDict", asname=None)], level=0)
        import_instrumentation = ast.ImportFrom(module="symbolic.instrumentation", names=[ast.alias(name="whichBranch", asname=None)], level=0)

        ord_function = ast.parse(ord_str).body
        if self.se_dict:
            node.body = [import_se_dict, import_instrumentation] + ord_function + node.body
        else:
            node.body = [import_instrumentation] + ord_function + node.body
        return node

    def visit_Dict(self, node):
        return ast.Call(func=ast.Name(id='SeDict', ctx=ast.Load()), args=[node], keywords=[], starargs=None, kwargs=None)

class NoxAppPass4(ast.NodeTransformer):
    def visit_Module(self, node):
        """ Add the imports injected by NOX """
        node = self.generic_visit(node)
        nox_api_mods = []
        for m in NOX_API_MODULES:
            aux = ast.ImportFrom(module=m, names=[ast.alias(name="*", asname=None)], level=0)
            nox_api_mods.append(aux)
        node.body = nox_api_mods + node.body

class NotBugfixPass(ast.NodeTransformer):

    def __init__(self):
        ast.NodeTransformer.__init__(self)
        self.counter = 0

    def TempName(self):
        self.counter += 1
        return "__not_bugfix_%d" % self.counter

    def visit_UnaryOp(self, node):
        node = self.generic_visit(node) # recusion
        if isinstance(node.op, ast.Not):
            zero = ast.Num(n=0)
            new_node = ast.Compare(
                left = node.operand,
                ops = [ast.Eq()],
                comparators = [zero],
            )
            print new_node
            ast.copy_location(new_node, node)
            ast.copy_location(zero, node)
            ast.copy_location(new_node.left, node)
            return new_node
        else:
            return node


def instrumentModule(module_filename, out_dir, is_app=False, in_dir=""):
    (dirname, mod_name) = os.path.split(module_filename)
    if len(dirname) > 0:
        out_dir = os.path.join(out_dir, dirname)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

    mod_file = os.path.join(out_dir, mod_name)

    if os.path.exists(mod_file) and os.stat(os.path.join(in_dir, module_filename)).st_mtime < os.stat(mod_file).st_mtime:
        return
    print "Instrumenting %s" % module_filename
    if "se_dict.py" in module_filename:
        import_se_dict = False
    else:
        import_se_dict = True

    module_contents = file(os.path.join(in_dir, module_filename), "U").read()
    if len(module_contents.strip()) == 0:
        file(mod_file, "w").close()
        return
    root_node = ast.parse(module_contents)
    SplitBoolOpPass1().visit(root_node)
    MoveFunctionCallsPass2().visit(root_node)
    BranchIdentifierPass3(import_se_dict).visit(root_node)
    if is_app:
        NoxAppPass4().visit(root_node)
    NotBugfixPass().visit(root_node)
    ast.fix_missing_locations(root_node)

    compile(root_node, module_filename, 'exec') # to make sure the new AST is ok

    unparse.Unparser(root_node, file(mod_file, "w"))

def instrumentPackage(package_dir, out_dir, in_dir=""):
    abs_package_dir = os.path.join(in_dir, package_dir)
    for f in os.listdir(abs_package_dir):
        in_f = os.path.join(package_dir, f)
        abs_in_f = os.path.join(in_dir, in_f)
        if f == ".svn" or os.path.splitext(f)[1] == ".pyc" or f[0] == ".":
            continue
        if os.path.isdir(abs_in_f):
            instrumentPackage(in_f, out_dir, in_dir)
        if os.path.isfile(abs_in_f):
            instrumentModule(in_f, out_dir, in_dir=in_dir)

