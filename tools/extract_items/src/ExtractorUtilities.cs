using StatisticAnalysisTool.Extractor.Enums;
using System.Text;
using System.Text.Json;

namespace StatisticAnalysisTool.Extractor;

internal static class ExtractorUtilities
{
    private static readonly JsonWriterOptions JsonWriterOptions = new ()
    {
        Indented = true,
        Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
    };
    
    public static void WriteItem(Stream stream, IdContainer idContainer, bool first = false)
    {
        if (!first)
        {
            stream.WriteByte((byte) ',');
            stream.WriteByte((byte) '\n');
        }

        using var writer = new Utf8JsonWriter(stream, JsonWriterOptions);
        if (idContainer is ItemContainer itemContainer)
        {
            JsonSerializer.Serialize(writer, itemContainer);
        }
        else
        {
            JsonSerializer.Serialize(writer, idContainer);
        }
    }

    public static void WriteString(Stream stream, string val)
    {
        var buffer = Encoding.UTF8.GetBytes(val);
        stream.Write(buffer, 0, buffer.Length);
    }

    public static string GetBinFilePath(string mainGameFolder)
    {
        return Path.Combine(mainGameFolder, "Albion-Online_Data", "StreamingAssets", "GameData");
    }

    public static string GetServerFolderName(ServerType serverType)
    {
        return serverType switch
        {
            ServerType.Staging => "staging",
            ServerType.Playground => "playground",
            _ => "game"
        };
    }

    public static string ResolveMainGameFolder(string gameRoot, ServerType serverType)
    {
        if (string.IsNullOrWhiteSpace(gameRoot))
        {
            return gameRoot;
        }

        var trimmed = gameRoot.Trim().Trim('\'', '"');
        if (LooksLikeGameFolder(trimmed))
        {
            return trimmed;
        }

        var serverFolder = GetServerFolderName(serverType);
        var candidates = new[]
        {
            Path.Combine(trimmed, serverFolder),
            Path.Combine(trimmed, $"{serverFolder}_x64"),
            Path.Combine(trimmed, $"{serverFolder}-x64"),
        };

        foreach (var candidate in candidates)
        {
            if (LooksLikeGameFolder(candidate))
            {
                return candidate;
            }
        }

        return Path.Combine(trimmed, serverFolder);
    }

    private static bool LooksLikeGameFolder(string mainGameFolder)
    {
        if (string.IsNullOrWhiteSpace(mainGameFolder))
        {
            return false;
        }

        var binPath = GetBinFilePath(mainGameFolder);
        if (!Directory.Exists(binPath))
        {
            return false;
        }

        return File.Exists(Path.Combine(binPath, "items.bin"))
               && File.Exists(Path.Combine(binPath, "localization.bin"));
    }
}
