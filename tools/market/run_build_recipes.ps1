param(
    [string[]] $Input = @(),
    [string[]] $InputGlob = @("tools/market/sources/**/*.json"),
    [string] $Output = "albion_dps/market/data/recipes.json",
    [string] $Report = "artifacts/market/recipes_build_report.json",
    [switch] $Strict,
    [int] $MinRecipes = 1
)

$args = @("tools/market/build_recipes.py")
foreach ($item in $Input) {
    $args += @("--input", $item)
}
foreach ($pattern in $InputGlob) {
    $args += @("--input-glob", $pattern)
}
$args += @("--output", $Output, "--report", $Report, "--min-recipes", "$MinRecipes")
if ($Strict) {
    $args += "--strict"
}

python @args

