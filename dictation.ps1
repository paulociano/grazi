$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding
Add-Type -AssemblyName System.Speech
$recognizerInfo = [System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers() | Where-Object { $_.Culture.Name -eq 'pt-BR' } | Select-Object -First 1
if ($null -eq $recognizerInfo) { exit 2 }
$recognizer = New-Object System.Speech.Recognition.SpeechRecognitionEngine($recognizerInfo)
try {
    $recognizer.LoadGrammar((New-Object System.Speech.Recognition.DictationGrammar))
    $recognizer.SetInputToDefaultAudioDevice()
    $result = $recognizer.Recognize([TimeSpan]::FromSeconds(10))
    if ($null -ne $result) { [Console]::WriteLine($result.Text) } else { exit 3 }
} finally { $recognizer.Dispose() }
