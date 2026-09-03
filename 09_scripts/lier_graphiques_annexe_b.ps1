param(
    [Parameter(Mandatory = $true)]
    [string]$DocxPath,

    [Parameter(Mandatory = $true)]
    [string]$WorkbookPath,

    [Parameter(Mandatory = $true)]
    [string]$ManifestPath
)

$ErrorActionPreference = "Stop"
$utf8 = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = $utf8
$OutputEncoding = $utf8
$wdFindStop = 0
$wdPasteOLEObject = 0
$wdInLine = 0
$wdWithInTable = 12
$msoTrue = -1

$word = $null
$excel = $null
$document = $null
$workbook = $null
$inserted = 0

try {
    $DocxPath = [System.IO.Path]::GetFullPath($DocxPath)
    $WorkbookPath = [System.IO.Path]::GetFullPath($WorkbookPath)
    $ManifestPath = [System.IO.Path]::GetFullPath($ManifestPath)

    if (-not (Test-Path -LiteralPath $DocxPath -PathType Leaf)) {
        throw "Document Word introuvable : $DocxPath"
    }
    if (-not (Test-Path -LiteralPath $WorkbookPath -PathType Leaf)) {
        throw "Classeur Excel introuvable : $WorkbookPath"
    }
    if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
        throw "Manifeste des graphiques introuvable : $ManifestPath"
    }

    $manifest = Get-Content -LiteralPath $ManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $chartEntries = @($manifest.charts.PSObject.Properties)

    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    $workbook = $excel.Workbooks.Open($WorkbookPath, 0, $true)

    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Open($DocxPath, $false, $false)

    foreach ($entry in $chartEntries) {
        $sheetName = [string]$entry.Value.sheet_name
        if ([string]::IsNullOrWhiteSpace($sheetName)) {
            continue
        }

        $step = "recherche du marqueur"
        try {
            $marker = "[[ANNEXE_B_CHART:$sheetName]]"
            $range = $document.Content
            $find = $range.Find
            $find.ClearFormatting()
            $found = $find.Execute($marker, $false, $false, $false, $false, $false, $true, $wdFindStop)
            if (-not $found) {
                continue
            }

            $step = "copie du graphique Excel"
            $worksheet = $workbook.Worksheets.Item($sheetName)
            $chartObject = $worksheet.ChartObjects(1)
            $worksheet.Activate()
            $chartObject.Activate()
            $chartObject.Copy()
            Start-Sleep -Milliseconds 400

            $step = "collage lié dans Word"
            $isInTable = [bool]$range.Information($wdWithInTable)
            $range.Text = ""
            $range.Collapse(0)
            $insertionStart = $range.Start
            $range.PasteSpecial($null, $true, $wdInLine, $false, $wdPasteOLEObject)
            Start-Sleep -Milliseconds 200

            $step = "dimensionnement du graphique"
            $inlineShape = $null
            for ($i = 1; $i -le $document.InlineShapes.Count; $i++) {
                $candidate = $document.InlineShapes.Item($i)
                if ([Math]::Abs($candidate.Range.Start - $insertionStart) -le 2) {
                    $inlineShape = $candidate
                    break
                }
                [void][Runtime.InteropServices.Marshal]::ReleaseComObject($candidate)
            }
            if ($inlineShape -eq $null) {
                for ($i = 1; $i -le $document.Shapes.Count; $i++) {
                    $candidateShape = $document.Shapes.Item($i)
                    if ([Math]::Abs($candidateShape.Anchor.Start - $insertionStart) -le 2) {
                        $inlineShape = $candidateShape.ConvertToInlineShape()
                        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($candidateShape)
                        break
                    }
                    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($candidateShape)
                }
            }
            if ($inlineShape -eq $null) {
                throw "Objet collé introuvable (InlineShapes=$($document.InlineShapes.Count), Shapes=$($document.Shapes.Count))."
            }
            $inlineShape.LockAspectRatio = $msoTrue
            if ($isInTable) {
                $inlineShape.Width = 225
            } else {
                $inlineShape.Width = 440
            }
            if ($inlineShape.LinkFormat -ne $null) {
                $inlineShape.LinkFormat.AutoUpdate = $true
            }
            $inserted += 1
        }
        catch {
            throw "Feuille '$sheetName', étape '$step' : $($_.Exception.Message)"
        }

        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($chartObject)
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($worksheet)
    }

    if ($inserted -ne 42) {
        throw "Nombre de graphiques liés inattendu : $inserted inséré(s), 42 attendu(s)."
    }

    $document.Save()
    Write-Output "[ANNEXE-B] $inserted graphiques Excel liés insérés dans Word."
}
finally {
    if ($document -ne $null) {
        try { $document.Close($false) } catch {}
        try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($document) } catch {}
    }
    if ($word -ne $null) {
        try { $word.Quit() } catch {}
        try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word) } catch {}
    }
    if ($workbook -ne $null) {
        try { $workbook.Close($false) } catch {}
        try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($workbook) } catch {}
    }
    if ($excel -ne $null) {
        try { $excel.Quit() } catch {}
        try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel) } catch {}
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
