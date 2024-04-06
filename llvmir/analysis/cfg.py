import enum
import tempfile
import subprocess

from ..function import Function
from ..instruction import *

import networkx as nx


class EntryNode:
    def get_name(self) -> str:
        return "entry"

    def sname(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return "entry"


class ExitNode:
    def get_name(self) -> str:
        return "exit"

    def sname(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return "exit"


class CFGEdge(enum.Enum):
    UNCOND = ""
    TRUE = "true"
    FALSE = "false"


class CFG:
    def __init__(self, function: Function):
        self.function = function
        self.graph: nx.DiGraph = nx.DiGraph()
        entry = EntryNode()
        exit_ = ExitNode()
        self.graph.add_node(entry)
        self.graph.add_node(exit_)
        for block in function.blocks:
            self.graph.add_node(block)
        self.graph.add_edge(
            entry, function.blocks[0], edge_type=CFGEdge.UNCOND)
        for block in function.blocks:
            inst = block.terminator()
            match inst:
                case BranchInst(dest):
                    self.graph.add_edge(
                        block, dest, edge_type=CFGEdge.UNCOND)
                case CondBrInst(_, true, false):
                    self.graph.add_edge(
                        block, true, edge_type=CFGEdge.TRUE)
                    self.graph.add_edge(
                        block, false, edge_type=CFGEdge.FALSE)
                case ReturnInst(_):
                    self.graph.add_edge(
                        block, exit_, edge_type=CFGEdge.UNCOND)
                case _:
                    raise NotImplementedError(
                        f"Unknown terminator {inst} in CFG")

    def to_dot(self) -> str:
        dot = "digraph {\n"
        for node in self.graph.nodes():
            if isinstance(node, EntryNode):
                dot += "    entry [shape=ellipse];\n"
            elif isinstance(node, ExitNode):
                dot += "    exit [shape=ellipse];\n"
            else:
                insts = "\\l\n    ".join([str(inst)
                                         for inst in node.instructions])
                dot += f"    {node.get_name()
                              } [shape=record, label=\"{{ {node.sname()}:\\l\\l  {insts}\\l}}\"];\n"
        for a, b, e in self.graph.edges(data=True):
            match e['edge_type']:
                case CFGEdge.UNCOND:
                    dot += f"    {a.get_name()} -> {b.get_name()};\n"
                case CFGEdge.TRUE:
                    dot += f"    {a.get_name()} -> {b.get_name()
                                                    } [label=\"true\"];\n"
                case CFGEdge.FALSE:
                    dot += f"    {a.get_name()} -> {b.get_name()
                                                    } [label=\"false\"];\n"
                case _:
                    raise NotImplementedError(f"Unknown edge type {e}")
        dot += "}"
        return dot

    def visualize(self, path):
        dot = self.to_dot()
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".dot")
        with open(temp.name, "w") as f:
            f.write(dot)
        try:
            subprocess.run(["dot", "-Tpng", temp.name, "-o", path])
        except Exception as e:
            print(e)
