param(
    [Parameter(Mandatory = $true)]
    [string]$DocxPath,

    [Parameter(Mandatory = $true)]
    [string]$ManifestPath,

    [Parameter(Mandatory = $false)]
    [string]$WorkbookPath = "",

    [Parameter(Mandatory = $false)]
    [ValidateSet("linked", "embedded")]
    [string]$PasteMode = "linked",

    [Parameter(Mandatory = $false)]
    [int]$ExpectedCount = 0,

    [Parameter(Mandatory = $false)]
    [string]$LogPath = ""
)

$ErrorActionPreference = "Stop"
$utf8 = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = $utf8
$OutputEncoding = $utf8

$wdFindStop = 0
$wdPasteOLEObject = 0
$wdInLine = 0
$wdWithInTable = 12
$wdCollapseStart = 1
$msoTrue = -1
$pasteRetryDelayMs = 75
$pasteMaxAttempts = 40
$shapeWaitTimeoutMs = 3000

function Write-StepLog {
    param(
        [Parameter(Mandatory = $true)][string]$Message
    )

    if ([string]::IsNullOrWhiteSpace($LogPath)) {
        return
    }
    $timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fff")
    $line = "$timestamp | $Message"
    try {
        Add-Content -LiteralPath $LogPath -Value $line -Encoding UTF8
    }
    catch {
    }
}

function Get-MarkerOccurrences {
    param(
        [Parameter(Mandatory = $true)]$Document,
        [Parameter(Mandatory = $true)][string]$Marker
    )

    $count = 0
    $searchRange = $Document.Content
    while ($true) {
        $find = $searchRange.Find
        $find.ClearFormatting()
        $found = $find.Execute($Marker, $false, $false, $false, $false, $false, $true, $wdFindStop)
        if (-not $found) {
            break
        }
        $count += 1
        $searchRange.Start = $searchRange.End
        $searchRange.End = $Document.Content.End
    }
    return $count
}

function Find-MarkerRange {
    param(
        [Parameter(Mandatory = $true)]$Document,
        [Parameter(Mandatory = $true)][string]$Marker
    )

    $range = $Document.Content
    $find = $range.Find
    $find.ClearFormatting()
    $found = $find.Execute($Marker, $false, $false, $false, $false, $false, $true, $wdFindStop)
    if ($found) {
        return $range
    }
    return $null
}

function Resolve-FullPath {
    param([string]$PathValue)
    return [System.IO.Path]::GetFullPath($PathValue)
}

function Normalize-ChartEntries {
    param(
        [Parameter(Mandatory = $true)]$ManifestObject,
        [Parameter(Mandatory = $true)][hashtable]$WorkbookPaths,
        [Parameter(Mandatory = $false)][string]$LegacyWorkbookPath
    )

    $normalized = New-Object System.Collections.Generic.List[object]
    $markers = @{}

    $manifestCharts = $ManifestObject.charts
    if ($manifestCharts -is [System.Array]) {
        foreach ($entry in $manifestCharts) {
            $marker = [string]$entry.marker
            $sheetName = [string]$entry.sheet_name
            $workbookKey = [string]$entry.workbook_key
            $chartIndexRaw = $entry.chart_index
            $imageName = [string]$entry.image_filename

            if ([string]::IsNullOrWhiteSpace($marker)) {
                throw "Entrée manifeste invalide : marker absent."
            }
            if ([string]::IsNullOrWhiteSpace($sheetName)) {
                throw "Entrée manifeste invalide ($marker) : sheet_name absent."
            }
            if ([string]::IsNullOrWhiteSpace($workbookKey)) {
                throw "Entrée manifeste invalide ($marker) : workbook_key absent."
            }
            if (-not $WorkbookPaths.ContainsKey($workbookKey)) {
                throw "Entrée manifeste invalide ($marker) : workbook_key '$workbookKey' non défini dans workbooks."
            }
            if ($markers.ContainsKey($marker)) {
                throw "Manifeste invalide : marqueur dupliqué '$marker'."
            }
            $markers[$marker] = $true

            try {
                $chartIndex = [int]$chartIndexRaw
            }
            catch {
                throw "Entrée manifeste invalide ($marker) : chart_index non entier."
            }
            if ($chartIndex -lt 1) {
                throw "Entrée manifeste invalide ($marker) : chart_index doit être >= 1."
            }

            $normalized.Add([PSCustomObject]@{
                    marker        = $marker
                    workbook_key  = $workbookKey
                    sheet_name    = $sheetName
                    chart_index   = $chartIndex
                    image_filename = $imageName
                })
        }
        return $normalized
    }

    # Rétrocompatibilité (ancien manifeste annexe B : objet {charts:{png:{sheet_name}}})
    if ($manifestCharts -eq $null -or $manifestCharts.PSObject.Properties.Count -eq 0) {
        return $normalized
    }
    if ([string]::IsNullOrWhiteSpace($LegacyWorkbookPath)) {
        throw "Ancien format de manifeste détecté mais WorkbookPath n'est pas fourni."
    }

    if (-not $WorkbookPaths.ContainsKey("legacy")) {
        $WorkbookPaths["legacy"] = Resolve-FullPath $LegacyWorkbookPath
    }

    foreach ($property in $manifestCharts.PSObject.Properties) {
        $chartMeta = $property.Value
        $sheetName = [string]$chartMeta.sheet_name
        if ([string]::IsNullOrWhiteSpace($sheetName)) {
            continue
        }
        $marker = "[[ANNEXE_B_CHART:$sheetName]]"
        if ($markers.ContainsKey($marker)) {
            throw "Manifeste legacy invalide : marqueur dupliqué '$marker'."
        }
        $markers[$marker] = $true

        $normalized.Add([PSCustomObject]@{
                marker        = $marker
                workbook_key  = "legacy"
                sheet_name    = $sheetName
                chart_index   = 1
                image_filename = [string]$property.Name
            })
    }

    return $normalized
}

