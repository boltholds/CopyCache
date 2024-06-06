from pynput import keyboard
from transitions import Machine
from dataclasses import dataclass
from typing import Callable, List, Dict, Optional
from abc import ABC, abstractmethod

@dataclass
class MenuCommand:
    key: str
    name: str
    description: str
    action: Callable

class BaseCommand(ABC):
    @abstractmethod
    def execute(self):
        """Метод, который нужно переопределить в подклассе для реализации команды."""
        print("Эта функция находится в разработке.")

class SettingsCommand(BaseCommand):
    def execute(self):
        print("Настройки открыты!")

class CopyCommand(BaseCommand):
    def execute(self):
        print("Текст скопирован!")

class PasteCommand(BaseCommand):
    def execute(self):
        print("Текст вставлен!")

class HelpCommand(BaseCommand):
    def execute(self):
        print("Помощь открыта!")

class ListCommand(BaseCommand):
    def execute(self):
        print("Список элементов отображен!")

class ClearCommand(BaseCommand):
    def execute(self):
        print("Экран очищен!")

class WaitCommand(BaseCommand):
    def execute(self):
        pass  # Ничего не делает

class CommandMenu:
    def __init__(self):
        """Инициализирует CommandMenu с пустым списком команд."""
        self.commands: List[MenuCommand] = []
        self.states = ['wait'] + [command.name for command in commands]
        self.machine = Machine(model=self, states=self.states, initial='wait')
        self._setup_transitions()

    def _setup_transitions(self):
        for state in self.states:
            if state != 'wait':
                self.machine.add_transition(trigger=f'go_to_{state}', source='wait', dest=state, after='execute_command')
        self.machine.add_transition(trigger='back_to_wait', source='*', dest='wait')

    def add_command(self, command: MenuCommand):
        """Добавляет новую команду в список команд.
        
        Args:
            command (MenuCommand): Команда, которую нужно добавить.
        """
        self.commands.append(command)

    def get_command_names(self) -> List[str]:
        """Возвращает список названий всех команд.
        
        Returns:
            List[str]: Список названий команд.
        """
        return [command.name for command in self.commands]

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
                return getattr(self, f'go_to_{command.name}')
        return None

    def execute_command(self):
        command_name = self.state
        action = self.get_command_action(command_name)
        if action:
            print(f"Выполнение команды: {command_name}")
            action()

# Создадим экземпляры MenuCommand с использованием классов команд
commands = [
    MenuCommand(key='s', name="settings", description="Открыть настройки", action=SettingsCommand().execute),
    MenuCommand(key='c', name="copy", description="Скопировать текст", action=CopyCommand().execute),
    MenuCommand(key='p', name="paste", description="Вставить текст", action=PasteCommand().execute),
    MenuCommand(key='h', name="help", description="Открыть помощь", action=HelpCommand().execute),
    MenuCommand(key='l', name="list", description="Отобразить список элементов", action=ListCommand().execute),
    MenuCommand(key='r', name="clear", description="Очистить экран", action=ClearCommand().execute),
    MenuCommand(key='w', name="wait", description="Ожидание", action=WaitCommand().execute)
]

# Создадим экземпляр CommandMenu и добавим команды
menu = CommandMenu()
for command in commands:
    menu.add_command(command)

# Переменная для отслеживания состояния Alt
alt_pressed = False

# Функция для обработки нажатий клавиш
def on_press(key):
    global alt_pressed
    if key == keyboard.Key.alt_l:
        alt_pressed = True
    if alt_pressed:
        try:
            if hasattr(key, 'char'):
                command = menu.get_command_by_key(key.char)
                if command:
                    command()
                    menu.back_to_wait()
        except AttributeError:
            pass

def on_release(key):
    global alt_pressed
    if key == keyboard.Key.alt_l:
        alt_pressed = False
    print(f'{key} released')
    if key == keyboard.Key.esc:
        # Stop listener
        return False

# Запуск прослушивания клавиатуры
listener = keyboard.Listener(
    on_press=on_press,
    on_release=on_release)
listener.start()

# Основной цикл, чтобы программа не завершалась
while True:
    pass
