"""Mini desensamblador: imprime, en orden, las cadenas (ldc), llamadas (invoke*), campos (get/putstatic) y saltos
de un método de una clase del jar del juego. Uso: python jdis.py clase/Ruta metodo"""
import sys, struct, zipfile
JAR = r"D:\SteamLibrary\steamapps\common\ProjectZomboid\projectzomboid.jar"
cls, meth = sys.argv[1], sys.argv[2]
d = zipfile.ZipFile(JAR).read(cls + ".class")
p = 10; n = struct.unpack(">H", d[8:10])[0]; cp = [None] * n; i = 1
while i < n:
    t = d[p]
    if t == 1:
        ln = struct.unpack(">H", d[p+1:p+3])[0]; cp[i] = ("utf8", d[p+3:p+3+ln].decode("utf-8", "replace")); p += 3 + ln
    elif t in (7, 8, 16, 19, 20): cp[i] = (t, struct.unpack(">H", d[p+1:p+3])[0]); p += 3
    elif t == 15: p += 4
    elif t in (9, 10, 11, 12, 17, 18): cp[i] = (t,) + struct.unpack(">HH", d[p+1:p+5]); p += 5
    elif t in (3, 4): p += 5
    elif t in (5, 6): p += 9; i += 1
    i += 1
def u(k): return cp[k][1] if cp[k] and cp[k][0] == "utf8" else "?"
def name(k):
    e = cp[k]
    if e is None: return "?"
    if e[0] == 8: return '"%s"' % u(e[1])
    if e[0] == 7: return u(e[1])
    if e[0] in (9, 10, 11):
        c = u(cp[e[1]][1]); nt = cp[e[2]]; return "%s.%s%s" % (c.split("/")[-1], u(nt[1]), u(nt[2]))
    if e[0] == 12: return u(e[1])
    return str(e)
p += 6
nif = struct.unpack(">H", d[p:p+2])[0]; p += 2 + 2 * nif
def members(p, want=None):
    cnt = struct.unpack(">H", d[p:p+2])[0]; p += 2; found = []
    for _ in range(cnt):
        acc, ni, di, ac = struct.unpack(">HHHH", d[p:p+8]); p += 8
        for _ in range(ac):
            an = struct.unpack(">H", d[p:p+2])[0]; ln = struct.unpack(">I", d[p+2:p+6])[0]
            if want and u(ni) == want and u(an) == "Code": found.append((u(di), d[p+6:p+6+ln]))
            p += 6 + ln
    return p, found
p, _ = members(p)
p, codes = members(p, meth)
OPS = {0x12: ("ldc", 1), 0x13: ("ldc_w", 2), 0xb6: ("invokevirtual", 2), 0xb7: ("invokespecial", 2), 0xb8: ("invokestatic", 2),
       0xb9: ("invokeinterface", 4), 0xb2: ("getstatic", 2), 0xb3: ("putstatic", 2), 0xb4: ("getfield", 2), 0xb5: ("putfield", 2), 0xbb: ("new", 2), 0xc1: ("instanceof", 2)}
JMP = {0x99: "ifeq", 0x9a: "ifne", 0xa7: "goto", 0xc6: "ifnull", 0xc7: "ifnonnull", 0xa5: "if_acmpeq", 0xa6: "if_acmpne"}
RET = {0xb0: "areturn", 0xac: "ireturn", 0xb1: "return"}
LEN = {0x10: 2, 0x11: 3, 0x15: 2, 0x16: 2, 0x17: 2, 0x18: 2, 0x19: 2, 0x36: 2, 0x37: 2, 0x38: 2, 0x39: 2, 0x3a: 2, 0x84: 3, 0xbc: 2, 0xbd: 3, 0xc0: 3, 0xc5: 4}
for desc, attr in codes:
    print("==", meth, desc)
    clen = struct.unpack(">I", attr[4:8])[0]; code = attr[8:8+clen]; q = 0
    while q < len(code):
        op = code[q]
        if op in OPS:
            nm, ln = OPS[op]; idx = code[q+1] if ln == 1 else struct.unpack(">H", code[q+1:q+3])[0]
            print("%4d %s %s" % (q, nm, name(idx))); q += 1 + ln
        elif op in JMP or 0x9f <= op <= 0xa4:
            off = struct.unpack(">h", code[q+1:q+3])[0]; print("%4d %s -> %d" % (q, JMP.get(op, "if_icmp"), q + off)); q += 3
        elif op in RET: print("%4d %s" % (q, RET[op])); q += 1
        elif 0x2a <= op <= 0x2d: print("%4d aload_%d" % (q, op - 0x2a)); q += 1
        elif op == 0x19: print("%4d aload %d" % (q, code[q + 1])); q += 2
        elif 0x4b <= op <= 0x4e: print("%4d astore_%d" % (q, op - 0x4b)); q += 1
        elif op == 0x3a: print("%4d astore %d" % (q, code[q + 1])); q += 2
        elif op == 0xaa or op == 0xab: print("%4d switch (parada)" % q); break
        else: q += LEN.get(op, 1)
