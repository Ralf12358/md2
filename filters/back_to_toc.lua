local toc_enabled = false

function Meta(m)
  if m and m.toc ~= nil then
    toc_enabled = m.toc ~= false
  elseif m and m["table-of-contents"] ~= nil then
    toc_enabled = m["table-of-contents"] ~= false
  else
    toc_enabled = false
  end
  return nil
end

local function is_docx()
  return FORMAT:match("docx") ~= nil
end

function Header(h)
  if not toc_enabled or not is_docx() then return nil end
  if h.level and h.level >= 2 then
    local space = pandoc.Space()
    local link = pandoc.Link(pandoc.Inlines(pandoc.Str("⇧ TOC")), "#TOC", "", { class = "toc-back" })
    h.content:insert(space)
    h.content:insert(link)
    return h
  end
  return nil
end

function Pandoc(doc)
  if not toc_enabled or not is_docx() then return nil end
  local blocks = doc.blocks
  local attr = pandoc.Attr("TOC", {}, {})
  local anchor = pandoc.Div({}, attr)
  table.insert(blocks, 1, anchor)
  doc.blocks = blocks
  return doc
end
