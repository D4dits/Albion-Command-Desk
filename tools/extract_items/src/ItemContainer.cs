namespace StatisticAnalysisTool.Extractor;

internal class ItemContainer : IdContainer
{
    public string LocalizationNameVariable { get; set; } = string.Empty;
    public string LocalizationDescriptionVariable { get; set; } = string.Empty;
    public Dictionary<string, string> LocalizedNames { get; set; } = new();
    public Dictionary<string, string> LocalizedDescriptions { get; set; } = new();
}
