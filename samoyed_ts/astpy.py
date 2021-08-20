
EMPTY = () # 空のタプル

class PExpr(object):  # 式
    name: str
    params: tuple

    def __init__(self, name='', params=EMPTY):
        self.name = name
        self.params = params

    def emit(self, buffers, env):
        pass

    def __repr__(self):
        buffers = []
        self.emit(buffers, {})
        return ''.join(buffers)

    # def __lt__(self, a):
    #     return id(self) < id(a)

    def __len__(self):
        return len(self.params)

    def __getitem__(self, index):
        return self.params[index]

ESC = str.maketrans({'\n': '\\n', '\t': '\\t', '"': '\\"'})

class PValue(PExpr): # 値
    value: object

    def __init__(self, value):
        PExpr.__init__(self)
        self.value = value

    def emit(self, buffers, env):
        value = self.value
        if isinstance(value, str):
            buffers.append('"')
            buffers.append(value.translate(ESC))
            buffers.append('"')
        else:
            buffers.append(str(value))

class PVar(PExpr):  # 変数

    def __init__(self, name):
        PExpr.__init__(self, name)

    def emit(self, buffers, env):
        buffers.append(self.name)

def e(x):
    if isinstance(x, PExpr):
        return x
    if isinstance(x, str):
        return PVar(x)
    return PValue(x)


class PBinary(PExpr):
    MAP = {
        'and': ' and ',
        'or': ' or ',
    }
    def __init__(self, left, op, right):
        PExpr.__init__(self, op, (e(left), e(right)))

    def emit(self, buffers, env):
        self.params[0].emit(buffers, env)
        buffers.append(PBinary.MAP.get(self.name, self.name))
        self.params[1].emit(buffers, env)

class PUnary(PExpr):
    MAP = {
        'not': 'not ',
    }

    def __init__(self, op, expr):
        PExpr.__init__(self, op, (e(expr),))

    def emit(self, buffers, env):
        buffers.append(PUnary.MAP.get(self.name, self.name))
        self.params[0].emit(buffers, env)

class PIfExpr(PExpr):
    def __init__(self, *es):
        PExpr.__init__(self, '{}', tuple(e(x) for x in es))

    def emit(self, buffers, env):
        self.params[1].emit(buffers, env)
        buffers.append(' if ')
        self.params[0].emit(buffers, env)
        buffers.append(' else ')
        self.params[2].emit(buffers, env)


class PField(PExpr):

    def __init__(self, expr, name: str):
        PExpr.__init__(self, name, (e(expr), ))

    def emit(self, buffers, env):
        self.params[0].emit(buffers, env)
        buffers.append('.')
        buffers.append(self.name)

class PIndex(PExpr):

    def __init__(self, expr, index):
        PExpr.__init__(self, [], (e(expr), e(index)))

    def emit(self, buffers, env):
        self.params[0].emit(buffers, env)
        buffers.append('[')
        self.params[1].emit(buffers, env)
        buffers.append(']')

class PEmpty(PExpr):

    def __init__(self):
        PExpr.__init__(self)

    def emit(self, buffers, env):
        pass

class PSlice(PExpr):

    def __init__(self, expr, index):
        PExpr.__init__(self, [], (e(expr), e(index)))

    def emit(self, buffers, env):
        self.params[0].emit(buffers, env)
        buffers.append('[')
        self.params[1].emit(buffers, env)
        buffers.append(':')
        self.params[2].emit(buffers, env)
        if len(self.params[3]) > 3:
            self.params[3].emit(buffers, env)
        buffers.append(']')


class PApp(PExpr):

    def __init__(self, *es):
        PExpr.__init__(self, '', tuple(e(x) for x in es))

    def emit(self, buffers, env):
        self.params[0].emit(buffers, env)
        buffers.append('(')
        for i, p in enumerate(self.params[1:]):
            if i > 0:
                buffers.append(',')
            p.emit(buffers, env)
        buffers.append(')')

class PGroup(PExpr):

    def __init__(self, expr):
        PExpr.__init__(self, "(,)", tuple(e(expr)))

    def emit(self, buffers, env):
        buffers.append('(')
        self.params[0].emit(buffers, env)
        buffers.append(')')

