import pyperclip
from pynput import keyboard
from pynput.keyboard import Controller
from typing import Optional, Callable, List, Dict, Awaitable, OrderedDict
from abc import ABC, abstractmethod
from dataclasses import dataclass
from transitions import Machine
from enum import Enum
import asyncio

class KeyType(Enum):
    CTRL = 'CTRL'
    DIGIT = 'DIGIT'
    ALPHA = 'ALPHA'
    OTHER = 'OTHER'

class KeyState(Enum):
    PRESSED = 1
    RELEASED = 2

class HotkeyState:
    def __init__(self, state: KeyState, key_name: str):
        if not key_name:
            raise ValueError("Имя клавиши не может быть пустым.")
        
        self.state = state
        self.name = key_name
        self.key = self.get_key_by_name(key_name)
        self.type = self.get_key_type(self.key)

    @staticmethod
    def get_key_name(key: keyboard.Key) -> str:
        """Возвращает имя клавиши."""
        if hasattr(key, 'char'):
            return key.char
        return str(key).split('.')[-1]

    @staticmethod
    def get_key_by_name(key_name: str) -> keyboard.Key:
        """Возвращает объект клавиши по ее имени."""
        try:
            return getattr(keyboard.Key, key_name)
        except AttributeError:
            if len(key_name) == 1:
                return keyboard.KeyCode(char=key_name)
            else:
                raise ValueError(f"Имя клавиши '{key_name}' не определено.")

    @staticmethod
    def get_key_type(key: keyboard.Key) -> KeyType:
        """Возвращает тип клавиши."""
        if key in keyboard.Key.__members__.values():
            return KeyType.CTRL
        if hasattr(key, 'char'):
            if key.char.isdigit():
                return KeyType.DIGIT
            if key.char.isalpha():
                return KeyType.ALPHA
        return KeyType.OTHER

class ClipboardManager:
    def __init__(self):
        """Инициализирует менеджер буфера обмена."""
        self.kb = Controller()

    def get_system_clipboard_content(self) -> str:
        """Получает текст из системного буфера обмена.
        
        Returns:
            str: Содержимое системного буфера обмена.
        """
        return pyperclip.paste()

    def set_system_clipboard_content(self, text: str):
        """Устанавливает текст в системный буфер обмена.
        
        Args:
            text (str): Текст для установки в буфер обмена.
        """
        pyperclip.copy(text)

    def simulate_paste(self):
        """Эмулирует нажатие Ctrl+V для вставки текста из системного буфера обмена."""
        with self.kb.pressed(keyboard.Key.ctrl):
            self.kb.press('v')
            self.kb.release('v')

class Clipboard:
    def __init__(self, max_size: int, clipboard_manager: ClipboardManager):
        """Инициализирует буфер обмена с заданным максимальным размером.
        
        Args:
            max_size (int): Максимальное количество ячеек в буфере обмена.
            clipboard_manager (ClipboardManager): Менеджер системного буфера обмена.
        """
        self.max_size = max_size
        self.buffer = {}
        self.clipboard_manager = clipboard_manager

    def copy(self, index: int):
        """Копирует текст из системного буфера обмена в указанную ячейку буфера обмена.
        
        Args:
            index (int): Номер ячейки для копирования.
        """
        if len(self.buffer) >= self.max_size:
            print("Буфер обмена переполнен!")
            return

        text = self.clipboard_manager.get_system_clipboard_content()
        self.buffer[index] = text
        print(f"Текст скопирован в ячейку {index}!")

    def paste(self, index: int):
        """Копирует текст из указанной ячейки буфера обмена в системный буфер обмена и эмулирует нажатие Ctrl+V.
        
        Args:
            index (int): Номер ячейки для вставки.
        """
        if index in self.buffer:
            text = self.buffer[index]
            self.clipboard_manager.set_system_clipboard_content(text)
            print(f"Текст из ячейки {index} вставлен!")
            self.clipboard_manager.simulate_paste()
        else:
            print(f"Ячейка {index} пуста!")

    def clear(self):
        """Очищает буфер обмена."""
        self.buffer.clear()
        print("Буфер обмена очищен!")

    def list(self):
        """Выводит содержимое буфера обмена."""
        if not self.buffer:
            print("Буфер обмена пуст!")
            return
        
        for index, content in self.buffer.items():
            print(f"Ячейка {index}: {content if isinstance(content, str) else repr(content)}")

class BaseCommand(ABC):
    @abstractmethod
    def execute(self, *args, **kwargs):
        """Метод, который нужно переопределить в подклассе для реализации команды."""
        if args or kwargs:
            print(f"Приняты аргументы: args={args}, kwargs={kwargs}, но метод находится в разработке.")
        else:
            print("Эта функция находится в разработке.")

