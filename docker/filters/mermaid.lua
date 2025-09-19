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

-- Make SVGs render at a sensible, responsive size without relying on CSS.
-- Heuristic: use viewBox width to choose a default width percentage.
local function tune_svg(svg, opts)
  if type(svg) ~= 'string' then
    return svg
  end
  opts = opts or {}
  local open_tag = svg:match('<svg[^>]*>')
  if not open_tag then
    return svg
  end

  -- Extract attributes we care about
  local viewbox = open_tag:match('view[Bb]ox%s*=%s*"([^"]+)"') or open_tag:match("view[Bb]ox%s*=%s*'([^']+)'")
  local width_attr = open_tag:match('width%s*=%s*"([^"]+)"') or open_tag:match("width%s*=%s*'([^']+)'")
  local height_attr = open_tag:match('height%s*=%s*"([^"]+)"') or open_tag:match("height%s*=%s*'([^']+)'")
  local style_attr = open_tag:match('style%s*=%s*"([^"]*)"') or open_tag:match("style%s*=%s*'([^']*)'")

  -- Determine width percent from viewBox width if available
  local width_percent = tonumber(opts.width_percent or '') or 100
  if viewbox then
    local nums = {}
    for n in viewbox:gmatch('[-%d%.]+') do
      nums[#nums+1] = tonumber(n)
    end
    local vbw = nums[3] or 0
    if vbw > 0 and (not opts.width_percent) then
      if vbw < 500 then
        width_percent = 60
      elseif vbw < 900 then
        width_percent = 80
      else
        width_percent = 100
      end
    end
  elseif not opts.width_percent then
    -- No viewBox: pick a safe default
    width_percent = 80
  end

  -- Build new style string
  local extra_style = string.format('width:%d%%;height:auto;max-width:100%%;', width_percent)
  local new_style
  if style_attr and #style_attr > 0 then
    -- Append, avoiding duplicate width/height if present
    local cleaned = style_attr
      :gsub('%s*width%s*:%s*[^;]*;?', '')
      :gsub('%s*height%s*:%s*[^;]*;?', '')
    if #cleaned > 0 and cleaned:sub(-1) ~= ';' then
      cleaned = cleaned .. ';'
    end
    new_style = cleaned .. extra_style
  else
    new_style = extra_style
  end

  -- Remove fixed width/height attributes to allow responsive sizing only if viewBox is present
  local new_open = open_tag
  if viewbox then
    new_open = new_open
      :gsub('%s+width%s*=%s*"[^"]*"', '')
      :gsub("%s+width%s*=%s*'[^']*'", '')
      :gsub('%s+height%s*=%s*"[^"]*"', '')
      :gsub("%s+height%s*=%s*'[^']*'", '')
  end

  -- Ensure preserveAspectRatio is set for proper scaling
  if not new_open:match('preserveAspectRatio%s*=') then
    new_open = new_open:gsub('>$', ' preserveAspectRatio="xMidYMid meet">')
  end

  -- Upsert style attribute
  if new_open:match('style%s*=') then
    new_open = new_open
      :gsub('style%s*=%s*"[^"]*"', function() return 'style="' .. new_style .. '"' end)
      :gsub("style%s*=%s*'[^']*'", function() return "style='" .. new_style .. "'" end)
  else
    new_open = new_open:gsub('>$', function() return ' style="' .. new_style .. '">' end)
  end

  -- Replace only the first <svg ...> tag (plain find)
  local s, e = string.find(svg, open_tag, 1, true)
  if s then
    return svg:sub(1, s - 1) .. new_open .. svg:sub(e + 1)
  else
    return svg
  end
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
  -- Inspect code block attributes for optional sizing control
  local desired_percent
  local attr_width = el.attributes["width"] or el.attributes["data-width"]
  if attr_width then
    local p = attr_width:match('^(%d+)%%$')
    if p then desired_percent = tonumber(p) end
    if not desired_percent then
      local num = tonumber(attr_width)
      if num then
        if num <= 2 then
          desired_percent = math.floor(num * 100 + 0.5)
        elseif num <= 100 then
          desired_percent = math.floor(num + 0.5)
        end
      end
    end
  end
  local scale = el.attributes["scale"] or el.attributes["data-scale"]
  local scale_num = tonumber(scale)
  if scale_num and scale_num > 0 and not desired_percent then
    -- Apply scale to heuristic defaults (handled in tune_svg via opts.width_percent)
    -- We'll compute after we know heuristic; here we pass a hint to scale the result later.
  end

  local tuned = tune_svg(data, { width_percent = desired_percent })
  if scale_num and scale_num > 0 then
    -- Adjust the inline style width by scaling factor
  local current_style = tuned:match('<svg[^>]-style%s*=%s*"([^"]*)"') or tuned:match("<svg[^>]-style%s*=%s*'([^']*)'")
    if current_style then
      local w = current_style:match('width%s*:%s*(%d+)%%')
      if w then
        local newp = math.max(10, math.min(100, math.floor(tonumber(w) * scale_num + 0.5)))
        local new_style = current_style:gsub('width%s*:%s*%d+%%', 'width:' .. newp .. '%%')
        tuned = tuned:gsub('style%s*=%s*"[^"]*"', function() return 'style="' .. new_style .. '"' end)
        tuned = tuned:gsub("style%s*=%s*'[^']*'", function() return "style='" .. new_style .. "'" end)
      end
    end
  end
  -- Inline the SVG so sizing is self-contained and not CSS-dependent.
  return pandoc.RawBlock('html', tuned)
end
