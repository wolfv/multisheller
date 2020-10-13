from .visitor import NodeVisitor
import re

def ensure_quotes(x):
    if x[0] == '"' or x[0] == '\'' and x[-1] == x[0]:
      return x
    else:
      return f"\"{re.escape(x)}\""


class BashVisitor(NodeVisitor):
    def visit_BinOp(self, op):
        op_map = {
            'add': '+',
            'eq': '-eq',
            'lt': '-lt',
            'le': '-le',
            'gt': '-gt',
            'ge': '-ge',
            'ne': '-ne'
            'or': '||',
            'and': '&&',
        }

        if op.op in ('export', 'assign'):
            if op.op == 'export':
                return f"export {self.visit(op.lhs)}={self.visit(op.rhs)}"
            else:
                return f"{self.visit(op.lhs)}={self.visit(op.rhs)}"
        return f"{self.visit(op.lhs)} {op_map[op.op]} {self.visit(op.rhs)}"

    def visit_UnaryOp(self, op):
        op_map = {
            'is_set': '-z',
            'not': '!'
        }
        return f"{op_map[op.op]} {self.visit(op.value)}"

    def visit_StrOp(self, node):
        q = ensure_quotes
        if node.op == 'quoted':
            return q(node.value)
        elif node.op == 'starts_with':
            return f"{q(self.visit(node.lhs))} == {q(self.visit(node.rhs))}*"
        elif node.op == 'ends_with':
            return f"{q(self.visit(node.lhs))} == *{q(self.visit(node.rhs))}"
        elif node.op == 'contains':
            return f"{q(self.visit(node.lhs))} == *{q(self.visit(node.rhs))}*"

    def visit_Env(self, op):
        return f"${self.visit(op.varname)}"

    def visit_Conditional(self, op):
        then_expr, else_expr = "", ""
        if op.then_expr:
            then_expr = f"\nthen\n    {self.visit(op.then_expr)}"
        if op.else_expr:
            else_expr = f"\nelse\n    {self.visit(op.else_expr)}"

        return f"if [[ {self.visit(op.if_expr)} ]];{then_expr}{else_expr}\nfi;"

    def visit_Call(self, op):
        return f"{op.cmd} {' '.join(op.args)}"

    def visit_default(self, node):
        return str(node)

def to_script(script):
    res = []
    visitor = BashVisitor()

    for cmd in script.cmds:
        res.append(visitor.visit(cmd))

    return '\n'.join(res)