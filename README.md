# Grazi 🐾

Assistente para a área de trabalho do Windows, inspirada na cachorrinha Grazi: caramelo robotizada, coleira rosa e orelhas relaxadas.

<img src="assets/grazi.png" alt="Grazi, cachorrinha caramelo robótica" width="240">

**Protótipo 0.6 — balão de conversa, expressões e voz feminina online opcional.**

## Começar ou atualizar

1. Feche a versão anterior. Baixe **Code → Download ZIP** e extraia tudo em uma pasta nova.
2. Instale Python **3.12 de 64 bits**, com Python Launcher.
3. Instale e abra [Ollama](https://ollama.com/download/windows). No Terminal: `ollama pull qwen3:1.7b`.
4. Execute `INICIAR.bat`. Ele prepara `.venv-py312` e instala as dependências; essa etapa requer internet.
5. Converse pelo pequeno balão junto à Grazi. O botão direito abre **Conversa completa**, **Personalizar**, **Ditado** e outras opções.

Histórico e preferências existentes são preservados em `%LOCALAPPDATA%\Grazi`. Para atualizar, não copie apenas `grazi.py`: os módulos `balloon.py`, `speech.py` e os assets também são necessários.

## Novidades

- Após mais de 60 segundos sem interação com a Grazi, ela se deita com um macaquinho de pelúcia e respira suavemente. Clicar, arrastar ou digitar acorda a personagem. O tempo não conta enquanto ela processa, ouve ou prepara/reproduz fala. O balão se recolhe durante o repouso.

- A janela grande deixa de abrir automaticamente. O balão acompanha o mascote ao arrastar e muda de lado perto da borda.
- Respostas longas são divididas em páginas. Durante a leitura, cada trecho aparece no balão; as setas permitem reler e interrompem a voz.
- Duplo clique reabre o balão; botão direito → **Abrir conversa completa** exibe o histórico.
- Piscadas periódicas, boca alternada durante a reprodução e pose de atenção ao ouvir. São quadros 2D, sem sincronização por fonemas. Desative **Movimento suave** para manter a pose estática.
- Voz feminina brasileira **Francisca**, via [edge-tts](https://github.com/rany2/edge-tts), selecionável em **Personalizar**. Marque **Ler respostas em voz alta**, escolha Francisca e use **Ouvir amostra**.

**A voz online envia o texto falado ao serviço da Microsoft e precisa de internet.** Ela é opcional; a voz instalada no Windows continua sendo o padrão. O serviço pode falhar ou mudar. A síntese ocorre por trechos, podendo haver uma pequena pausa entre eles. Não há clonagem de voz nem promessa de idade percebida.

## Recursos existentes

Chat com Ollama, escolha de modelos locais, memória editável, histórico local, tamanho ajustável, bandeja e ditado Windows mediante reconhecedor pt-BR instalado. Não há escuta contínua.

Comandos explícitos: `que horas são`, `que dia é hoje`, `calcule 12 * 8`, `abrir calculadora`, `abrir bloco de notas`, `status do computador` e `abrir github`. O texto gerado pelo modelo nunca é executado como comando de sistema.

O perfil inicial usa Qwen3 1.7B, contexto de 2.048 tokens e respostas de até 400 tokens. O desempenho deve ser medido no notebook de 8 GB; não foi presumida aceleração pela GPU Intel.

## Pesquisa de voz

| Projeto | Opção pt-BR | Decisão nesta versão |
|---|---|---|
| [edge-tts](https://github.com/rany2/edge-tts) | Francisca, feminina, serviço online | Integrado como opção; sem baixar outro modelo local |
| [Kokoro](https://github.com/hexgrad/kokoro) | `pf_dora`, feminina brasileira | Alternativa local para avaliação futura; não instalada |

A [lista oficial do Kokoro](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md) documenta Dora. A [Microsoft](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts) também lista Leticia como voz infantil no Azure; isso não garante sua disponibilidade no serviço Edge e ela não foi integrada.

## Verificação e limites

16 testes passaram: núcleo/Ollama simulado e interface Qt offscreen, incluindo abertura compacta, envio, paginação, bordas de tela e cancelamento de áudio atrasado. Assets carregados pelo Qt e quadros inspecionados visualmente.

A tentativa de consultar vozes online neste ambiente falhou na validação TLS; **áudio real e execução nativa no Windows ainda precisam de teste no computador final**. Não foram desativadas verificações de certificado. Há tratamento de falhas com orientação no balão e preservação da resposta na conversa completa.

Não inclui instalador `.exe`, leitura de tela, agenda, navegação geral, execução automática no login ou rig Live2D. Dependências e modelos mantêm suas licenças.

- [Guia e privacidade](LEIA-ME.md)
- [Registro de verificação](VERIFICACAO.txt)
- Testes: `python -m unittest discover -s tests -v`

| Arquivo | Função |
|---|---|
| `grazi.py` | Interface, mascote e integração |
| `balloon.py` | Balão ancorado e páginas de resposta |
| `speech.py` | Voz Windows/Edge, reprodução e cancelamento |
| `core.py` | Estado local, comandos explícitos e Ollama |
| `assets/grazi-expressions.png` | Atlas de quatro expressões |
| `idle.py` | Temporizador de inatividade da Grazi |
| `assets/grazi-sleep.png` | Repouso com macaquinho de pelúcia |
| `assets/grazi.png` | Imagem alternativa e ícone |
| `dictation.ps1` | Reconhecimento de fala Windows |
| `INICIAR.bat` | Preparação Python 3.12 e inicialização |
