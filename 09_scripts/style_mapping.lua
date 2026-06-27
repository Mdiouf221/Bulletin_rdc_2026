-- style_mapping.lua
-- Filtre Pandoc Lua : gère les éléments UI à supprimer et les cellules de tableau.
-- Correction [STY-001] — export Word du bulletin RDC.
--
-- Note : le style des paragraphes (Body Text, Source, GraphicTitle…) est géré
-- en amont dans apply_corrections() via des <div custom-style="…"> Pandoc.
-- Ce filtre ne modifie pas les Para (pas de propriété attr sur Para en Lua).

-- ---------------------------------------------------------------------------
-- Tableaux : TableHeader pour l'en-tête, TableText pour les cellules corps
-- ---------------------------------------------------------------------------

local function wrap_para(para, style)
    return pandoc.Div({para}, pandoc.Attr("", {}, {["custom-style"] = style}))
end

local function style_cell(cell, style)
    local new_contents = {}
    for _, block in ipairs(cell.contents) do
        if block.t == "Para" then
            table.insert(new_contents, wrap_para(block, style))
        elseif block.t == "Plain" then
            -- Pandoc crée des blocs Plain (pas Para) pour les <td> sans <p>.
            -- On convertit en Para pour pouvoir appliquer le custom-style.
            table.insert(new_contents, wrap_para(pandoc.Para(block.content), style))
        else
            table.insert(new_contents, block)
        end
    end
    cell.contents = new_contents
    return cell
end

local function process_rows(rows, style)
    if not rows then return rows end
    for i, row in ipairs(rows) do
        for j, cell in ipairs(row.cells) do
            rows[i].cells[j] = style_cell(cell, style)
        end
    end
    return rows
end

function Table(tbl)
    -- Appliquer le style ILOTable sur le tableau (gère automatiquement
    -- les styles header/body selon la définition du style dans le template)
    if tbl.attr then
        tbl.attr.attributes["custom-style"] = "ILOTable"
    end

    -- Envelopper explicitement les Para des cellules en-tête en TableHeader
    if tbl.head and tbl.head.rows then
        tbl.head.rows = process_rows(tbl.head.rows, "TableHeader")
    end
    -- Envelopper explicitement les Para des cellules corps en TableText
    if tbl.bodies then
        for b, body in ipairs(tbl.bodies) do
            if body.body then
                tbl.bodies[b].body = process_rows(body.body, "TableText")
            end
        end
    end
    if tbl.foot and tbl.foot.rows then
        tbl.foot.rows = process_rows(tbl.foot.rows, "TableText")
    end
    return tbl
end

-- ---------------------------------------------------------------------------
-- Span : supprimer les éléments UI (badges, annotations inline)
-- ---------------------------------------------------------------------------

local SPAN_REMOVE = {
    ["valid-badge"]      = true,
    ["status-dot"]       = true,
    ["status-brouillon"] = true,
    ["status-arevoir"]   = true,
    ["status-redige"]    = true,
    ["status-revu"]      = true,
    ["status-valide"]    = true,
}

function Span(span)
    for cls, _ in pairs(SPAN_REMOVE) do
        if span.classes:includes(cls) then
            return {}
        end
    end
    if span.classes:includes("val") or
       span.classes:includes("val-cite") or
       span.classes:includes("val-para") then
        return span.content
    end
    return span
end

