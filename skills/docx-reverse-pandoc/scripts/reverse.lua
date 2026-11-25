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

function Span(el)
  if el.attributes["custom-style"] == "Footnote Reference" and #el.content == 0 then
    return {}
  end
end

function Str(el)
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
