local widths = {}
local f = io.open("table-widths.txt")
if f then
  for line in f:lines() do
    local row, sum = {}, 0
    for n in line:gmatch("%d+") do
      row[#row + 1] = tonumber(n)
      sum = sum + tonumber(n)
    end
    widths[#widths + 1] = { row = row, sum = sum }
  end
  f:close()
end

local table_styles = {}
local sf = io.open("table-styles.txt")
if sf then
  for line in sf:lines() do
    table_styles[#table_styles + 1] = line
  end
  sf:close()
end

local empties = {}
local ef = io.open("empty-paragraphs.txt")
if ef then
  for line in ef:lines() do
    empties[#empties + 1] = line
  end
  ef:close()
end

local apply, count = false, 0

local function check(doc)
  local n = 0
  doc:walk({ Table = function() n = n + 1 end })
  apply = n == #widths
  if #widths > 0 and not apply then
    io.stderr:write("build.lua: the document has " .. n .. " tables but table-widths.txt lists " .. #widths .. "; widths not applied\n")
  end
end

local function fit(el)
  count = count + 1
  local changed = false
  local style = table_styles[count]
  if apply and style and style ~= "" then
    el.attributes["custom-style"] = style
    changed = true
  end
  local w = widths[count]
  if apply and w and w.sum > 0 and #w.row == #el.colspecs then
    local specs = {}
    for k, spec in ipairs(el.colspecs) do
      specs[k] = { spec[1], w.row[k] / w.sum }
    end
    el.colspecs = specs
    changed = true
  end
  if changed then
    return el
  end
end

local function toc(el)
  if el.format == "html" then
    local n = el.text:match("^%s*<!%-%-%s*P(%d+)%s*%-%->%s*$")
    if n and empties[tonumber(n)] then
      return pandoc.RawBlock("openxml", empties[tonumber(n)])
    end
    local close, b = el.text:match("^%s*<!%-%-%s*(/?)TEXTBOX (%d+)%s*%-%->%s*$")
    if b then
      return pandoc.RawBlock("openxml", "<w:p><w:r><w:t>TXBX" .. (close == "/" and "END" or "BEGIN") .. b .. "END</w:t></w:r></w:p>")
    end
  end
  if el.format == "html" and el.text:match("^%s*<!%-%-%s*TOC%s*%-%->%s*$") then
    local t = io.open("toc.xml")
    if t then
      local xml = t:read("a")
      t:close()
      return pandoc.RawBlock("openxml", xml)
    end
  end
end

return { { Pandoc = check }, { Table = fit, RawBlock = toc } }
