# Grazi • protótipo Windows 0.8

Mascote de desktop personalizado para Paulo, inspirado na Grazi real: caramelo robotizada, coleira rosa e orelhas relaxadas.

## Instalar e abrir

1. Extraia **toda** esta pasta ZIP antes de executar qualquer arquivo.
2. Instale **Python 3.12 para Windows, 64 bits** em https://www.python.org/downloads/windows/ . Mantenha o Python Launcher selecionado na instalação.
3. Instale o Ollama em https://ollama.com/download/windows e abra o aplicativo.
4. Abra o Terminal do Windows e execute:

   ```powershell
   ollama pull qwen3:1.7b
   ```

5. Dê dois cliques em **INICIAR.bat**. A primeira abertura baixa o PySide6 e o edge-tts e cria um ambiente Python na pasta `.venv-py312`. Pode levar alguns minutos. Não precisa executar como administrador.
6. No botão direito da Grazi, abra **Abrir conversa completa** e clique em **Conectar**. O aplicativo encontra os modelos locais. Em **Configurar**, você pode trocar o modelo.
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

## Repouso automático

Por padrão, depois de mais de 1 minuto sem interação com a Grazi, ela troca suavemente para a pose deitada junto ao macaquinho de pelúcia, com movimento de respiração. O balão se recolhe. Cliques, arrastar, teclas e novos pedidos a acordam. O contador fica suspenso durante ditado, processamento, conexão e preparação/reprodução de voz. Isso mede interação com a Grazi, sem monitorar teclado ou mouse de outros aplicativos. Com movimentos desativados, a pose deitada permanece estática.

Em **Personalizar**, você pode desligar o repouso automático ou ajustar o tempo entre 1 e 30 minutos. **Descansar agora** funciona também com repouso automático desligado; **Acordar** reabre o balão. A Grazi não interrompe uma resposta ou ditado em andamento para descansar.

## Ativação por voz

Em **Personalizar**, a opção **Ativar ao ouvir “Grazi”** fica ligada por padrão em instalações novas e é migrada para instalações antigas que ainda não tinham uma escolha explícita. A Grazi usa o reconhecedor `System.Speech` local do Windows, com uma gramática que escuta somente a palavra de ativação. Ao ouvir “Grazi”, o reconhecimento de ditado é iniciado para você falar e revisar o pedido. A escuta pausa enquanto ela processa ou fala e não usa gravação contínua na nuvem. É necessário instalar um reconhecedor de fala **Português (Brasil)** no Windows; se houver uma falha temporária, a Grazi mostra o diagnóstico e tenta novamente. Você pode desligá-la em Personalizar ou no menu do botão direito.

## Arquivos e aplicativos

Escolha uma **Pasta de trabalho** em Personalizar. Os comandos são deliberadamente explícitos:

`listar arquivos`, `abrir pasta`, `abrir arquivo nome.pdf`, `ler arquivo notas.txt`, `salvar arquivo notas.txt | conteúdo`, `salvar resposta em resposta.txt`, `excluir arquivo notas.txt`, `abrir calculadora`, `abrir bloco de notas`, `fechar calculadora` e `fechar bloco de notas`.

O caminho é sempre relativo à pasta escolhida. A Grazi não abre `.exe`, não aceita caminhos fora da pasta, não executa texto produzido pelo Qwen e não apaga diretamente: exclusões vão para a Lixeira e pedem confirmação. Salvamentos substituindo arquivo também pedem confirmação e usam arquivo temporário antes de trocar o destino. O fechamento envia uma solicitação normal ao aplicativo, permitindo que ele pergunte se deve salvar; não há encerramento forçado.

## Controles

| Ação | Como fazer |
|---|---|
| Mover Grazi | Arrastar o mascote |
| Reabrir balão | Duplo clique no mascote |
| Histórico completo | Botão direito → Abrir conversa completa |
| Abrir opções ou sair | Botão direito no mascote ou ícone na bandeja |
| Trocar modelo, tamanho, memória, voz | Configurar |
| Apagar conversa | Limpar; confirma antes de apagar |
| Repetir última resposta | Ouvir no balão ou Ouvir última resposta no menu; usa a voz selecionada mesmo com leitura automática desligada |
| Ativar por voz | Personalizar → Ativar ao ouvir “Grazi”; botão direito → Desativar ativação por voz |
| Parar leitura | Parar voz |
| Fechar conversa | X da janela; Grazi permanece disponível |

## Voz

**Leitura Windows:** habilite “Ler respostas em voz alta” em Configurar. Usa síntese de voz disponível no Windows via Qt; instale uma voz de português brasileiro nas opções de idioma/fala do Windows se necessário. Não há clonagem de voz.

**Leitura natural online:** em **Personalizar**, escolha **Francisca — feminina pt-BR (online)** e marque “Ler respostas em voz alta”. O botão **Ouvir amostra** reproduz uma frase com a opção selecionada. A voz online envia o texto falado à Microsoft. É opcional e exige internet; falhas são exibidas no balão. O texto completo permanece na conversa. A voz feminina não tem uma idade garantida.

O balão acompanha cada trecho da fala. As setas permitem reler e interrompem a reprodução. Pode haver pausas entre trechos enquanto o próximo áudio é preparado. **Parar** interrompe e descarta resultados atrasados.

