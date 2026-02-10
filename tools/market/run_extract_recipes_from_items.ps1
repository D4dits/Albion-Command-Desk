param(
    [string] $ItemsJson = "data/items.json",
    [string] $IndexedItems = "data/indexedItems.json",
    [string] $Output = "tools/market/sources/recipes_from_items.json",
    [string] $Report = "artifacts/market/recipes_from_items_report.json",
    [switch] $ExcludeLocked
)

$args = @(
    "tools/market/extract_recipes_from_items.py",
    "--items-json", $ItemsJson,
    "--output", $Output,
    "--report", $Report
)
if (Test-Path -LiteralPath $IndexedItems) {
    $args += @("--indexed-items", $IndexedItems)
}
if ($ExcludeLocked) {
    $args += "--exclude-locked"
}

python @args
