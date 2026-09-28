# Grazi 🐾

Assistente de desktop para Windows, com aparência inspirada na cachorrinha Grazi: caramelo robotizada, coleira rosa e orelhas relaxadas.

<img src="assets/grazi.png" alt="Grazi, cachorrinha caramelo robótica" width="260">

**Protótipo 0.1 — Python + PySide6 + Ollama + Qwen.**

## Começar

1. Baixe este repositório em **Code → Download ZIP** e extraia a pasta.
2. Instale [Python 3.12 para Windows](https://www.python.org/downloads/windows/) com Python Launcher.
3. Instale e abra [Ollama](https://ollama.com/download/windows).
4. No Terminal, execute `ollama pull qwen3:1.7b`.
5. Abra `INICIAR.bat` e clique em **Conectar**.

A primeira abertura instala as dependências Python em `.venv`. Não exige administrador. O modelo padrão e o contexto reduzido foram escolhidos como ponto inicial para um notebook com i5-1335U e 8 GB de RAM; o desempenho ainda precisa ser medido nesse equipamento.

## Funcionalidades

- Mascote transparente, sempre visível, arrastável e com movimento suave.
- Chat com modelo local do Ollama e seleção de modelos instalados.
- Memória editável e histórico local.
- Leitura por voz do Windows e ditado mediante reconhecedor pt-BR instalado.
- Controles de tamanho, movimento e voz, além de menu na bandeja.

## Limitações atuais

Não controla o computador nem acessa agenda, arquivos, tela ou internet. Não possui escuta contínua, palavra de ativação, rig Live2D ou movimentos independentes de boca, orelhas e cauda. Não há instalador `.exe` nesta versão.

Testes de integração usam servidor HTTP simulado. Interface verificada com Qt offscreen em Linux; execução Windows, áudio e inferência Qwen real ainda precisam de validação no equipamento final.

## Documentação e testes

- [Guia completo, privacidade e solução de problemas](LEIA-ME.md)
- [Registro de verificação](VERIFICACAO.txt)
- Testes: `python -m unittest discover -s tests -v`

Dados pessoais da aplicação ficam em `%LOCALAPPDATA%\Grazi`, fora deste repositório. Use **Limpar** para apagar o histórico e **Configurar** para editar a memória.

## Estrutura

| Arquivo | Função |
|---|---|
| `grazi.py` | Interface, mascote, voz e interações |
| `core.py` | Estado local e comunicação com Ollama |
| `dictation.ps1` | Ponte para reconhecimento de fala do Windows |
| `assets/grazi.png` | Personagem aprovado |
| `INICIAR.bat` | Preparação do ambiente e inicialização |
| `tests/` | Testes do núcleo e contrato HTTP |

Implementação própria, inspirada na pesquisa de Open-LLM-VTuber e AIRI, sem importar código desses projetos. Dependências e modelos mantêm suas respectivas licenças; consulte o guia.