function Find-PastedInlineShape {
    param(
        [Parameter(Mandatory = $true)]$Document,
        [Parameter(Mandatory = $true)][int]$InsertionStart
    )

    for ($i = $Document.InlineShapes.Count; $i -ge 1; $i--) {
        $candidate = $Document.InlineShapes.Item($i)
        try {
            if ([Math]::Abs([int]$candidate.Range.Start - $InsertionStart) -le 2) {
                return $candidate
            }
        }
        catch {
        }
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($candidate)
    }

    for ($i = $Document.Shapes.Count; $i -ge 1; $i--) {
        $shape = $Document.Shapes.Item($i)
        try {
            if ([Math]::Abs([int]$shape.Anchor.Start - $InsertionStart) -le 2) {
                $inline = $shape.ConvertToInlineShape()
                [void][Runtime.InteropServices.Marshal]::ReleaseComObject($shape)
                return $inline
            }
        }
        catch {
        }
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($shape)
    }

    return $null
}

function Wait-PastedInlineShape {
    param(
        [Parameter(Mandatory = $true)]$Document,
        [Parameter(Mandatory = $true)][int]$InlineCountBefore,
        [Parameter(Mandatory = $true)][int]$ShapeCountBefore,
        [Parameter(Mandatory = $true)][int]$TimeoutMs
    )

    $deadline = [DateTime]::UtcNow.AddMilliseconds($TimeoutMs)
    while ([DateTime]::UtcNow -lt $deadline) {
        if ([int]$Document.InlineShapes.Count -gt $InlineCountBefore) {
            return $Document.InlineShapes.Item($Document.InlineShapes.Count)
        }
        if ([int]$Document.Shapes.Count -gt $ShapeCountBefore) {
            $shape = $Document.Shapes.Item($Document.Shapes.Count)
            try {
                return $shape.ConvertToInlineShape()
            }
            finally {
                [void][Runtime.InteropServices.Marshal]::ReleaseComObject($shape)
            }
        }
        Start-Sleep -Milliseconds $pasteRetryDelayMs
    }
    return $null
}

function Invoke-PasteSpecialWithRetry {
    param(
        [Parameter(Mandatory = $true)]$Range,
        [Parameter(Mandatory = $true)][string]$PasteMode,
        [Parameter(Mandatory = $true)][int]$MaxAttempts,
        [Parameter(Mandatory = $true)][int]$DelayMs
    )

    $lastError = ""
    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        try {
            if ($PasteMode -eq "linked") {
                $Range.PasteSpecial($null, $true, $wdInLine, $false, $wdPasteOLEObject)
            }
            else {
                $Range.PasteSpecial($null, $false, $wdInLine, $false, $wdPasteOLEObject)
            }
            return
        }
        catch {
            $lastError = $_.Exception.Message
            if ($attempt -lt $MaxAttempts) {
                Start-Sleep -Milliseconds $DelayMs
            }
        }
    }

    throw "PasteSpecial a échoué après $MaxAttempts tentative(s) : $lastError"
}

