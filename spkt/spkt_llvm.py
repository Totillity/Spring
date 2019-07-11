import os
import subprocess
from typing import Dict, List

import llvmlite.ir as ir

import spkt.spkt_nodes as spkt

__all__ = ["compile_spkt"]


class Visitor:
    def visit(self, obj, *args, **kwargs):
        for base in obj.__class__.mro():
            try:
                meth = getattr(self, "visit_" + base.__name__)
                break
            except AttributeError:
                pass
        else:
            raise ValueError(f"(In {self.__class__.__qualname__}) "
                             f"No Visitor implemented for class {obj.__class__.__qualname__}") from None
        return meth(obj, *args, **kwargs)


class Scope:
    def __init__(self):
        self.vars: Dict[spkt.Value, ir.Value] = {}
        self.types: Dict[spkt.TypeDecl, ir.Type] = {}


class SpktToLLVM(Visitor):
    ir_Int = ir.IntType(32)
    ir_Void = ir.VoidType()

    def __init__(self):
        # noinspection PyTypeChecker
        self.builder: ir.IRBuilder = None
        self.scopes: List[Scope] = []

        self.module = ir.Module()

    def compile_modules(self, modules: List[spkt.Module], and_run=False):
        llvm_mod = self.llvm_from_modules(modules)

        passed = []

        main_path = modules[0].path.with_suffix(".ll")

        with main_path.open("w") as main_file:
            main_file.write(str(llvm_mod))

        passed += [main_path]

        for mod in modules:
            if isinstance(mod, spkt.CModule):
                passed.append(str(mod.source_path))

        if os.name == 'posix':
            try:
                subprocess.run(["clang",
                                *passed,
                                "-o", main_path.with_suffix(''),
                                '-Wno-override-module'], check=True)
            except subprocess.CalledProcessError:
                raise Exception("Error compiling generated code") from None

            main_path.unlink()

            if and_run:
                subprocess.run([f"./{main_path.with_suffix('')}"], check=True)

            return main_path.with_suffix('')
        else:
            raise SystemError("Only support compilation to executable code on POSIX (perhaps even only mac os x)")

    def llvm_from_modules(self, modules: List[spkt.Module]):
        self.scopes.append(Scope())
        self.scopes[-1].types[spkt.Int] = self.ir_Int
        self.scopes[-1].types[spkt.Void] = self.ir_Void

        data = []
        for module in modules:
            llvm_funcs = []
            for func in module.funcs.values():
                func_type = ir.FunctionType(self.visit(func.ret.type),
                                            [self.visit(param.type) for param in func.params])
                llvm_func = ir.Function(self.module, func_type, func.name)
                self.scopes[-1].vars[func] = llvm_func
                llvm_funcs.append(llvm_func)
            data.append(llvm_funcs)

        for llvm_funcs, module in zip(data, modules):
            self.visit(module, llvm_funcs)

        return self.module

    def visit_Module(self, node: spkt.Module, llvm_funcs):
        for llvm_func, func in zip(llvm_funcs, node.funcs.values()):
            self.visit(func, in_llvm=llvm_func)

    def visit_Function(self, node: spkt.Function, in_llvm: ir.Function = None):
        if in_llvm:
            func = in_llvm
            self.builder = ir.IRBuilder(func.append_basic_block("entry"))
            self.scopes.append(Scope())
            for n, param in enumerate(node.params):
                self.scopes[-1].vars[param] = func.args[n]

            for instr in node.body.body:
                self.visit(instr)
        else:
            return self.visit_Value(node)

    def visit_FuncDecl(self, node: spkt.FuncDecl, in_llvm: ir.Function = None):
        if in_llvm:
            pass
        else:
            return self.visit_Value(node)

    def visit_TypeDecl(self, node: spkt.TypeDecl):
        for scope in self.scopes:
            if node in scope.types:
                return scope.types[node]
        else:
            raise KeyError(f"Node {node} not in scope")

    def visit_Call(self, node: spkt.Call):
        return self.builder.call(self.visit(node.func), [self.visit(arg) for arg in node.args])

    def visit_Value(self, node: spkt.Value):
        for scope in self.scopes:
            if node in scope.vars:
                return scope.vars[node]
            # else:
            #     print({id(key) for key in scope.vars.keys()}, id(node))
        else:
            # breakpoint()
            raise KeyError(f"Node {node} not in scope")

    def visit_IntConstant(self, node: spkt.IntConstant):
        self.scopes[-1].vars[node.to] = self.ir_Int(node.val)

    def visit_Return(self, node: spkt.Return):
        self.builder.ret(self.visit(node.ret))


def compile_spkt(modules: List[spkt.Module], and_run=False):
    to_llvm = SpktToLLVM()
    res = to_llvm.compile_modules(modules, and_run=and_run)
    return res
