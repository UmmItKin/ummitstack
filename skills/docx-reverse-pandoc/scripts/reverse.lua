local managed = {
  ["Body Text"] = true, ["First Paragraph"] = true, ["Compact"] = true,
  ["Captioned Figure"] = true, ["Image Caption"] = true, ["Table Caption"] = true,
  ["Footnote Text"] = true, ["Block Text"] = true,
}

local has_toc = io.open("toc.xml") ~= nil
local seen_toc = false

function Div(el)
  local s = el.attributes["custom-style"]
  if has_toc and s and s:match("^toc %d") then
    if not seen_toc then
      seen_toc = true
      return pandoc.RawBlock("html", "<!-- TOC -->")
    end
    return {}
  end
  if managed[s] then
    return el.content
  end
end

function Header(el)
  if el.classes:includes("TOC-Heading") then
    return pandoc.Div({ pandoc.Para(el.content) }, pandoc.Attr("", {}, { ["custom-style"] = "TOC Heading" }))
  end
end

-- A raw space run sits outside Pandoc's own formatting, so its span style, bold and italic are written in here.
local SPACE_RUN = '^<w:r>(.-)<w:t xml:space="preserve">( +)</w:t></w:r>$'

local function with_props(el, front, back)
  return el:walk({
    Str = function(s)
      local n = s.text:match("^SPMK(%d+)SPMK$")
      if n then
        return pandoc.RawInline("openxml", '<w:r><w:rPr>' .. front .. back .. '</w:rPr><w:t xml:space="preserve">' .. string.rep(" ", tonumber(n)) .. "</w:t></w:r>")
      end
    end,
    RawInline = function(r)
      local pr, sp = r.text:match(SPACE_RUN)
      if r.format == "openxml" and sp then
        pr = pr:match("^<w:rPr>(.*)</w:rPr>$") or ""
        return pandoc.RawInline("openxml", '<w:r><w:rPr>' .. front .. pr .. back .. '</w:rPr><w:t xml:space="preserve">' .. sp .. "</w:t></w:r>")
      end
    end,
  })
end

function Strong(el)
  return with_props(el, "", "<w:b/><w:bCs/>")
end

function Emph(el)
  return with_props(el, "", "<w:i/><w:iCs/>")
end

function Span(el)
  local style = el.attributes["custom-style"]
  if style == "Footnote Reference" and #el.content == 0 then
    return {}
  end
  if style then
    return with_props(el, '<w:rStyle w:val="' .. style .. '"/>', "")
  end
end

-- markers with no spaces around them, so Pandoc keeps them inside the text and its span
local function marker(kind, n)
  if kind == "TABMK" then
    return pandoc.RawInline("openxml", "<w:r><w:tab/></w:r>")
  end
  if kind == "SHPMK" then
    return pandoc.RawInline("openxml", "<w:r><!--SHAPE " .. n .. "--></w:r>")
  end
  return pandoc.RawInline("openxml", '<w:r><w:t xml:space="preserve">' .. string.rep(" ", tonumber(n)) .. "</w:t></w:r>")
end

function Str(el)
  if el.text:find("S[H]?PMK%d+S[H]?PMK") or el.text:find("TABMK%d+TABMK") then
    local out, rest = {}, el.text
    while true do
      local a, b, kind, n
      for _, k in ipairs({ "SPMK", "SHPMK", "TABMK" }) do
        local x, y, m = rest:find(k .. "(%d+)" .. k)
        if x and (not a or x < a) then a, b, kind, n = x, y, k, m end
      end
      if not a then break end
      if a > 1 then out[#out + 1] = pandoc.Str(rest:sub(1, a - 1)) end
      out[#out + 1] = marker(kind, n)
      rest = rest:sub(b + 1)
    end
    if #rest > 0 then out[#out + 1] = pandoc.Str(rest) end
    return out
  end
  if el.text == "PAGEBREAKMARK" then
    return pandoc.RawInline("openxml", '<w:r><w:br w:type="page"/></w:r>')
  end
  if el.text == "TABMARK" then
    return pandoc.RawInline("openxml", "<w:r><w:tab/></w:r>")
  end
end

function Para(el)
  if #el.content == 1 and el.content[1].t == "Str" then
    local n = el.content[1].text:match("^EMPTYPARAMARK(%d+)END$")
    if n then
      return pandoc.RawBlock("html", "<!-- P" .. n .. " -->")
    end
    local edge, b = el.content[1].text:match("^TXBX(%u+)(%d+)END$")
    if edge == "BEGIN" then
      return pandoc.RawBlock("html", "<!-- TEXTBOX " .. b .. " -->")
    elseif edge == "END" then
      return pandoc.RawBlock("html", "<!-- /TEXTBOX " .. b .. " -->")
    end
  end
  if #el.content == 1 and el.content[1].t == "Image" then
    local img = el.content[1]
    local alt = pandoc.utils.stringify(img.caption)
    if alt ~= "" then
      img.attributes["alt"] = alt
      img.caption = {}
      return pandoc.Para({ img })
    end
  end
end

function Figure(el)
  el.attr = pandoc.Attr(el.identifier)
  return el
end
