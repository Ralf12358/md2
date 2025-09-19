local sha1 = require('pandoc.utils').sha1

local function url_encode(data)
  -- URL-encode SVG data for data URI
  local result = {}
  for i = 1, #data do
    local c = data:sub(i, i)
    local byte = string.byte(c)
    if (byte >= 65 and byte <= 90) or   -- A-Z
       (byte >= 97 and byte <= 122) or  -- a-z
       (byte >= 48 and byte <= 57) or   -- 0-9
       c == '-' or c == '_' or c == '.' or c == '~' then
      result[#result + 1] = c
    else
      result[#result + 1] = string.format("%%%02X", byte)
    end
  end
  return table.concat(result)
end

local function mermaid_image(code)
  local hash = sha1(code)
  local base = '/tmp/mermaid-' .. hash
  local infile = base .. '.mmd'
  local outfile = base .. '.svg'
  local f = assert(io.open(infile, 'w'))
  f:write(code)
  f:close()
  local ok, err = pcall(function()
    pandoc.pipe('mermaid', {'-i', infile, '-o', outfile, '-b', 'transparent'}, '')
  end)
  os.remove(infile)
  if not ok then
    return nil, 'mermaid cli failed: ' .. tostring(err)
  end
  return outfile
end

function CodeBlock(el)
  if not el.classes:includes('mermaid') then
    return nil
  end
  local out, err = mermaid_image(el.text)
  if not out then
    io.stderr:write('[mermaid] generation failed: ' .. err .. '\n')
    return nil
  end
  local f = io.open(out, 'rb')
  if not f then
    io.stderr:write('[mermaid] cannot read output: ' .. out .. '\n')
    return nil
  end
  local data = f:read('*all')
  f:close()
  os.remove(out)
  local target = 'data:image/svg+xml;charset=utf-8,' .. url_encode(data)
  local img = pandoc.Image({}, target)
  img.attributes["style"] = "max-width:100%;height:auto;"
  return pandoc.Para({ img })
end
