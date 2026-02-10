param(
    [string] $ItemsJson = "data/items.json",
    [string] $IndexedItems = "data/indexedItems.json",
    [string] $SourceOut = "tools/market/sources/recipes_from_items.json",
    [string] $SourceReport = "artifacts/market/recipes_from_items_report.json",
    [string] $Output = "albion_dps/market/data/recipes.json",
    [string] $Report = "artifacts/market/recipes_build_report.json",
    [switch] $Strict,
    [switch] $ExcludeLocked,
    [int] $MinRecipes = 100
)

.\tools\market\run_extract_recipes_from_items.ps1 `
    -ItemsJson $ItemsJson `
    -IndexedItems $IndexedItems `
    -Output $SourceOut `
    -Report $SourceReport `
    -ExcludeLocked:$ExcludeLocked

.\tools\market\run_build_recipes.ps1 `
    -Input $SourceOut `
    -InputGlob @() `
    -Output $Output `
    -Report $Report `
    -Strict:$Strict `
    -MinRecipes $MinRecipes
