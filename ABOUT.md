# Sobre a Grazi

## O que é

Grazi é uma assistente pessoal de área de trabalho para Windows, criada para ser uma presença pequena, simpática e útil no computador do Paulo. Sua identidade visual combina a cachorrinha caramelo real do usuário com uma interpretação robotizada: coleira rosa, placa com o nome Grazi, detalhes mecânicos e orelhas naturalmente relaxadas.

Ela usa um modelo local do Ollama — por padrão, Qwen3 1.7B — para conversar em português brasileiro. A interface foi pensada para ficar disponível sem ocupar uma janela inteira: a conversa aparece em um balão ligado ao mascote, e a conversa completa continua disponível pelo botão direito.

## Princípios do projeto

- **Local primeiro:** o chat é enviado ao Ollama em `127.0.0.1`. Não há API paga obrigatória.
- **Ações explícitas:** o modelo conversa, mas não transforma sua própria resposta em código ou comando de sistema.
- **Escopo visível:** ações com arquivos só funcionam dentro da Pasta de trabalho escolhida.
- **Confirmação humana:** sobrescrever e enviar arquivos à Lixeira exigem confirmação.
- **Reversibilidade:** exclusão usa a Lixeira; fechamento de aplicativo envia uma solicitação normal para que o programa possa perguntar se deve salvar.
- **Privacidade configurável:** a ativação por voz usa o reconhecedor local do Windows; a voz Francisca é opcional e online.
- **Baixo consumo:** a personagem, o balão e as animações foram dimensionados para um notebook com 8 GB de RAM e gráficos integrados.

## Como funciona

```text
Você fala ou digita
        ↓
Balão da Grazi / ditado do Windows
        ↓
Comando explícito? ── sim → ação permitida e confirmação quando necessário
        │
        não
        ↓
Ollama local → resposta em português → balão e voz opcional
```

O reconhecimento da palavra “Grazi” é separado do ditado: primeiro a gramática local procura a palavra de ativação; depois a Grazi inicia uma captura curta para você revisar o pedido. A escuta é pausada enquanto ela fala, pensa ou executa uma ação.

## Assistência atual

A Pasta de trabalho é escolhida na tela **Personalizar**. Dentro dela, a Grazi pode:

- listar arquivos e subpastas;
- abrir a pasta ou arquivos compatíveis no aplicativo padrão;
- ler arquivos pequenos de texto;
- salvar texto fornecido após `|`;
- salvar a última resposta em um arquivo;
- enviar um arquivo para a Lixeira após confirmação;
- abrir Calculadora e Bloco de Notas;
- solicitar o fechamento de instâncias desses aplicativos que ela própria abriu.

Ela não abre executáveis, não aceita caminhos absolutos ou caminhos que escapem da Pasta de trabalho e não encerra processos à força. Documentos maiores ou formatos não textuais devem ser abertos no aplicativo apropriado.

## Vozes

A opção padrão é a voz do Windows, instalada no próprio computador. A opção Francisca usa `edge-tts` e o serviço online de síntese da Microsoft; quando selecionada, o texto que será falado é transmitido ao serviço. Essa opção requer internet, não clona a voz de ninguém e não tem idade percebida garantida. O projeto também registra Kokoro/Dora como alternativa local para uma etapa futura, mas esse modelo não é baixado automaticamente.

## Animação e presença

O mascote tem estados de repouso, escuta, processamento e fala. Há piscada, boca alternada durante a reprodução, inclinação ao ouvir e brilho discreto. Após o tempo configurado — um minuto por padrão — ela se deita com um macaquinho de pelúcia e respira suavemente. Qualquer interação acorda a Grazi. O recurso pode ser desligado ou ajustado entre 1 e 30 minutos.

## Limites atuais

Grazi ainda não lê a tela, controla livremente qualquer aplicativo, acessa agenda, envia mensagens, navega na internet por conta própria ou inicia automaticamente com o Windows. O atlas atual não é um rig Live2D e a boca não faz sincronização fonética precisa. A ativação por voz e o áudio real precisam ser validados no Windows final com microfone e reconhecedor pt-BR instalados.

## Estrutura técnica

- `grazi.py`: janela, mascote, menu, bandeja e coordenação.
- `balloon.py`: balão compacto ancorado ao mascote.
- `core.py`: estado local, Ollama e comandos simples.
- `assistance.py`: ações de arquivos, aplicativos e confirmação.
- `wake.py` / `wake_word.ps1`: palavra de ativação local.
- `speech.py`: voz do Windows e Edge, reprodução e cancelamento.
- `idle.py`: temporizador de repouso.
- `assets/`: personagem, expressões e pose deitada.

## Próximos passos

1. Validar ativação por voz, áudio e ações nativas no Windows do usuário.
2. Adicionar pré-visualização segura antes de salvar arquivos maiores.
3. Avaliar uma voz brasileira local com Kokoro para reduzir dependência online.
4. Expandir aplicativos permitidos por uma lista explícita e configurável.
5. Melhorar a animação facial sem aumentar significativamente o consumo de memória.

## Licenças e referências

O código deste repositório é uma implementação própria. PySide6, Ollama, Qwen, `edge-tts`, `Send2Trash` e os modelos de voz mantêm suas próprias licenças. Consulte o [guia completo](LEIA-ME.md) para fontes, privacidade e solução de problemas.
