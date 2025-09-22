local done = false

function Header(el)
  if not done and el.level == 1 then
    if el.attr and el.attr.classes then
      table.insert(el.attr.classes, 'unlisted')
    end
    done = true
  end
  return el
end
