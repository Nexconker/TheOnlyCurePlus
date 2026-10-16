"""Ejecuta el BodyLocations.lua del mod con lupa sobre una imitación de la API del juego y la lista real de ubicaciones vanilla: imprime el orden alrededor de las ubicaciones TOC y las relaciones alt. Uso: python test_bodylocations.py"""
import re, lupa
V = r"D:\SteamLibrary\steamapps\common\ProjectZomboid\media\lua\shared\NPCs\BodyLocations.lua"
MODF = r"C:\Users\nexco\Zomboid\mods\TheOnlyCurePlus\42\media\lua\shared\TOC\BodyLocations.lua"
order = [m.group(1) for m in (re.match(r"\s*group:getOrCreateLocation\(ItemBodyLocation\.(\w+)\)", l) for l in open(V, encoding="utf-8", errors="ignore")) if m]
L = lupa.LuaRuntime(unpack_returned_tuples=True)
L.execute(r'''
ItemBodyLocation = {}
local registry = {}
function ItemBodyLocation.get(rl) local k = rl.id; if not registry[k] then registry[k] = setmetatable({id=k}, {__tostring=function(s) return s.id end}) end; return registry[k] end
ResourceLocation = { of = function(s) return {id = string.lower(s)} end }
function mkconst(name) ItemBodyLocation[name] = ItemBodyLocation.get({id = "base:" .. string.lower(name)}) end
local function newLoc(id) local loc = {id=id, multi=false, alt={}}
  function loc:getId() return self.id end
  function loc:setMultiItem(b) self.multi = b end
  return loc end
local function newGroup(name) local g = {name=name, locs={}, alt={}}
  function g:getId() return self.name end
  function g:size() return #self.locs end
  function g:getLocationByIndex(i) return self.locs[i+1] end
  function g:getOrCreateLocation(id) assert(id ~= nil, "id nil"); for _, l in ipairs(self.locs) do if l.id == id then return l end end
     local l = newLoc(id); table.insert(self.locs, l); return l end
  function g:getLocation(id) for _, l in ipairs(self.locs) do if l.id == id then return l end end end
  function g:isExclusive() return false end
  function g:isHideModel() return false end
  function g:isAltModel(a, b) local l = self:getLocation(a); return l and l.alt[b] or false end
  function g:setExclusive() end
  function g:setHideModel() end
  function g:setAltModel(a, b) local l = self:getLocation(a); assert(l, "setAltModel sin ubicacion " .. tostring(a)); l.alt[b] = true end
  function g:setMultiItem(id, b) end
  function g:isMultiItem(id) return false end
  return g end
local groups = {}
BodyLocations = {}
function BodyLocations.getGroup(n) if not groups[n] then groups[n] = newGroup(n); table.insert(groups, groups[n]) end; return groups[n] end
function BodyLocations.reset() for k in pairs(groups) do groups[k] = nil end end
function BodyLocations.getAllGroups() local list = {}; for _, g in ipairs(groups) do table.insert(list, g) end
  return { size = function() return #list end, get = function(_, i) return list[i+1] end } end
''')
for n in order: L.execute('mkconst("%s")' % n)
L.execute("local g = BodyLocations.getGroup('Human')")
for n in order: L.execute("BodyLocations.getGroup('Human'):getOrCreateLocation(ItemBodyLocation.%s)" % n)
# registries.lua del mod
L.execute("""for _, n in ipairs({"toc:arm_l","toc:arm_r","toc:armprost_l","toc:armprost_r","toc:armaccessory_l","toc:armaccessory_r","toc:leg_l","toc:leg_r","toc:legprost_l","toc:legprost_r","toc:legaccessory_l","toc:legaccessory_r"}) do ItemBodyLocation.get({id=n}) end""")
src = open(MODF, encoding="utf-8").read()
L.execute("_handlers = {}; Events = { OnGameBoot = { Add = function(f) table.insert(_handlers, f) end }, OnInitWorld = { Add = function(f) table.insert(_handlers, f) end } }")
L.execute(src)
g = L.eval("BodyLocations.getGroup('Human')")
ids = [str(g.getLocationByIndex(g, i).id) for i in range(int(g.size(g)))]
print("total", len(ids), "vanilla", len(order), "duplicados", len(ids) - len(set(ids)))
print("faltan vanilla:", [n for n in order if "base:" + n.lower() not in ids])
i = ids.index("base:long_dress"); print(" -> ".join(ids[i - 1:i + 16]))
alt = L.eval("BodyLocations.getGroup('Human'):getLocation(ItemBodyLocation.PANTS).alt")
print("PANTS alt ->", sorted(str(k.id) for k in alt.keys()))
print("JERSEY alt ->", sorted(str(k.id) for k in L.eval("BodyLocations.getGroup('Human'):getLocation(ItemBodyLocation.JERSEY).alt").keys()))
print("armprost_r alt ->", sorted(str(k.id) for k in L.eval("BodyLocations.getGroup('Human'):getLocation(ItemBodyLocation.get({id='toc:armprost_r'})).alt").keys()))

# otro mod recrea el grupo sólo con las vanilla (borra las TOC) y después se disparan los eventos
L.execute("""
local g = BodyLocations.getGroup('Human'); local keep = {}
for _, l in ipairs(g.locs) do if not string.find(l.id.id, '^toc:') then table.insert(keep, l) end end
g.locs = keep
for _, f in ipairs(_handlers) do f() end
""")
g = L.eval("BodyLocations.getGroup('Human')")
ids = [str(g.getLocationByIndex(g, i).id) for i in range(int(g.size(g)))]
print("tras borrado ajeno + eventos: TOC presentes", sum(1 for i in ids if i.startswith("toc:")), "| armprost_r alt ->",
      sorted(str(k.id) for k in L.eval("BodyLocations.getGroup('Human'):getLocation(ItemBodyLocation.get({id='toc:armprost_r'})).alt").keys()),
      "| PANTS alt ->", sorted(str(k.id) for k in L.eval("BodyLocations.getGroup('Human'):getLocation(ItemBodyLocation.PANTS).alt").keys()))
