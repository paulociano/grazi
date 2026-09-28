# Grazi • protótipo Windows 0.1

Mascote de desktop personalizado para Paulo, inspirado na Grazi real: caramelo robotizada, coleira rosa e orelhas relaxadas.

## Instalar e abrir

1. Extraia **toda** esta pasta ZIP antes de executar qualquer arquivo.
2. Instale **Python 3.12 para Windows, 64 bits** em https://www.python.org/downloads/windows/ . Mantenha o Python Launcher selecionado na instalação.
3. Instale o Ollama em https://ollama.com/download/windows e abra o aplicativo.
4. Abra o Terminal do Windows e execute:

   ```powershell
   ollama pull qwen3:1.7b
   ```

5. Dê dois cliques em **INICIAR.bat**. A primeira abertura baixa o PySide6 e cria um ambiente Python na pasta `.venv`. Pode levar alguns minutos. Não precisa executar como administrador.
6. Na janela da Grazi, clique em **Conectar**. O aplicativo encontra os modelos locais. Em **Configurar**, você pode trocar o modelo.
7. Escreva uma mensagem e clique em **Enviar**.

Se o Ollama não estiver atendendo, abra-o. Você também pode executar `ollama serve` no Terminal caso ele não esteja iniciado. Um erro de porta em uso normalmente significa que ele já está aberto.

## Perfil para este notebook

Configuração informada: Intel Core i5-1335U, 8 GB de RAM (7,70 GB utilizáveis), Intel Iris Xe integrada e aproximadamente 65 GB livres no armazenamento na captura enviada.

- Modelo inicial: **Qwen3 1.7B**, cerca de 1,4 GB para download no catálogo consultado. Tamanho do arquivo não é o consumo total de RAM.
- Contexto: 2.048 tokens; saída limitada a 400 tokens; até 12 mensagens recentes enviadas ao modelo. Conversas muito longas podem ser truncadas pelo modelo.
- Memória: preferências explícitas em Configurar; últimos 40 itens de histórico persistidos.
- Modo de raciocínio desativado para reduzir espera.
- Mascote 2D com movimento leve, 20 atualizações por segundo; pode desativar o movimento.
- Não foi presumida aceleração pela GPU Intel. A velocidade deve ser avaliada no próprio notebook.
- Se ficar lento, feche programas pesados ou teste `ollama pull qwen3:0.6b`. Esse modelo menor tende a responder com menos qualidade.
- Qwen3 4B fica como experiência posterior, se houver memória disponível. Não é o padrão para este equipamento. Não recomendo começar por 8B neste perfil.

## Controles

| Ação | Como fazer |
|---|---|
| Mover Grazi | Arrastar o mascote |
| Conversar | Duplo clique no mascote |
| Abrir opções ou sair | Botão direito no mascote ou ícone na bandeja |
| Trocar modelo, tamanho, memória, voz | Configurar |
| Apagar conversa | Limpar; confirma antes de apagar |
| Parar leitura | Parar voz |
| Fechar conversa | X da janela; Grazi permanece disponível |

## Voz

**Leitura:** habilite “Ler respostas em voz alta” em Configurar. Usa síntese de voz disponível no Windows via Qt; instale uma voz de português brasileiro nas opções de idioma/fala do Windows se necessário. Não há clonagem de voz.

**Ditado:** clique em Ditado e fale. A captura usa System.Speech no Windows, por até 10 segundos, e depende de um reconhecedor pt-BR instalado e de acesso ao microfone. O texto reconhecido aparece no campo para você revisar e enviar. Não existe escuta contínua nem ativação por “Grazi”.

Se o reconhecedor local não estiver disponível, use o campo de texto com **Win+H** ou digite. O ditado do Windows via Win+H pode usar serviços online da Microsoft, conforme suas configurações; não é parte do caminho local do Ollama.

## O que está incluído e o que ainda falta

Incluído: janela transparente flutuante, arrastar, menu e bandeja, movimento suave do corpo inteiro, chat com Ollama, escolha de modelos locais, memória editável, histórico local, síntese de voz e ponte para ditado local Windows.

O visual usa a imagem aprovada; ainda não possui rig Live2D, piscadas, boca sincronizada, movimento independente das orelhas ou cauda. Essa animação exige novos assets ou rig. O movimento atual é uma oscilação discreta do mascote inteiro.

Esta versão conversa e ajuda a redigir ou planejar. **Não controla o computador, não lê a tela, não acessa agenda, não navega e não envia mensagens.** Instruções geradas pelo modelo são apenas texto. Integrações operacionais são o próximo estágio.

Não é um instalador `.exe`: é uma aplicação Python com inicializador `.bat`. Nenhuma instalação foi feita no computador do usuário remotamente. Não configura execução automática ao iniciar o Windows.

## Dados e privacidade

Preferências e histórico ficam em `%LOCALAPPDATA%\Grazi\state.json`, em texto legível. Não coloque senhas nesse campo. Limpar remove o histórico ativo, mas mantém as preferências; para apagar tudo, saia da Grazi e exclua a pasta `%LOCALAPPDATA%\Grazi`.

O aplicativo envia as mensagens exclusivamente para `http://127.0.0.1:11434`; não aceita servidor remoto nem modelos com “cloud” no nome. Isso não equivale a auditar a configuração do seu Ollama ou de modelos criados por terceiros. Use o modelo oficial indicado para este primeiro teste. Downloads de Python, bibliotecas e modelos exigem internet. Depois de preparados, chat e reconhecimento local não precisam de API paga.

## Verificação realizada

Testes de persistência/corrupção de dados, contrato HTTP com servidor simulado, falha de conexão e bloqueio de nomes cloud. Interface renderizada e fluxo de chat exercitado em Linux com Qt offscreen. **Sem execução nativa no Windows, sem teste de áudio e sem benchmark real do Qwen neste notebook.** O servidor simulado verifica a integração, não a qualidade do modelo.

## Próxima evolução

1. Medir consumo de memória e tempo de resposta do Qwen neste computador.
2. Produzir estados animados da personagem preservando orelhas relaxadas.
3. Conectar uma primeira ferramenta de leitura, como agenda, com autenticação própria.
4. Acrescentar ações explícitas e confirmação para alterações externas.

## Fontes e dependências

Pesquisa: 28/09/2026.

- Ollama chat: https://docs.ollama.com/api/chat
- Catálogo Qwen3: https://ollama.com/library/qwen3
- Modelos instalados: https://docs.ollama.com/api/tags
- Qt/PySide6: https://doc.qt.io/qtforpython-6/
- Windows System.Speech: https://learn.microsoft.com/en-us/dotnet/api/system.speech.recognition.speechrecognitionengine
- Referências de produto: https://github.com/Open-LLM-VTuber/Open-LLM-VTuber e https://github.com/moeru-ai/airi

Implementação própria; não é um fork nem importa código desses dois projetos de referência. PySide6 6.8.3 é instalado separadamente pelo pip; as licenças de Qt/PySide6 e do modelo escolhido continuam aplicáveis. A imagem da Grazi foi gerada a partir da referência fornecida pelo usuário.

Arsenal aplicado: research-and-synthesize, idea-refine, high-fidelity-image-generation e surgical-engineering.
