-- table_borders.lua
-- Filtre Pandoc Lua : force des bordures complètes sur tous les tableaux.
-- Correction [TAB-001] — export Word du bulletin RDC.
-- Compatible Pandoc 3.x

local border_xml = '<w:tcPr><w:tcBorders>' ..
    '<w:top w:val="single" w:sz="4" w:space="0" w:color="000000"/>' ..
    '<w:left w:val="single" w:sz="4" w:space="0" w:color="000000"/>' ..
    '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="000000"/>' ..
    '<w:right w:val="single" w:sz="4" w:space="0" w:color="000000"/>' ..
    '</w:tcBorders></w:tcPr>'

local function add_borders_to_cell(cell)
    local raw = pandoc.RawBlock('openxml', border_xml)
    table.insert(cell.contents, 1, raw)
    return cell
end

local function process_rows(rows)
    if not rows then return rows end
    for i, row in ipairs(rows) do
        for j, cell in ipairs(row.cells) do
            rows[i].cells[j] = add_borders_to_cell(cell)
        end
    end
    return rows
end

function Table(tbl)
    -- En-tête
    if tbl.head and tbl.head.rows then
        tbl.head.rows = process_rows(tbl.head.rows)
    end

    -- Corps
    if tbl.bodies then
        for b, body in ipairs(tbl.bodies) do
            if body.body then
                tbl.bodies[b].body = process_rows(body.body)
            end
        end
    end

    -- Pied
    if tbl.foot and tbl.foot.rows then
        tbl.foot.rows = process_rows(tbl.foot.rows)
    end

    return tbl
end
