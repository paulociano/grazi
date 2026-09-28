$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding
Add-Type -AssemblyName System.Speech
$info = [System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers() | Where-Object { $_.Culture.Name -eq 'pt-BR' } | Select-Object -First 1
if ($null -eq $info) { exit 2 }
$recognizer = New-Object System.Speech.Recognition.SpeechRecognitionEngine($info)
try {
    $builder = New-Object System.Speech.Recognition.GrammarBuilder
    $builder.Culture = $info.Culture
    $builder.Append('Grazi')
    $grammar = New-Object System.Speech.Recognition.Grammar($builder)
    $recognizer.LoadGrammar($grammar)
    $recognizer.SetInputToDefaultAudioDevice()
    while ($true) {
        $result = $recognizer.Recognize([TimeSpan]::FromSeconds(1))
        if ($null -ne $result -and $result.Confidence -ge 0.65) {
            [Console]::WriteLine('WAKE')
            break
        }
    }
} finally { $recognizer.Dispose() }