class CopyCommand(BaseCommand):
    def execute(self, *args, **kwargs):
        if args:
            clipboard.copy(args[0])
        else:
            print("Нажмите цифру для копирования в соответствующую ячейку буфера.")
            hotkey_manager.set_hotkey_state(1, KeyState.PRESSED)

class PasteCommand(BaseCommand):
    def execute(self, *args, **kwargs):
        if args:
            clipboard.paste(args[0])
        else:
            print("Нажмите цифру для вставки текста из соответствующей ячейки буфера.")
            hotkey_manager.set_hotkey_state(1, KeyState.PRESSED)

class ClearCommand(BaseCommand):
    def execute(self, *args, **kwargs):
        clipboard.clear()

class ListCommand(BaseCommand):
    def execute(self, *args, **kwargs):
        clipboard.list()

class SettingsCommand(BaseCommand):
    def execute(self, *args, **kwargs):
        if args or kwargs:
            print(f"Приняты аргументы: args={args}, kwargs={kwargs}, но метод находится в разработке.")
        else:
            print("Настройки открыты!")

class HelpCommand(BaseCommand):
    def execute(self, *args, **kwargs):
        if args or kwargs:
            print(f"Приняты аргументы: args={args}, kwargs={kwargs}, но метод находится в разработке.")
        else:
            print("Помощь открыта!")

@dataclass
class MenuCommand:
    key: str
    name: str
    description: str
    action: Callable

class HotkeyManager:
    def __init__(self):
        """Инициализирует HotkeyManager с состоянием горячих клавиш."""
        self.hotkeys_state: OrderedDict[int, HotkeyState] = OrderedDict([
            (0, HotkeyState(KeyState.RELEASED, 'alt_l'))
        ])

    def set_hotkey_state(self, hotkey: int, state: KeyState):
        """Устанавливает состояние горячей клавиши.
        
        Args:
            hotkey (int): Ключ горячей клавиши в словаре.
            state (KeyState): Состояние горячей клавиши.
        """
        if hotkey in self.hotkeys_state:
            self.hotkeys_state[hotkey].state = state

    def get_hotkey_state(self, hotkey: int) -> KeyState:
        """Возвращает состояние горячей клавиши.
        
        Args:
            hotkey (int): Ключ горячей клавиши в словаре.
        
        Returns:
            KeyState: Состояние горячей клавиши.
        """
        if hotkey in self.hotkeys_state:
            return self.hotkeys_state[hotkey].state
        return KeyState.RELEASED

    def get_hotkey_by_key(self, key: keyboard.Key) -> Optional[int]:
        """Возвращает ключ горячей клавиши по объекту клавиши.
        
        Args:
            key (keyboard.Key): Объект клавиши.
        
        Returns:
            int: Ключ горячей клавиши.
        """
        for hotkey, hotkey_state in self.hotkeys_state.items():
            if hotkey_state.key == key:
                return hotkey
        return None

class MenuState:
    def __init__(self):
        """Инициализирует MenuState с пустым списком команд."""
        self.machine = Machine(model=self, states=['wait'], initial='wait')

    def add_command(self, command: MenuCommand):
        """Добавляет новую команду и соответствующий переход в состояние."""
        self.machine.add_state(command.name)
        self.machine.add_transition(trigger=f'go_to_{command.name}', source='wait', dest=command.name, after=command.action)
        self.machine.add_transition(trigger='back_to_wait', source=command.name, dest='wait')

class KeyInterceptor:
    def __init__(self, callback: Optional[Callable[[OrderedDict], Awaitable[None]]] = None):
        """Инициализирует KeyInterceptor и запускает прослушивание клавиатуры."""
        self.pressed_keys = set()
        self.combination = OrderedDict()
        self.callback = callback
        self.listener = keyboard.Listener(
            on_press=self.intercept_on_press,
            on_release=self.intercept_on_release)
        self.listener.start()

    def intercept_on_press(self, key):
        """Перехватывает нажатие клавиши.
        
        Args:
            key: Нажатая клавиша.
        """
        if key not in self.pressed_keys:
            print(f'Key {key} pressed')
            key_name = HotkeyState.get_key_name(key)
            self.pressed_keys.add(key)
            self.combination[key] = HotkeyState(KeyState.PRESSED, key_name)

    def intercept_on_release(self, key):
        """Перехватывает отпускание клавиши.
        
        Args:
            key: Отпущенная клавиша.
        """
        if key in self.pressed_keys:
            print(f'Key {key} released')
            key_name = HotkeyState.get_key_name(key)
            self.pressed_keys.remove(key)
            self.combination[key] = HotkeyState(KeyState.RELEASED, key_name)
            if not self.pressed_keys:
                asyncio.run(self.finalize_combination(self.callback))

    async def finalize_combination(self, callback: Optional[Callable[[OrderedDict], Awaitable[None]]] = None):
        """Фиксирует и выводит текущую комбинацию клавиш.
        
        Args:
            callback (Optional[Callable[[OrderedDict], Awaitable[None]]]): Функция, вызываемая при завершении комбинации.
        """
        combination = self.get_key_combination()
        print(f'Key combination: {combination}')
        self.combination.clear()
        if callback:
            await callback(combination)

    def get_key_combination(self) -> OrderedDict:
        """Возвращает OrderedDict с последовательностью зажатых и отпущенных клавиш.
        
        Returns:
            OrderedDict: OrderedDict с последовательностью зажатых и отпущенных клавиш.
        """
        return self.combination

