"""Explicit user commands only. Model output is never interpreted as an action."""
import os
import re
import subprocess
import tempfile
from pathlib import Path

TEXT_TYPES = {'.txt', '.md', '.csv', '.json', '.log'}
OPEN_TYPES = TEXT_TYPES | {'.pdf', '.docx', '.xlsx', '.pptx', '.png', '.jpg', '.jpeg', '.webp', '.bmp'}
HELP = '''Comandos de assistência:
listar arquivos
abrir pasta
abrir arquivo nome.pdf
ler arquivo notas.txt
salvar arquivo notas.txt | conteúdo do arquivo
salvar resposta em resposta.txt
excluir arquivo notas.txt (Lixeira, com confirmação)
abrir/abra calculadora, bloco de notas, terminal, explorador, Chrome, Edge, Word, Excel ou VS Code
fechar/feche calculadora ou bloco de notas (instâncias abertas pela Grazi)
Escolha sua pasta em Personalizar → Pasta de trabalho.'''


class AssistantActions:
    def __init__(self, state, confirm, opener=None, recycler=None):
        self.state = state
        self.confirm = confirm
        self.opener = opener or self._open
        self.recycler = recycler or self._recycle
        self.processes = {}

    @staticmethod
    def _open(path):
        if os.name != 'nt':
            raise ValueError('A abertura com o aplicativo padrão está disponível no Windows.')
        os.startfile(str(path))

    @staticmethod
    def _recycle(path):
        from send2trash import send2trash
        send2trash(str(path))

    def root(self):
        raw = self.state.get('file_root', '')
        if not raw:
            raise ValueError('Escolha uma Pasta de trabalho em Personalizar antes de usar arquivos.')
        root = Path(raw).resolve(strict=True)
        if not root.is_dir():
            raise ValueError('A pasta de trabalho não está disponível.')
        return root

    def path(self, name):
        root = self.root()
        # Reject Windows drive paths, device paths and alternate data streams.
        name = name.strip().strip('"')
        if not name or ':' in name or '\\' in name or Path(name).is_absolute():
            raise ValueError('Use um nome relativo à pasta de trabalho, como notas.txt ou pasta/notas.txt.')
        target = (root / name).resolve()
        if not target.is_relative_to(root) or target == root:
            raise ValueError('Esse caminho está fora da pasta de trabalho.')
        if not target.parent.is_dir():
            raise ValueError('A subpasta indicada não existe.')
        return target

    def save(self, name, content):
        target = self.path(name)
        if target.suffix.lower() not in TEXT_TYPES:
            raise ValueError('Salvo texto em .txt, .md, .csv, .json ou .log. Para documentos Word/PDF, use o aplicativo correspondente.')
        if target.exists():
            if not target.is_file():
                raise ValueError('O destino não é um arquivo.')
            if not self.confirm('Substituir arquivo?', f'{target}\n\nO conteúdo atual será substituído por:\n{content[:500]}'):
                return 'Salvamento cancelado. O arquivo foi mantido.'
            fd, temporary = tempfile.mkstemp(dir=target.parent, prefix='.grazi-')
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                    stream.write(content)
                os.replace(temporary, target)
            finally:
                Path(temporary).unlink(missing_ok=True)
        else:
            with target.open('x', encoding='utf-8') as stream:
                stream.write(content)
        return f'Salvei {target.name} em {target.parent}.'

    def execute(self, text, last_answer=''):
        text = text.strip()
        value = text.casefold()
        if value in {'ajuda', 'comandos', 'o que você pode fazer', 'o que voce pode fazer'}:
            return HELP
        apps = {
            'calculadora': 'calc.exe',
            'bloco de notas': 'notepad.exe',
            'terminal': 'wt.exe',
            'explorador de arquivos': 'explorer.exe',
            'chrome': 'chrome.exe',
            'google chrome': 'chrome.exe',
            'edge': 'msedge.exe',
            'microsoft edge': 'msedge.exe',
            'word': 'winword.exe',
            'excel': 'excel.exe',
            'visual studio code': 'code.exe',
            'vscode': 'code.exe',
        }
        for name, executable in apps.items():
            if value in {f'abrir {name}', f'abrir a {name}', f'abrir o {name}',
                         f'abra {name}', f'abra a {name}', f'abra o {name}',
                         f'iniciar {name}', f'inicie {name}', name}:
                if os.name != 'nt':
                    return 'A abertura de aplicativos está disponível no Windows.'
                try:
                    process = subprocess.Popen([executable], close_fds=True)
                except (FileNotFoundError, OSError):
                    return f'Não encontrei {name} instalado neste Windows.'
                self.processes.setdefault(name, []).append(process)
                return f'Solicitei a abertura de {name}.'
            if value in {f'fechar {name}', f'feche {name}', f'encerrar {name}', f'encerre {name}'}:
                return self.close_app(name)
        if value == 'listar arquivos':
            entries = sorted(self.root().iterdir(), key=lambda p: (not p.is_dir(), p.name.casefold()))
            if not entries:
                return 'A pasta de trabalho está vazia.'
            lines = [('Pasta: ' if p.is_dir() else 'Arquivo: ') + p.name for p in entries[:80]]
            if len(entries) > 80:
                lines.append(f'Mostrando 80 de {len(entries)} itens.')
            return '\n'.join(lines)
        if value == 'abrir pasta':
            self.opener(self.root())
            return 'Solicitei a abertura da pasta de trabalho.'
        match = re.fullmatch(r'salvar arquivo\s+(.+?)\s*\|\s*([\s\S]+)', text, re.I)
        if match:
            return self.save(match[1], match[2])
        match = re.fullmatch(r'salvar resposta em\s+(.+)', text, re.I)
        if match:
            if not last_answer:
                return 'Ainda não há uma resposta para salvar.'
            return self.save(match[1], last_answer)
        match = re.fullmatch(r'(abrir|ler|excluir) arquivo\s+(.+)', text, re.I)
        if match:
            action, name = match[1].casefold(), match[2]
            target = self.path(name)
            if not target.is_file():
                raise ValueError('Arquivo não encontrado. Use listar arquivos para conferir o nome.')
            if action == 'abrir':
                if target.suffix.lower() not in OPEN_TYPES:
                    raise ValueError('Esse tipo de arquivo não está habilitado para abertura. Use documentos, imagens ou textos; executáveis não são abertos por este comando.')
                self.opener(target)
                return f'Solicitei a abertura de {target.name} no aplicativo padrão.'
            if action == 'ler':
                if target.suffix.lower() not in TEXT_TYPES:
                    raise ValueError('A leitura nesta versão aceita apenas arquivos de texto (.txt, .md, .csv, .json, .log).')
                with target.open('rb') as stream:
                    data = stream.read(20001)
                if len(data) > 20000:
                    raise ValueError('O arquivo excede 20 KB. Abra-o no aplicativo padrão.')
                return f'Conteúdo de {target.name}:\n' + data.decode('utf-8-sig')
            if not self.confirm('Mover para a Lixeira?', f'{target}\n\nO arquivo será enviado à Lixeira do sistema.'):
                return 'Exclusão cancelada. O arquivo foi mantido.'
            self.recycler(target)
            return f'Enviei {target.name} para a Lixeira.'
        if value.startswith(('salvar arquivo', 'salvar resposta', 'abrir arquivo', 'ler arquivo', 'excluir arquivo')):
            return HELP
        return None

    def close_app(self, name):
        if os.name != 'nt':
            return 'O fechamento de aplicativos está disponível no Windows.'
        running = [p for p in self.processes.get(name, []) if p.poll() is None]
        if not running:
            return 'Não encontrei uma instância aberta por mim nesta sessão. Feche pelo próprio aplicativo.'
        pids = {p.pid for p in running}
        count = request_window_close(pids)
        if not count:
            return 'Não encontrei uma janela associada à instância aberta por mim. Algumas versões do Windows redirecionam para outro processo; feche pelo aplicativo.'
        return f'Solicitei o fechamento de {name}. Confira a janela: ela pode pedir para salvar alterações. Não forcei o encerramento.'


def request_window_close(pids):
    """WM_CLOSE preserves the application's save prompt; never terminate processes."""
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    count = 0
    @callback_type
    def visit(hwnd, unused):
        nonlocal count
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value in pids and user32.IsWindowVisible(hwnd):
            if user32.PostMessageW(hwnd, 0x0010, 0, 0):
                count += 1
        return True
    user32.EnumWindows(visit, 0)
    return count
