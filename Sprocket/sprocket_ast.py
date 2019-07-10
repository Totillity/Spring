from __future__ import annotations

from typing import List, Dict
from dataclasses import dataclass, field
from abc import ABC


@dataclass()
class Node:
    pass


@dataclass()
class Namespace(Node):
    pass


@dataclass()
class NamedNodeDecl:
    name: str
    namespace: Namespace

    usages: List[NamedNodeUse] = field(init=False, default=[])


@dataclass()
class NamedNodeUse:
    decl: NamedNodeDecl

    def __post_init__(self):
        self.decl.usages.append(self)


@dataclass()
class TypedNodeDecl:
    usages: List[TypedNodeUse] = field(init=False, default=[])


@dataclass()
class TypedNodeUse:
    type: TypedNodeDecl

    def __post_init__(self):
        self.type.usages.append(self)


@dataclass()
class Module(Namespace):
    funcs: Dict[str, Function]
    types: Dict[str, TypedNodeDecl]


@dataclass()
class Function(NamedNodeDecl):
    params: List[FuncParameter]
    ret: FuncReturn

    body: List[Stmt]


@dataclass()
class FuncParameter(TypedNodeUse, NamedNodeDecl):
    pass


@dataclass()
class FuncReturn(TypedNodeUse):
    pass


@dataclass()
class Stmt(Node):
    scope: Node


@dataclass()
class ExprStmt(Stmt):
    expr: Expr


@dataclass()
class Expr(Node, TypedNodeUse):
    pass


@dataclass()
class Call(Expr):
    func: Expr
    args: List[Expr]


@dataclass()
class GetVar(Expr, NamedNodeUse):
    pass