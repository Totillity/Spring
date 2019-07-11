import pathlib
from typing import Dict, List, Union

from spring import parse_text
from spring.spring_ast import *
from . import spkt_nodes as spkt

__all__ = ['to_spkt']


class Visitor:
    def visit(self, obj, *args, **kwargs):
        try:
            meth = getattr(self, "visit_" + obj.__class__.__name__)
        except AttributeError:
            raise ValueError(f"(In {self.__class__.__qualname__}) "
                             f"No Visitor implemented for class {obj.__class__.__qualname__}") from None
        return meth(obj, *args, **kwargs)


class AstToSpkt(Visitor):
    def __init__(self):
        self.funcs: Dict[str, spkt.FuncDecl] = {}
        self.namespaces: Dict[str, spkt.Namespace] = {}

        # noinspection PyTypeChecker
        self.builder: spkt.Builder = None

    def compile(self, node: Program, path: pathlib.Path):
        return self.visit(node, path=path)

    @staticmethod
    def program_from_file(path: pathlib.Path):
        if path.suffix == ".spng":
            with path.open("r") as program_file:
                text = program_file.read()

            return parse_text(str(path), text)
        else:
            raise Exception("Cannot")

    def visit_Program(self, node: Program, path: pathlib.Path):
        mod = spkt.Module(path.name, path)

        for top_level in node.top_levels:
            if isinstance(top_level, Import):
                path = pathlib.Path(top_level.file)
                if path.suffix == ".spng":
                    # TODO
                    other_program = self.program_from_file(path)
                elif path.suffix == ".h":
                    if top_level.file == "test.h":
                        # test = spkt.Module("test")
                        #
                        # typ = spkt.FuncType([], spkt.Void)
                        #
                        # spkt.FuncDecl(typ, "test", test, [], spkt.FuncReturn(spkt.Void))
                        #
                        # self.namespaces["test"] = test

                        self.namespaces["test"] = spkt.Builtins
                    else:
                        raise Exception()
                else:
                    raise Exception()

            elif isinstance(top_level, Function):
                body = spkt.FuncBody()
                params = [spkt.FuncParam(self.visit(typ), name, body) for name, typ in top_level.params]
                ret = spkt.FuncReturn(self.visit(top_level.ret))

                typ = spkt.FuncType([param.type for param in params], ret.type)

                func = spkt.Function(typ, top_level.name, mod, params, ret, body)

                top_level.meta["spkt_func"] = func
            else:
                raise Exception()

        for top_level in node.top_levels:
            self.visit(top_level, **top_level.meta)

        return mod

    def visit_Import(self, node: Import):
        pass

    def visit_Function(self, node: Function, spkt_func: spkt.Function):
        with spkt.Builder(spkt_func.body, obj=self):
            for stmt in node.body:
                self.visit(stmt)

    def visit_Name(self, node: Name):
        if node.name == "int":
            return spkt.Int
        else:
            raise Exception()

    def visit_ExprStmt(self, node: ExprStmt):
        self.visit(node.expr)

    def visit_ReturnStmt(self, node: ReturnStmt):
        self.builder.ret(self.visit(node.expr))

    def visit_Call(self, node: Call):
        func: spkt.Value = self.visit(node.callee)
        args: List[spkt.Value] = [self.visit(arg) for arg in node.args]

        if not isinstance(func.type, spkt.FuncType):
            raise Exception()
        return self.builder.call(func, args, func.type)

    def visit_GetVar(self, node: GetVar):
        name = node.var

        if name in self.funcs:
            # TODO needs work NamedTypedDecl?
            return self.builder.get(name, self.funcs[name].type)
        elif name in self.namespaces:
            return self.namespaces[name]
        else:
            raise Exception()

    def visit_GetAttr(self, node: GetAttr):
        obj = self.visit(node.obj)

        if isinstance(obj, spkt.Module):
            func_decl = obj.get_decl(node.attr)
            return func_decl
        else:
            raise Exception()

    def visit_Literal(self, node: Literal):
        if node.type == "num":
            return self.builder.int(int(node.val))
        else:
            raise Exception()


def to_spkt(program: Program, path: Union[str, pathlib.Path]) -> List[spkt.Module]:
    if isinstance(path, str):
        path = pathlib.Path(path)
    compiler = AstToSpkt()
    mod = compiler.compile(program, path)
    return [mod] + [spkt.Builtins]