class PSeq(PExpr):

    def __init__(self, *es):
        PExpr.__init__(self, ",", tuple(e(x) for x in es))

    def emit(self, buffers, env):
        for i, p in enumerate(self.params):
            if i > 0:
                buffers.append(',')
            p.emit(buffers, env)

class PTuple(PExpr):

    def __init__(self, *es):
        PExpr.__init__(self, "(,)", tuple(e(x) for x in es))

    def emit(self, buffers, env):
        buffers.append('(')
        for i, p in enumerate(self.params):
            if i > 0:
                buffers.append(',')
            p.emit(buffers, env)
        if len(self.params) == 1:
            buffers.append(',')
        buffers.append(')')

class PList(PExpr):

    def __init__(self, *es):
        PExpr.__init__(self, "[,]", tuple(e(x) for x in es))

    def emit(self, buffers, env):
        buffers.append('[')
        for i, p in enumerate(self.params):
            if i > 0:
                buffers.append(',')
            p.emit(buffers, env)
        buffers.append(']')

class PKeyValue(PExpr):

    def __init__(self, key, value):
        PExpr.__init__(self, (e(key), e(value)))

    def emit(self, buffers, env):
        self.params[0].emit(buffers, env)
        buffers.append(':')
        self.params[1].emit(buffers, env)


class PDict(PExpr):

    def __init__(self, *es):
        PExpr.__init__(self, "{,}", tuple(e(x) for x in es))

    def emit(self, buffers, env):
        buffers.append('{')
        for i, p in enumerate(self.params):
            if i > 0:
                buffers.append(',')
            p.emit(buffers, env)
        buffers.append('}')

class PBlock(PExpr):
    def __init__(self, *es):
        PExpr.__init__(self, '{}', tuple(e(x) for x in es))

    def emit(self, buffers, env):
        indent = env.get('@indent', '\n')
        env['@indent'] = indent+'  '
        for i, p in enumerate(self.params):
            buffers.append(env['@indent'])
            p.emit(buffers, env)
        env['@indent'] = indent

class PStatement(PExpr):

    def __init__(self, pred, *es):
        PExpr.__init__(self, pred, tuple(e(x) for x in es))

    def emit(self, buffers, env):
        buffers.append(self.name)
        if len(self.params) > 0:
            buffers.append(' ')
            self.params[0].emit(buffers, env)
  
class PIf(PExpr):

    def __init__(self, *es):
        PExpr.__init__(self, '{}', tuple(e(x) for x in es))

    def emit(self, buffers, env):
        buffers.append('if ')
        self.params[0].emit(buffers, env)
        buffers.append(':')
        self.params[1].emit(buffers, env)
        if len(self.params) > 2:
            buffers.append(env.get('@indent', '\n'))
            buffers.append('else:')
            self.params[2].emit(buffers, env)

class PWhile(PExpr):

    def __init__(self, *es):
        PExpr.__init__(self, '{}', tuple(e(x) for x in es))

    def emit(self, buffers, env):
        buffers.append('while ')
        self.params[0].emit(buffers, env)
        buffers.append(':')
        self.params[1].emit(buffers, env)

class PForIn(PExpr):

    def __init__(self, *es):
        PExpr.__init__(self, '{}', tuple(e(x) for x in es))

    def emit(self, buffers, env):
        buffers.append('for ')
        self.params[0].emit(buffers, env)
        buffers.append(' in ')
        self.params[1].emit(buffers, env)
        buffers.append(':')
        self.params[2].emit(buffers, env)

class PForInRange(PExpr):

    def __init__(self, *es):
        PExpr.__init__(self, '{}', tuple(e(x) for x in es))

    def emit(self, buffers, env):
        buffers.append('for ')
        self.params[0].emit(buffers, env)
        buffers.append(' in range(')
        self.params[1].emit(buffers, env)
        if len(self.params) > 2:
            buffers.append(',')
            self.params[3].emit(buffers, env)
        if len(self.params) > 3:
            buffers.append(',')
            self.params[4].emit(buffers, env)
        buffers.append('): ')


if __name__ == '__main__':
    print(PIf(PBinary('a', '=', 1), 'pass', 'pass'))
    print(PApp('print'))
    print(PApp('print', 1))