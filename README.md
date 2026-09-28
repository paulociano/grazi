# Grazi 🐾

Assistente para a área de trabalho do Windows, inspirada na cachorrinha Grazi: caramelo robotizada, coleira rosa e orelhas relaxadas.

<img src="assets/grazi.png" alt="Grazi, cachorrinha caramelo robótica" width="240">

### Pose de descanso

Após o período de inatividade configurado, a Grazi se deita com seu macaquinho de pelúcia e respira suavemente.

<img src="assets/grazi-sleep.png" alt="Grazi deitada ao lado de um macaquinho de pelúcia" width="520">

**Versão 0.8 — balão compacto, ativação por voz e assistência local com arquivos.**

> A Grazi é um protótipo pessoal em evolução. Os comandos de arquivo são explícitos, limitados a uma pasta escolhida e sempre pedem confirmação para operações destrutivas.

Leia [Sobre a Grazi](ABOUT.md) para conhecer o propósito, a arquitetura e as decisões de privacidade do projeto.

## Começar ou atualizar

1. Feche a versão anterior. Baixe **Code → Download ZIP** e extraia tudo em uma pasta nova.
2. Instale Python **3.12 de 64 bits**, com Python Launcher.
3. Instale e abra [Ollama](https://ollama.com/download/windows). No Terminal: `ollama pull qwen3:1.7b`.
4. Execute `INICIAR.bat`. Ele prepara `.venv-py312` e instala as dependências; essa etapa requer internet.
5. Converse pelo pequeno balão junto à Grazi. O botão direito abre **Conversa completa**, **Personalizar**, **Ditado**, **Comandos disponíveis** e outras opções.

## Instalador `.exe`

O repositório inclui uma receita de instalador Windows. Para gerar localmente, instale o [Inno Setup 6](https://jrsoftware.org/isinfo.php) e execute `BUILD_INSTALLER.bat` em um Windows com Python 3.12. O instalador será criado em `installer-output\Grazi-Setup-v0.9.0.exe`.

Também é possível abrir **Actions → Windows installer → Run workflow** no GitHub. O artefato `Grazi-Windows-installer` será gerado em um runner Windows, sem incluir o Python separado: o aplicativo empacotado já leva o runtime e as dependências.

Histórico e preferências existentes são preservados em `%LOCALAPPDATA%\Grazi`. Para atualizar, não copie apenas `grazi.py`: os módulos `balloon.py`, `speech.py` e os assets também são necessários.

## Novidades

- Interface menor: Grazi inicia em 170 px e o balão em 270 px; o tamanho da personagem pode ser ajustado em Personalizar.
- Ativação por voz ao ouvir “Grazi”, usando o reconhecedor local pt-BR do Windows. Ela inicia automaticamente por padrão, inclusive ao atualizar uma instalação antiga, pausa enquanto a Grazi fala e tenta novamente se houver uma falha temporária. Pode ser desligada em Personalizar.
- Pasta de trabalho escolhida em Personalizar. Comandos explícitos para listar, abrir e ler arquivos, salvar texto/respostas, enviar arquivos à Lixeira, abrir Calculadora/Bloco de Notas e solicitar o fechamento de instâncias abertas pela Grazi.
- Arquivos são restritos à pasta escolhida; executáveis não são abertos. Sobrescrita e exclusão exigem confirmação. Fechamento usa WM_CLOSE e preserva pedidos de salvamento do aplicativo.

- **Personalizar → Repouso:** ative/desative e ajuste de 1 a 30 minutos; padrão de 1 minuto preservado.
- **Botão direito → Descansar agora / Acordar:** controle manual da pose. Descansar aguarda o fim de uma resposta ou ditado em andamento.
- **Ouvir**, no balão ou menu: repete a última resposta usando a voz selecionada, mesmo com leitura automática desligada. Não chama o Ollama nem duplica o histórico. Se Francisca estiver selecionada, o texto é enviado novamente ao serviço online.

- Por padrão, após mais de 60 segundos sem interação com a Grazi, ela se deita com um macaquinho de pelúcia e respira suavemente. Clicar, arrastar ou digitar acorda a personagem. O tempo não conta enquanto ela processa, ouve ou prepara/reproduz fala. O balão se recolhe durante o repouso.

- A janela grande deixa de abrir automaticamente. O balão acompanha o mascote ao arrastar e muda de lado perto da borda.
- Respostas longas são divididas em páginas. Durante a leitura, cada trecho aparece no balão; as setas permitem reler e interrompem a voz.
- Duplo clique reabre o balão; botão direito → **Abrir conversa completa** exibe o histórico.
- Piscadas periódicas, boca alternada durante a reprodução e pose de atenção ao ouvir. São quadros 2D, sem sincronização por fonemas. Desative **Movimento suave** para manter a pose estática.
- Voz feminina brasileira **Francisca**, via [edge-tts](https://github.com/rany2/edge-tts), selecionável em **Personalizar**. Marque **Ler respostas em voz alta**, escolha Francisca e use **Ouvir amostra**.

**A voz online envia o texto falado ao serviço da Microsoft e precisa de internet.** Ela é opcional; a voz instalada no Windows continua sendo o padrão. O serviço pode falhar ou mudar. A síntese ocorre por trechos, podendo haver uma pequena pausa entre eles. Não há clonagem de voz nem promessa de idade percebida.

## Comandos de assistência

Depois de escolher a **Pasta de trabalho** em Personalizar, a Grazi entende comandos explícitos como:

`listar arquivos` · `abrir pasta` · `abrir arquivo contrato.pdf` · `ler arquivo notas.txt` · `salvar arquivo notas.txt | conteúdo` · `salvar resposta em resposta.txt` · `excluir arquivo notas.txt` · `abrir (ou abra) calculadora` · `fechar (ou feche) calculadora`.

O comando de fechar apenas solicita o fechamento de instâncias abertas pela Grazi; ele não força o encerramento de processos nem interfere em aplicativos que você abriu separadamente.

## Recursos existentes

Chat com Ollama, escolha de modelos locais, memória editável, histórico local, tamanho ajustável, bandeja e ditado Windows mediante reconhecedor pt-BR instalado. Não há escuta contínua.

Comandos locais adicionais: `que horas são`, `que dia é hoje`, `calcule 12 * 8`, `status do computador` e `abrir github`. O texto gerado pelo modelo nunca é executado como comando de sistema.

O perfil inicial usa Qwen3 1.7B, contexto de 2.048 tokens e respostas de até 400 tokens. O desempenho deve ser medido no notebook de 8 GB; não foi presumida aceleração pela GPU Intel.

## Pesquisa de voz

| Projeto | Opção pt-BR | Decisão nesta versão |
|---|---|---|
| [edge-tts](https://github.com/rany2/edge-tts) | Francisca, feminina, serviço online | Integrado como opção; sem baixar outro modelo local |
| [Kokoro](https://github.com/hexgrad/kokoro) | `pf_dora`, feminina brasileira | Alternativa local para avaliação futura; não instalada |

A [lista oficial do Kokoro](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md) documenta Dora. A [Microsoft](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts) também lista Leticia como voz infantil no Azure; isso não garante sua disponibilidade no serviço Edge e ela não foi integrada.

## Verificação e limites

Os testes cobrem núcleo/Ollama simulado, assistência de arquivos, persistência, escopo da pasta, confirmações e interface Qt offscreen, incluindo abertura compacta, envio, paginação, bordas de tela e cancelamento de áudio atrasado. Assets foram carregados pelo Qt e quadros inspecionados visualmente.

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
| `assistance.py` | Arquivos, Lixeira e aplicativos permitidos |
| `wake.py` / `wake_word.ps1` | Ativação local ao ouvir “Grazi” |
| `ABOUT.md` | Visão geral e decisões do projeto |
| `assets/grazi-expressions.png` | Atlas de quatro expressões |
| `idle.py` | Temporizador de inatividade da Grazi |
| `assets/grazi-sleep.png` | Repouso com macaquinho de pelúcia |
| `assets/grazi.png` | Imagem alternativa e ícone |
| `dictation.ps1` | Reconhecimento de fala Windows |
| `INICIAR.bat` | Preparação Python 3.12 e inicialização |
