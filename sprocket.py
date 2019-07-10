from __future__ import annotations

from typing import List, Dict, Any


import llvmlite.ir as ir


class Module:
    def __init__(self, name: str):
        self.name = name
        self.types: Dict[str, Type] = {}
        self.vars: Dict[str, Function] = {}
        # self.namespaces: Dict[str, Namespace] = {}


class Type:
    pass


class IntType(Type):
    def __init__(self, bits: int):
        self.bits = bits


class ClassType(Type):
    def __init__(self, name: str, module: Module):
        self.name = name

        self.bases: List[ClassType] = []

        self.attrs: Dict[str, Type] = {}

        module.types[self.name] = self


class FuncType(Type):
    def __init__(self, args: List[Type], ret: Type):
        self.args = args
        self.ret = ret


class Function:
    def __init__(self, name: str, args: List[Type], ret: Type):
        self.name = name
        self.args = args
        self.ret = ret









