-- footnotes.lua
-- Filtre Pandoc Lua : convertit les <span class="footnote">texte</span>
-- en vraies notes de bas de page Word.
-- Correction [LNK-001] — export Word du bulletin RDC.

function Span(span)
    if span.classes:includes('footnote') then
        -- Para (et non Plain) force le style FootnoteText dans Word,
        -- y compris quand la note est créée depuis une cellule de tableau
        -- (Plain dans ce contexte reçoit le style Compact).
        return pandoc.Note({ pandoc.Para(span.content) })
    end
end
