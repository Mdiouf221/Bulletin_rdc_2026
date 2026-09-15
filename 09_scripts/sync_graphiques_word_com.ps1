param(
    [Parameter(Mandatory = $true)]
    [string]$WorkbookPath,

    [Parameter(Mandatory = $true)]
    [string]$UpdatePlanPath,

    [Parameter(Mandatory = $true)]
    [string]$DocxPath,

    [Parameter(Mandatory = $true)]
    [string]$WorkbookSourceName,

    [Parameter(Mandatory = $false)]
    [ValidateSet("embedded", "linked")]
    [string]$WordMode = "embedded",

    [Parameter(Mandatory = $false)]
    [int]$ExpectedWordTargetCount = 0
)

$ErrorActionPreference = "Stop"
$utf8 = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = $utf8
$OutputEncoding = $utf8

$excel = $null
$word = $null
$workbook = $null
$document = $null

try {
    $WorkbookPath = [System.IO.Path]::GetFullPath($WorkbookPath)
    $UpdatePlanPath = [System.IO.Path]::GetFullPath($UpdatePlanPath)
    $DocxPath = [System.IO.Path]::GetFullPath($DocxPath)
    $WorkbookSourceName = [System.IO.Path]::GetFileName($WorkbookSourceName)

    if (-not (Test-Path -LiteralPath $WorkbookPath -PathType Leaf)) {
        throw "Classeur introuvable : $WorkbookPath"
    }
    if (-not (Test-Path -LiteralPath $UpdatePlanPath -PathType Leaf)) {
        throw "Plan JSON introuvable : $UpdatePlanPath"
    }
    if (-not (Test-Path -LiteralPath $DocxPath -PathType Leaf)) {
        throw "Document Word introuvable : $DocxPath"
    }

    $plan = Get-Content -LiteralPath $UpdatePlanPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $sheetPlans = @($plan.sheets)
    if ($sheetPlans.Count -le 0) {
        throw "Plan vide : aucune feuille à mettre à jour."
    }

    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    $workbook = $excel.Workbooks.Open($WorkbookPath, 0, $false)

    $cellsExamined = 0
    $cellsChanged = 0
    $cellsUnchanged = 0
    $cellsWritten = 0
    $sheetsTouched = 0
    $workbookChartCount = 0

    foreach ($sheetPlan in $sheetPlans) {
        $sheetName = [string]$sheetPlan.sheet_name
        if ([string]::IsNullOrWhiteSpace($sheetName)) {
            throw "Nom de feuille vide dans le plan."
        }
        $worksheet = $null
        try {
            $worksheet = $workbook.Worksheets.Item($sheetName)
        }
        catch {
            throw "Feuille introuvable dans le classeur : $sheetName"
        }

        try {
            $charts = $worksheet.ChartObjects()
            $actualChartCount = [int]$charts.Count
            $expectedChartCount = [int]$sheetPlan.expected_chart_count
            if ($expectedChartCount -gt 0 -and $actualChartCount -ne $expectedChartCount) {
                throw "Feuille '$sheetName' : $actualChartCount graphique(s), $expectedChartCount attendu(s)."
            }
            $workbookChartCount += $actualChartCount

            $updates = @($sheetPlan.updates)
            foreach ($u in $updates) {
                $row = [int]$u.row
                $col = [int]$u.col
                $value = $u.value
                $isChanged = $true
                if ($null -ne $u.changed) {
                    $isChanged = [bool]$u.changed
                }
                $cellsExamined += 1
                if (-not $isChanged) {
                    $cellsUnchanged += 1
                    continue
                }
                try {
                    if ($null -eq $value) {
                        $worksheet.Cells.Item($row, $col).ClearContents() | Out-Null
                    }
                    else {
                        $excelValue = $value
                        if ($value -is [string]) {
                            $parsed = 0.0
                            if ([double]::TryParse(
                                $value,
                                [System.Globalization.NumberStyles]::Float,
                                [System.Globalization.CultureInfo]::InvariantCulture,
                                [ref]$parsed
                            )) {
                                $excelValue = $parsed
                            }
                        }
                        elseif (
                            $value -is [byte] -or
                            $value -is [int16] -or
                            $value -is [int32] -or
                            $value -is [int64] -or
                            $value -is [single] -or
                            $value -is [double] -or
                            $value -is [decimal]
                        ) {
                            $excelValue = [double]$value
                        }
                        $worksheet.Cells.Item($row, $col).Value2 = $excelValue
                    }
                }
                catch {
                    throw "Échec écriture cellule $sheetName!R$row`C$col (valeur=$value) : $($_.Exception.Message)"
                }
                $cellsChanged += 1
                $cellsWritten += 1
            }
            $sheetsTouched += 1
        }
        finally {
            if ($worksheet -ne $null) {
                try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($worksheet) } catch {}
            }
        }
    }

    $workbook.Save()
    $workbook.Close($false)
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($workbook)
    $workbook = $null

    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Open($DocxPath, $false, $false)

    $inlineBefore = [int]$document.InlineShapes.Count
    $targetIndices = New-Object 'System.Collections.Generic.List[int]'
    for ($i = 1; $i -le $document.InlineShapes.Count; $i++) {
        $shape = $document.InlineShapes.Item($i)
        try {
            $sourceName = ""
            try { $sourceName = [string]$shape.LinkFormat.SourceName } catch {}
            if (
                -not [string]::IsNullOrWhiteSpace($sourceName) -and
                $sourceName.ToLowerInvariant() -ne "null"
            ) {
                $base = [System.IO.Path]::GetFileName($sourceName)
                if ($base.ToLowerInvariant() -eq $WorkbookSourceName.ToLowerInvariant()) {
                    [void]$targetIndices.Add($i)
                }
            }
        }
        finally {
            try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($shape) } catch {}
        }
    }

    if ($ExpectedWordTargetCount -gt 0 -and $targetIndices.Count -ne $ExpectedWordTargetCount) {
        throw "Objets Word cibles inattendus : $($targetIndices.Count) trouvés, $ExpectedWordTargetCount attendus."
    }
    if ($targetIndices.Count -le 0) {
        throw "Aucun objet Word lié au classeur source '$WorkbookSourceName' n'a été trouvé."
    }

    $updatedWordObjects = 0
    foreach ($idx in $targetIndices) {
        $shape = $null
        try {
            $shape = $document.InlineShapes.Item($idx)
            $shape.LinkFormat.SourceFullName = $WorkbookPath
            try { $shape.LinkFormat.AutoUpdate = $true } catch {}
            $shape.LinkFormat.Update()
            if ($WordMode -eq "embedded") {
                $shape.LinkFormat.BreakLink()
            }
            $updatedWordObjects += 1
        }
        finally {
            if ($shape -ne $null) {
                try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($shape) } catch {}
            }
        }
    }

    $linkedAfter = 0
    $embeddedAfter = 0
    for ($i = 1; $i -le $document.InlineShapes.Count; $i++) {
        $shape = $document.InlineShapes.Item($i)
        try {
            $hasLink = $false
            try {
                $tmp = [string]$shape.LinkFormat.SourceName
                if (-not [string]::IsNullOrWhiteSpace($tmp) -and $tmp.ToLowerInvariant() -ne "null") {
                    $hasLink = $true
                }
            } catch {}

            if ($hasLink) {
                $linkedAfter += 1
            }
            else {
                try {
                    $prog = [string]$shape.OLEFormat.ProgID
                    if (-not [string]::IsNullOrWhiteSpace($prog)) {
                        $embeddedAfter += 1
                    }
                } catch {}
            }
        }
        finally {
            try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($shape) } catch {}
        }
    }

    $document.Save()

    $result = [PSCustomObject]@{
        cells_examined = [int]$cellsExamined
        cells_changed = [int]$cellsChanged
        cells_unchanged = [int]$cellsUnchanged
        cells_written = [int]$cellsWritten
        sheets_touched = [int]$sheetsTouched
        workbook_chart_count = [int]$workbookChartCount
        word_target_count = [int]$targetIndices.Count
        word_updated_objects = [int]$updatedWordObjects
        word_inline_before = [int]$inlineBefore
        word_inline_after = [int]$document.InlineShapes.Count
        word_linked_after = [int]$linkedAfter
        word_embedded_after = [int]$embeddedAfter
        word_mode = $WordMode
    }
    $result | ConvertTo-Json -Depth 6 -Compress
}
catch {
    $lineNo = $_.InvocationInfo.ScriptLineNumber
    $line = $_.InvocationInfo.Line
    $msg = $_.Exception.Message
    throw "SYNC_COM_FAILURE line ${lineNo}: $msg`n$line"
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
