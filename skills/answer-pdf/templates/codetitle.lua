-- ```{.js title="server.js"} shows "server.js" in the box's title bar.
function CodeBlock(el)
  local opt = ''
  local t = el.attributes.title
  if t then
    el.attributes.title = nil
    opt = '[title={' .. pandoc.write(pandoc.Pandoc { pandoc.Plain { pandoc.Str(t) } }, 'latex') .. '}]'
  end
  return { pandoc.RawBlock('latex', '\\begin{codebox}' .. opt), el, pandoc.RawBlock('latex', '\\end{codebox}') }
end

function Table(t)
  for _, row in ipairs(t.head.rows) do
    for _, cell in ipairs(row.cells) do
      cell.contents = cell.contents:walk { Plain = function(p) return pandoc.Plain { pandoc.Strong(p.content) } end }
    end
  end
  return t
end

-- ```{.tree} with one entry per line, two spaces per level, folders ending in "/",
-- and an optional note after " # ". Becomes a forest folder tree with icons.
local function tex(s)
  return (pandoc.write(pandoc.Pandoc { pandoc.Plain { pandoc.Str(s) } }, 'latex'):gsub('%s+$', ''))
end

local function tree(el)
  local out, open = {}, {}
  for line in el.text:gmatch('[^\n]+') do
    local indent, body = line:match('^(%s*)(.-)%s*$')
    local depth = #indent // 2
    local name, note = body:match('^(.-)%s+#%s+(.*)$')
    name = name or body
    while #open > 0 and open[#open] >= depth do out[#out + 1] = ']'; open[#open] = nil end
    local node = name == '...' and '\\texttt{...}'
      or name:sub(-1) == '/' and '\\treefolder{' .. tex(name) .. '}'
      or '\\treefile{' .. tex(name) .. '}'
    if note then node = node .. '\\treenote{' .. tex(note) .. '}' end
    out[#out + 1] = '[{' .. node .. '}'
    open[#open + 1] = depth
  end
  for _ = 1, #open do out[#out + 1] = ']' end
  return pandoc.RawBlock('latex', '\\begin{treebox}\\begin{forest}filetree\n' .. table.concat(out, '\n') .. '\n\\end{forest}\\end{treebox}')
end

local function diff(el)
  local function esc(t) return (pandoc.write(pandoc.Pandoc { pandoc.Plain { pandoc.Str((t:gsub(' ', '\u{a0}'))) } }, 'latex'):gsub('%s+$', '')) end
  local numbered = el.classes:includes('numbered')
  local old, new = 0, 0
  local out = {}
  for line in (el.text .. '\n'):gmatch('(.-)\n') do
    local c = line:sub(1, 1)
    local bg = c == '+' and 'diffadd' or c == '-' and 'diffdel' or c == '@' and 'diffhunk' or 'white'
    local body = esc(line)
    if c == '+' or c == '-' then
      body = '\\textcolor{diff' .. (c == '+' and 'add' or 'del') .. 'sign}{\\textbf{' .. esc(c) .. '}}' .. esc(line:sub(2))
    end
    if numbered then
      local o, n = '', ''
      if c == '@' then
        local a, b = line:match('^@@ %-(%d+)[^+]*%+(%d+)')
        old, new = tonumber(a or 1), tonumber(b or 1)
      elseif c == '-' then o = old; old = old + 1
      elseif c == '+' then n = new; new = new + 1
      else o, n = old, new; old = old + 1; new = new + 1 end
      body = '\\difflnum{' .. o .. '}\\difflnum{' .. n .. '}' .. body
    end
    out[#out + 1] = '\\diffline{' .. bg .. '}{' .. body .. '}'
  end
  local opt = el.attributes.title and '[title={' .. tex(el.attributes.title) .. '}]' or ''
  return pandoc.RawBlock('latex', '\\begin{codebox}' .. opt .. '\n' .. table.concat(out, '\n') .. '\n\\end{codebox}')
end

local codeblock = CodeBlock
function CodeBlock(el)
  if el.classes:includes('diff') then return diff(el) end
  if el.classes:includes('tree') then return tree(el) end
  return codeblock(el)
end

-- Long paths in body text (e.g. ~/your8DigitSID_exe02/task2/public) have no spaces,
-- so LaTeX cannot wrap them. Allow a line break after each "/".
function Str(el)
  if #el.text < 20 or not el.text:find('/') then return nil end
  local out = {}
  for part, slash in el.text:gmatch('([^/]*)(/?)') do
    if part ~= '' then out[#out + 1] = pandoc.Str(part) end
    if slash ~= '' then
      out[#out + 1] = pandoc.Str('/')
      out[#out + 1] = pandoc.RawInline('latex', '\\allowbreak{}')
    end
  end
  return out
end
