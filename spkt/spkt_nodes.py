from __future__ import annotations

import itertools
import pathlib
from dataclasses import dataclass, field
from typing import List, Dict, ClassVar, Iterator, Iterable, Any, Union


class SprocketError(Exception):
    pass


@dataclass()
class Node:
    pass


@dataclass()
class Namespace(Node):
    def add_decl(self, decl: NamedNodeDecl):
        raise NotImplementedError()

    def add_type(self, decl: IdentifiedTypeDecl):
        raise NotImplementedError()

    def get_decl(self, name: str):
        raise NotImplementedError()


@dataclass()
class NamedNodeDecl:
    name: str
    namespace: Namespace = field(repr=False)

    named_usages: List[NamedNodeUse] = field(init=False, default_factory=list, repr=False)

    def __post_init__(self):
        self.namespace.add_decl(self)


@dataclass()
class NamedNodeUse:
    decl: NamedNodeDecl

    def __post_init__(self):
        self.decl.named_usages.append(self)


@dataclass()
class TypeDecl:
    typed_usages: List[TypedNodeUse] = field(init=False, default_factory=list, repr=False)

    def __hash__(self):
        return id(self)


@dataclass()
class IdentifiedTypeDecl(TypeDecl):
    name: str
    namespace: Namespace = field(repr=False)

    def __post_init__(self):
        self.namespace.add_type(self)

    def __hash__(self):
        return id(self)


@dataclass()
class TypedNodeUse:
    pass


@dataclass()
class SimpleTypedNodeUse(TypedNodeUse):
    type: TypeDecl

    def __post_init__(self):
        self.type.typed_usages.append(self)


@dataclass()
class Value(NamedNodeDecl, SimpleTypedNodeUse):
    def __hash__(self):
        return id(self)


@dataclass()
class Module(Namespace):
    name: str
    path: pathlib.Path
    funcs: Dict[str, FuncDecl] = field(init=False, default_factory=dict)
    types: Dict[str, TypeDecl] = field(init=False, default_factory=dict)

    def add_decl(self, decl: NamedNodeDecl):
        if isinstance(decl, FuncDecl):
            self.funcs[decl.name] = decl
        else:
            raise SprocketError(f"Can only add functions to a module namespace, not {type(decl).__qualname__}")

    def add_type(self, decl: IdentifiedTypeDecl):
        self.types[decl.name] = decl

    def get_decl(self, name: str):
        return self.funcs[name]


@dataclass()
class CModule(Module):
    source_path: pathlib.Path

    def add_decl(self, decl: NamedNodeDecl):
        if isinstance(decl, FuncDecl) and not isinstance(decl, Function):
            self.funcs[decl.name] = decl
        else:
            raise SprocketError(f"Can only add function declarations"
                                f" to a C-MODULE namespace, not {type(decl).__qualname__}")


@dataclass()
class FuncType(TypeDecl, TypedNodeUse):
    params: List[TypeDecl]
    ret: TypeDecl

    def __post_init__(self):
        self.ret.typed_usages.append(self)
        for param in self.params:
            param.typed_usages.append(self)


@dataclass()
class FuncDecl(Value):
    params: List[FuncParam]
    ret: FuncReturn

    def __hash__(self):
        return id(self)


@dataclass()
class Function(FuncDecl):
    body: Block

    def __hash__(self):
        return id(self)


@dataclass()
class FuncParam(Value):
    def __hash__(self):
        return id(self)


@dataclass()
class FuncReturn(SimpleTypedNodeUse):
    pass


@dataclass()
class Block(Namespace):
    names: Dict[str, NamedNodeDecl] = field(default_factory=dict)

    body: List[Instruction] = field(default_factory=list)
    parent: Block = field(default=None)

    def add_decl(self, decl: NamedNodeDecl):
        if isinstance(decl, Value):
            self.names[decl.name] = decl
        else:
            raise Exception()

    def add_type(self, decl: IdentifiedTypeDecl):
        raise SprocketError("Cannot define a type in a block")

    def get_decl(self, name: str):
        return self.names[name]


@dataclass()
class FuncBody(Block):
    pass


@dataclass()
class Instruction(Node, SimpleTypedNodeUse):
    scope: Namespace = field(repr=False)
    to: Union[Temp, None]


@dataclass()
class Call(Instruction):
    func: Value
    args: Iterable[Value]


@dataclass()
class Return(Instruction):
    ret: Value


@dataclass()
class Get(Instruction):
    var: str


@dataclass()
class IntConstant(Instruction):
    val: int


class Builder:
    def __init__(self, func: Block, *, obj=None):
        self.func = func
        self.instrs: List[Instruction] = []

        self._counter = itertools.count()

        if obj is not None:
            obj.builder = self

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            return False
        else:
            self.func.body = self.instrs

    def _add(self, instr: Instruction):
        self.instrs.append(instr)

    def next_temp(self, typ):
        return Temp(typ, str(next(self._counter)), self.func)

    def call(self, func: Value, args: Iterable[Value], typ: TypeDecl, *, to: Temp = None) -> Temp:
        if to is None:
            to = self.next_temp(typ)
        call_instr = Call(typ, self.func, to, func, args)
        self._add(call_instr)
        return to

    def ret(self, expr: Temp):
        ret_instr = Return(expr.type, self.func, None, expr)
        self._add(ret_instr)

    def get(self, name: str, typ: TypeDecl):
        tmp = Temp(typ, name, self.func)
        return tmp

    def int(self, val: int, *, to: Temp = None):
        if to is None:
            to = self.next_temp(Int)
        int_instr = IntConstant(Int, self.func, to, val)
        self._add(int_instr)
        return to


@dataclass()
class Temp(Value):
    _counter: ClassVar[Iterator[int]] = itertools.count()

    meta: Dict[str, Any] = field(init=False, default_factory=dict)

    @classmethod
    def next(cls, typ, ns):
        return cls(typ, str(next(cls._counter)), ns)

    def where(self, **kwargs):
        self.meta.update(kwargs)
        return self

    def __hash__(self):
        return id(self)


Builtins = CModule("builtins",
                   pathlib.Path(f"{__file__}").parent / "spkt_std" / "test.h",
                   pathlib.Path(f"{__file__}").parent / "spkt_std" / "test.c")

Int = IdentifiedTypeDecl("int", Builtins)
Void = IdentifiedTypeDecl("void", Builtins)

test_func = FuncDecl(FuncType([], Void), "test", Builtins, [], FuncReturn(Void))