$excel = $null
$word = $null
$document = $null
$workbooks = @{}
$tempDocxPath = $null
$swapped = $false
$inserted = 0

try {
    $DocxPath = Resolve-FullPath $DocxPath
    $ManifestPath = Resolve-FullPath $ManifestPath
    if (-not [string]::IsNullOrWhiteSpace($LogPath)) {
        $LogPath = Resolve-FullPath $LogPath
        $logDir = [System.IO.Path]::GetDirectoryName($LogPath)
        if (-not [string]::IsNullOrWhiteSpace($logDir)) {
            [System.IO.Directory]::CreateDirectory($logDir) | Out-Null
        }
        if (Test-Path -LiteralPath $LogPath -PathType Leaf) {
            Remove-Item -LiteralPath $LogPath -Force
        }
        Write-StepLog "START helper pid=$PID mode=$PasteMode expected=$ExpectedCount docx=$DocxPath manifest=$ManifestPath"
    }
    if (-not (Test-Path -LiteralPath $DocxPath -PathType Leaf)) {
        throw "Document Word introuvable : $DocxPath"
    }
    if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
        throw "Manifeste des graphiques introuvable : $ManifestPath"
    }

    $manifest = Get-Content -LiteralPath $ManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $workbookPaths = @{}
    if ($manifest.workbooks -ne $null) {
        foreach ($wb in $manifest.workbooks.PSObject.Properties) {
            $workbookPaths[[string]$wb.Name] = Resolve-FullPath ([string]$wb.Value)
        }
    }

    $normalizedEntries = @(Normalize-ChartEntries -ManifestObject $manifest -WorkbookPaths $workbookPaths -LegacyWorkbookPath $WorkbookPath)
    Write-StepLog "Manifest entries normalized count=$($normalizedEntries.Count)"
    if ($normalizedEntries.Count -eq 0) {
        Write-StepLog "No markers to process"
        Write-Output "[EXCEL-CHARTS] Aucun marqueur à traiter."
        return
    }

    if ($ExpectedCount -gt 0 -and $normalizedEntries.Count -ne $ExpectedCount) {
        throw "Préflight invalide : manifeste contient $($normalizedEntries.Count) entrée(s), $ExpectedCount attendu(s)."
    }

    foreach ($pair in $workbookPaths.GetEnumerator()) {
        if (-not (Test-Path -LiteralPath $pair.Value -PathType Leaf)) {
            throw "Classeur Excel introuvable (clé=$($pair.Key)) : $($pair.Value)"
        }
        Write-StepLog "Workbook path ok key=$($pair.Key) path=$($pair.Value)"
    }

    $docDirectory = [System.IO.Path]::GetDirectoryName($DocxPath)
    $docBaseName = [System.IO.Path]::GetFileNameWithoutExtension($DocxPath)
    $docExt = [System.IO.Path]::GetExtension($DocxPath)
    do {
        $runId = [Guid]::NewGuid().ToString("N")
        $tempName = "{0}.__excel_tmp_{1}_{2}{3}" -f $docBaseName, $PID, $runId, $docExt
        $tempDocxPath = Join-Path $docDirectory $tempName
    } while (Test-Path -LiteralPath $tempDocxPath -PathType Leaf)
    Copy-Item -LiteralPath $DocxPath -Destination $tempDocxPath -Force
    Write-StepLog "Temp docx created path=$tempDocxPath"

    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    Write-StepLog "Excel COM started"
    foreach ($workbookKey in ($workbookPaths.Keys | Sort-Object)) {
        $workbookPath = $workbookPaths[$workbookKey]
        $workbooks[$workbookKey] = $excel.Workbooks.Open($workbookPath, 0, $true)
        Write-StepLog "Workbook opened key=$workbookKey"
    }

    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Open($tempDocxPath, $false, $false)
    Write-StepLog "Word COM opened temp document"

    # Préflight complet : feuilles, indices, marqueurs.
    foreach ($entry in $normalizedEntries) {
        $workbook = $workbooks[$entry.workbook_key]
        $worksheet = $null
        try {
            $worksheet = $workbook.Worksheets.Item($entry.sheet_name)
            $chartCount = [int]$worksheet.ChartObjects().Count
            if ($entry.chart_index -gt $chartCount) {
                throw "index $($entry.chart_index) hors plage ($chartCount graphique(s))"
            }
            Write-StepLog "Preflight Excel ok marker=$($entry.marker) sheet=$($entry.sheet_name) chartIndex=$($entry.chart_index) chartCount=$chartCount"
        }
        catch {
            throw "Préflight Excel échoué (feuille '$($entry.sheet_name)', image '$($entry.image_filename)') : $($_.Exception.Message)"
        }
        finally {
            if ($worksheet -ne $null) {
                [void][Runtime.InteropServices.Marshal]::ReleaseComObject($worksheet)
            }
        }
    }

    foreach ($entry in $normalizedEntries) {
        $occurrences = Get-MarkerOccurrences -Document $document -Marker $entry.marker
        if ($occurrences -ne 1) {
            throw "Préflight Word échoué : marqueur '$($entry.marker)' trouvé $occurrences fois (attendu : 1)."
        }
        Write-StepLog "Preflight Word marker ok marker=$($entry.marker)"
    }

    # Collage OLE après préflight validé.
    foreach ($entry in $normalizedEntries) {
        $worksheet = $null
        $chartObject = $null
        $range = $null
        $inlineShape = $null

        try {
            $workbook = $workbooks[$entry.workbook_key]
            $workbookPath = [string]$workbookPaths[$entry.workbook_key]
            $expectedWorkbookBase = [System.IO.Path]::GetFileName($workbookPath).ToLowerInvariant()
            Write-StepLog "Insert begin marker=$($entry.marker) sheet=$($entry.sheet_name) chart=$($entry.chart_index)"

            $range = Find-MarkerRange -Document $document -Marker $entry.marker
            if ($range -eq $null) {
                throw "marqueur introuvable au moment du collage"
            }

            $worksheet = $workbook.Worksheets.Item($entry.sheet_name)
            $chartObject = $worksheet.ChartObjects($entry.chart_index)
            $worksheet.Activate()
            $chartObject.Activate()
            $chartObject.Copy()
            Write-StepLog "Copy ok marker=$($entry.marker)"
            $isInTable = [bool]$range.Information($wdWithInTable)
            $insertionStart = [int]$range.Start
            $range.Text = ""
            $range.Collapse($wdCollapseStart)
            $inlineCountBefore = [int]$document.InlineShapes.Count
            $shapeCountBefore = [int]$document.Shapes.Count

            Invoke-PasteSpecialWithRetry -Range $range -PasteMode $PasteMode -MaxAttempts $pasteMaxAttempts -DelayMs $pasteRetryDelayMs
            Write-StepLog "PasteSpecial ok marker=$($entry.marker)"
            $inlineShape = Wait-PastedInlineShape -Document $document -InlineCountBefore $inlineCountBefore -ShapeCountBefore $shapeCountBefore -TimeoutMs $shapeWaitTimeoutMs
            if ($inlineShape -eq $null) {
                $inlineShape = Find-PastedInlineShape -Document $document -InsertionStart $insertionStart
            }
            if ($inlineShape -eq $null) {
                throw "objet collé introuvable"
            }
            Write-StepLog "Shape detected marker=$($entry.marker)"

            $inlineShape.LockAspectRatio = $msoTrue
            if ($isInTable) {
                $inlineShape.Width = 225
            }
            else {
                $inlineShape.Width = 440
            }

            $sourceName = ""
            try { $sourceName = [string]$inlineShape.LinkFormat.SourceName } catch {}
            $sourceLower = $sourceName.ToLowerInvariant()
            if ($PasteMode -eq "linked") {
                if ([string]::IsNullOrWhiteSpace($sourceName) -or $sourceLower -eq "null") {
                    throw "objet lié attendu, mais LinkFormat.SourceName est vide"
                }
                if (-not $sourceLower.Contains($expectedWorkbookBase)) {
                    throw "lien inattendu '$sourceName' (classeur attendu : $expectedWorkbookBase)"
                }
                try { $inlineShape.LinkFormat.AutoUpdate = $true } catch {}
            }
            else {
                if (-not [string]::IsNullOrWhiteSpace($sourceName) -and $sourceLower -ne "null") {
                    throw "objet incorporé attendu, mais un lien externe subsiste : $sourceName"
                }
            }
            Write-StepLog "Shape validation ok marker=$($entry.marker)"

            $inserted += 1
            if (($inserted % 10) -eq 0 -or $inserted -eq $normalizedEntries.Count) {
                Write-Output "[EXCEL-CHARTS] Progression : $inserted/$($normalizedEntries.Count)"
            }
        }
        catch {
            throw "Insertion échouée pour '$($entry.marker)' (sheet=$($entry.sheet_name), chart_index=$($entry.chart_index)) : $($_.Exception.Message)"
        }
        finally {
            if ($excel -ne $null) {
                try { $excel.CutCopyMode = 0 } catch {}
            }
            if ($inlineShape -ne $null) {
                [void][Runtime.InteropServices.Marshal]::ReleaseComObject($inlineShape)
            }
            if ($range -ne $null) {
                [void][Runtime.InteropServices.Marshal]::ReleaseComObject($range)
            }
            if ($chartObject -ne $null) {
                [void][Runtime.InteropServices.Marshal]::ReleaseComObject($chartObject)
            }
            if ($worksheet -ne $null) {
                [void][Runtime.InteropServices.Marshal]::ReleaseComObject($worksheet)
            }
        }
    }

    if ($ExpectedCount -gt 0 -and $inserted -ne $ExpectedCount) {
        throw "Nombre d'objets insérés inattendu : $inserted inséré(s), $ExpectedCount attendu(s)."
    }
    if ($inserted -ne $normalizedEntries.Count) {
        throw "Nombre d'objets insérés inattendu : $inserted inséré(s), $($normalizedEntries.Count) entrée(s) manifeste."
    }

    foreach ($entry in $normalizedEntries) {
        $remaining = Get-MarkerOccurrences -Document $document -Marker $entry.marker
        if ($remaining -ne 0) {
            throw "Marqueur restant après collage : '$($entry.marker)' ($remaining occurrence(s))."
        }
        Write-StepLog "Post-check marker removed marker=$($entry.marker)"
    }

    if ($PasteMode -eq "embedded") {
        for ($i = 1; $i -le $document.InlineShapes.Count; $i++) {
            $shape = $document.InlineShapes.Item($i)
            try {
                $sourceName = ""
                try { $sourceName = [string]$shape.LinkFormat.SourceName } catch {}
                if (-not [string]::IsNullOrWhiteSpace($sourceName) -and $sourceName.ToLowerInvariant().Contains(".xlsx")) {
                    throw "Lien XLSX résiduel détecté en mode embedded : $sourceName"
                }
            }
            finally {
                [void][Runtime.InteropServices.Marshal]::ReleaseComObject($shape)
            }
        }
    }

    $document.Save()
    Write-StepLog "Document save ok"
    $document.Close($false)
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($document)
    $document = $null

    Move-Item -LiteralPath $tempDocxPath -Destination $DocxPath -Force
    $swapped = $true
    Write-StepLog "Swap temp->final ok final=$DocxPath inserted=$inserted"

    if ($PasteMode -eq "linked") {
        Write-Output "[EXCEL-CHARTS] $inserted objet(s) Excel liés insérés (annexes B/C)."
    }
    else {
        Write-Output "[EXCEL-CHARTS] $inserted objet(s) Excel incorporés insérés (annexes B/C)."
    }
}
finally {
    Write-StepLog "Cleanup start"
    if ($excel -ne $null) {
        try { $excel.CutCopyMode = 0 } catch {}
    }
    if ($document -ne $null) {
        try { $document.Close($false) } catch {}
        try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($document) } catch {}
    }

    if ($word -ne $null) {
        try { $word.Quit() } catch {}
        try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word) } catch {}
    }

    foreach ($workbookKey in @($workbooks.Keys)) {
        $wb = $workbooks[$workbookKey]
        if ($wb -ne $null) {
            try { $wb.Close($false) } catch {}
            try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($wb) } catch {}
        }
    }

    if ($excel -ne $null) {
        try { $excel.Quit() } catch {}
        try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel) } catch {}
    }

    if (-not $swapped -and $tempDocxPath -and (Test-Path -LiteralPath $tempDocxPath -PathType Leaf)) {
        try { Remove-Item -LiteralPath $tempDocxPath -Force } catch {}
    }

    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
    Write-StepLog "Cleanup end"
}