**Ditado:** clique em Ditado e fale. A captura usa System.Speech no Windows, por até 10 segundos, e depende de um reconhecedor pt-BR instalado e de acesso ao microfone. O texto reconhecido aparece no campo para você revisar e enviar. Não existe escuta contínua nem ativação por “Grazi”.

Se o reconhecedor local não estiver disponível, use o campo de texto com **Win+H** ou digite. O ditado do Windows via Win+H pode usar serviços online da Microsoft, conforme suas configurações; não é parte do caminho local do Ollama.

## O que está incluído e o que ainda falta

Incluído: janela transparente flutuante, arrastar, menu e bandeja, flutuação em repouso, inclinação/brilho ao ouvir, pulsação ao processar, brilho rosa ao falar, chat com Ollama, escolha de modelos locais, memória editável, histórico local, síntese de voz, ponte para ditado local Windows e ações locais explícitas para hora/data, cálculos, Calculadora, Bloco de Notas, status do sistema e GitHub.

As ações locais não executam texto arbitrário. Elas são reconhecidas por uma lista fixa de comandos; a resposta do Qwen não pode iniciar processos nem montar comandos. Exemplos: `que horas são`, `que dia é hoje`, `calcule 12 * 8`, `abrir calculadora`, `abrir bloco de notas`, `status do computador` e `abrir github`.

O visual usa quatro quadros da personagem: repouso, piscada, boca aberta e atenção. A boca alterna durante a reprodução de voz; não é sincronização por fonemas. Não há rig Live2D nem movimento independente de cauda. As orelhas ficam relaxadas em repouso. Se o atlas estiver indisponível, o mascote usa a imagem estática original.

Esta versão conversa e ajuda a redigir ou planejar. **Além dos comandos explícitos acima, não controla o computador, não lê a tela, não acessa agenda, não navega de forma geral e não envia mensagens.** Instruções geradas pelo modelo são apenas texto. Integrações operacionais são o próximo estágio.

Não é um instalador `.exe`: é uma aplicação Python com inicializador `.bat`. Nenhuma instalação foi feita no computador do usuário remotamente. Não configura execução automática ao iniciar o Windows.

## Dados e privacidade

Preferências e histórico ficam em `%LOCALAPPDATA%\Grazi\state.json`, em texto legível. Não coloque senhas nesse campo. Limpar remove o histórico ativo, mas mantém as preferências; para apagar tudo, saia da Grazi e exclua a pasta `%LOCALAPPDATA%\Grazi`.

O chat com o modelo envia as mensagens para `http://127.0.0.1:11434`; não aceita servidor remoto nem modelos com “cloud” no nome. Isso não equivale a auditar a configuração do seu Ollama ou de modelos criados por terceiros. Use o modelo oficial indicado para este primeiro teste. A voz Francisca, se selecionada, envia separadamente o texto a ser falado ao serviço online da Microsoft; não envia a memória e o histórico inteiro como pacote de voz. Áudios temporários são removidos ao terminar ou cancelar (uma interrupção abrupta pode deixar arquivos na pasta temporária do Windows). Downloads de Python, bibliotecas e modelos exigem internet. Depois de preparados, chat e reconhecimento local não precisam de API paga.

## Verificação realizada

Testes de persistência/corrupção de dados, contrato HTTP com servidor simulado, falha de conexão e bloqueio de nomes cloud. Interface renderizada e fluxo de chat exercitado em Linux com Qt offscreen. Os 20 testes incluem balão, paginação, bordas de tela, preferências de voz e descarte de áudio atrasado. A consulta ao serviço Edge falhou por certificado TLS neste ambiente; áudio real não foi validado. **Sem execução nativa no Windows, sem teste de áudio e sem benchmark real do Qwen neste notebook.** O servidor simulado verifica a integração, não a qualidade do modelo.

## Próxima evolução

1. Medir consumo de memória e tempo de resposta do Qwen neste computador.
2. Avaliar a voz e a latência no Windows; testar futuramente Kokoro/Dora offline.
3. Conectar uma primeira ferramenta de leitura, como agenda, com autenticação própria.
4. Acrescentar ações explícitas e confirmação para alterações externas.

## Fontes e dependências

Pesquisa: 28/09/2026.

- Ollama chat: https://docs.ollama.com/api/chat
- Catálogo Qwen3: https://ollama.com/library/qwen3
- Modelos instalados: https://docs.ollama.com/api/tags
- Voz Edge: https://github.com/rany2/edge-tts (LGPLv3, instalado via pip)
- Alternativa local Kokoro: https://github.com/hexgrad/kokoro
- Voz Dora: https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md
- Qt/PySide6: https://doc.qt.io/qtforpython-6/
- Windows System.Speech: https://learn.microsoft.com/en-us/dotnet/api/system.speech.recognition.speechrecognitionengine
- Referências de produto: https://github.com/Open-LLM-VTuber/Open-LLM-VTuber e https://github.com/moeru-ai/airi

Implementação própria; não é um fork nem importa código desses dois projetos de referência. PySide6 6.8.3 é instalado separadamente pelo pip; as licenças de Qt/PySide6 e do modelo escolhido continuam aplicáveis. A imagem da Grazi foi gerada a partir da referência fornecida pelo usuário.

Arsenal aplicado: research-and-synthesize, idea-refine, high-fidelity-image-generation e surgical-engineering.