class HotkeyComparator:
    @staticmethod
    def compare(combination1: OrderedDict, combination2: OrderedDict) -> bool:
        """Сравнивает два OrderedDict из HotkeyState.
        
        Args:
            combination1 (OrderedDict): Первая комбинация.
            combination2 (OrderedDict): Вторая комбинация.
        
        Returns:
            bool: True, если комбинации равны, иначе False.
        """
        return combination1 == combination2

    @staticmethod
    def is_subset(subset: OrderedDict, superset: OrderedDict) -> bool:
        """Проверяет, является ли один OrderedDict подмножеством другого.
        
        Args:
            subset (OrderedDict): Потенциальное подмножество.
            superset (OrderedDict): Потенциальное надмножество.
        
        Returns:
            bool: True, если subset является подмножеством superset, иначе False.
        """
        subset_iter = iter(subset.items())
        for key, value in superset.items():
            if key == next(subset_iter, (None, None))[0] and value == subset[key]:
                try:
                    next(subset_iter)
                except StopIteration:
                    return True
        return False

class CommandManager:
    def __init__(self, menu: MenuState):
        self.menu = menu
        self.commands = [
            MenuCommand(key='s', name="settings", description="Открыть настройки", action=SettingsCommand().execute),
            MenuCommand(key='c', name="copy", description="Скопировать текст", action=CopyCommand().execute),
            MenuCommand(key='p', name="paste", description="Вставить текст", action=PasteCommand().execute),
            MenuCommand(key='h', name="help", description="Открыть помощь", action=HelpCommand().execute),
            MenuCommand(key='l', name="list", description="Отобразить список элементов", action=ListCommand().execute),
            MenuCommand(key='r', name="clear", description="Очистить экран", action=ClearCommand().execute)
        ]
        self.add_commands_to_menu()

    def add_commands_to_menu(self):
        for command in self.commands:
            self.menu.add_command(command)

    def print_commands(self):
        """Выводит название и описание каждой команды."""
        for command in self.commands:
            print(f"Команда: {command.name}\nОписание: {command.description}\n")

    def get_command_action(self, name: str) -> Optional[Callable]:
        """Возвращает ссылку на функцию по названию команды.
        
        Args:
            name (str): Название команды.
        
        Returns:
            Callable: Функция, связанная с данной командой, или None, если команда не найдена.
        """
        command_dict: Dict[str, Callable] = {command.name: command.action for command in self.commands}
        return command_dict.get(name, None)

    def get_command_by_key(self, key: str) -> Optional[Callable]:
        """Возвращает функцию по символу команды.
        
        Args:
            key (str): Символ команды.
        
        Returns:
            Callable: Функция, связанная с данной командой, или None, если команда не найдена.
        """
        for command in self.commands:
            if command.key == key:
                return getattr(self.menu, f'go_to_{command.name}')
        return None

    def execute_command(self, command_name: str):
        """Выполняет команду по её имени."""
        action = self.get_command_action(command_name)
        if action:
            print(f"Выполнение команды: {command_name}")
            action()

# Создадим экземпляр HotkeyManager
hotkey_manager = HotkeyManager()

# Создадим экземпляр MenuState
menu = MenuState()

# Создадим экземпляр CommandManager и добавим команды в меню
command_manager = CommandManager(menu)

# Создадим экземпляр ClipboardManager и Clipboard
clipboard_manager = ClipboardManager()
clipboard = Clipboard(max_size=5, clipboard_manager=clipboard_manager)

# Функция для вывода комбинации
async def print_combination(combination: OrderedDict):
    print("Комбинация клавиш:", combination)

# Создание экземпляра KeyInterceptor с привязкой функции вывода комбинации
key_interceptor = KeyInterceptor(callback=print_combination)

# Основной цикл, чтобы программа не завершалась
async def main():
    while True:
        await asyncio.sleep(1)

asyncio.run(main())
