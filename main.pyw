import sys
import rtmidi
import importlib
import winshell
import os

import yaml

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

sys.stdout = open('log.txt', 'w')
sys.stdout = open('log.txt', 'w')

print(sys.argv)


def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.load(f, Loader=Loader)


config = load_yaml('config.yaml')
menu_data = load_yaml('Menus/main.yaml')

# Set defaults
config.setdefault('tray_icon', True)
config.setdefault('start_key', 0)
config.setdefault('end_key', 127)
config.setdefault('audio_volume', 100)
config.setdefault('midi_port', 0)
config.setdefault('sound_on', r'assets\switch.ogg')
config.setdefault('sound_off', r'assets\switch.ogg')
config.setdefault('autostart', False)
config.setdefault('start_menu_shortcut', False)


class State:
    def __init__(self):
        self.running = True
        self.config = config
        self.icon = None

    def quit(self):
        self.running = False


state = State()
midi_in = rtmidi.RtMidiIn()

# Print available MIDI ports
print('\nMIDI Ports:\n')
for i in range(midi_in.getPortCount()):
    print(str(i) + ' | ' + midi_in.getPortName(i))
print('\n')


def create_shortcut(path, autostart=False):
    from win32com.client import Dispatch

    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(os.path.join(path, "MIDI Mapper.lnk"))
    shortcut.Targetpath = 'pythonw'
    shortcut.Arguments = '"' + os.path.realpath(__file__) + ('" autostart' if autostart else '"')
    shortcut.WorkingDirectory = os.path.dirname(os.path.realpath(__file__))
    shortcut.IconLocation = os.path.abspath(r'assets\icon.ico')
    shortcut.save()


shortcut_made = "MIDI Mapper.lnk" in os.listdir(winshell.start_menu())
if config['start_menu_shortcut'] and not shortcut_made:
    # Create shortcut in Start Menu folder
    create_shortcut(winshell.start_menu())
elif shortcut_made and not config['start_menu_shortcut']:
    # Delete shortcut from Start Menu folder
    os.remove(os.path.join(winshell.start_menu(), "MIDI Mapper.lnk"))

shortcut_made = "MIDI Mapper.lnk" in os.listdir(winshell.startup())
if config['autostart'] and not shortcut_made:
    # Create shortcut in Startup folder
    create_shortcut(winshell.startup(), True)
elif shortcut_made and not config['autostart']:
    # Delete shortcut from Startup folder
    os.remove(os.path.join(winshell.startup(), "MIDI Mapper.lnk"))
    try:
        # Exit if autostarted despite it being off
        if sys.argv[1] == 'autostart':
            sys.exit()
    except IndexError:
        pass

# Try to open MIDI port
try:
    midi_in.openPort(config['midi_port'])
except rtmidi.Error as e:
    if str(e) == 'MidiInWinMM::openPort: error creating Windows MM MIDI input port.':
        print('Could not open MIDI input port, check if any other programs may be using the MIDI device.')
    elif str(e).endswith('is invalid'):
        print('That port does not exist, check the config file.')
    sys.exit()

if config['tray_icon']:
    import threading
    from PIL import Image
    from pystray import Menu, MenuItem, Icon


    def on_click(icon):
        state.quit()


    def icon_function():
        menu = Menu(
            MenuItem('Kill', on_click, default=True))
        state.icon = Icon('MIDI Mapper', Image.open(r'assets\icon.png'), 'MIDI Mapper', menu)
        state.icon.run()


    icon_thread = threading.Thread(target=icon_function)
    icon_thread.start()
    print("Started icon thread")

if config['audio_volume'] != 0:
    from os import environ

    environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'
    import pygame.mixer

    pygame.mixer.init()
    sound_on = pygame.mixer.Sound(config['sound_on'])
    sound_off = pygame.mixer.Sound(config['sound_off'])


def is_key_black(key):
    return key % 12 in (1, 3, 6, 8, 10)


def is_key_white(key):
    return key % 12 in (0, 2, 4, 5, 7, 9, 11)


# Convert relative keys to absolute
def absolute_key(key, start=config['start_key'], end=config['end_key']):
    match str(key)[0]:
        case 'r':
            if int(key[1:]) < 0:
                return end + int(key[1:]) + 1
            return start + int(key[1:])
        case 'w':
            if int(key[1:]) < 0:
                new_key = end
                while is_key_black(new_key):
                    new_key -= 1
                for i in range(abs(int(key[1:])) - 1):
                    new_key -= 1
                    while is_key_black(new_key):
                        new_key -= 1
                return new_key
            else:
                new_key = start
                while is_key_black(new_key):
                    new_key += 1
                for i in range(int(key[1:])):
                    new_key += 1
                    while is_key_black(new_key):
                        new_key += 1
                return new_key
        case 'b':
            if int(key[1:]) < 0:
                new_key = end
                while is_key_white(new_key):
                    new_key -= 1
                for i in range(abs(int(key[1:])) - 1):
                    new_key -= 1
                    while is_key_white(new_key):
                        new_key -= 1
                return new_key
            else:
                new_key = start
                while is_key_white(new_key):
                    new_key += 1
                for i in range(int(key[1:])):
                    new_key += 1
                    while is_key_white(new_key):
                        new_key += 1
                return new_key
        case _:
            return int(key)


def get_handler_pair(function):
    parts = function.partition(' ')
    module = importlib.import_module('Functions.' + parts[0])
    try:
        to_call = module.Handler()
    except AttributeError:
        to_call = module
    return [to_call, parts[2]]


class Menu:
    def __init__(self, data, path='main'):
        print('Loading menu: ' + path)
        print(data)
        self.actions = []
        for action in data.get('actions', []):
            self.actions.append({'keys':
                                     [absolute_key(key) for key in
                                      action.get('keys', [action['key']] if 'key' in action else [])],
                                 'only_downpress': action.get('only_downpress', False),
                                 'functions':
                                     [get_handler_pair(function) for function in
                                      action.get('functions', [action.get('function')])],
                                 'return': action.get('return', 0)})
        # Make first black key return
        if path != 'main':
            self.actions.append({'keys': [absolute_key('b0')],
                                 'only_downpress': True,
                                 'functions': [],
                                 'return': 1})
        self.menus = []
        for menu in data.get('menus', []):
            if menu['path'] in path.split('/'):
                raise RecursionError('Can not loop menus')

            self.actions.append(
                {'keys': [absolute_key(key) for key in action.get('keys', [action['key']] if 'key' in menu else [])],
                 'only_downpress': True,
                 'functions': [['menu', len(self.menus)]],
                 'return': 0})
            self.menus.append(Menu(load_yaml(f"Menus/{menu['name']}.yaml"), path + '/' + menu['path']))
        self.menu = -1

    def press(self, note, on, vel):
        # Redirect if in submenu
        if self.menu != -1:
            to_return = self.menus[self.menu].press(note, on, vel)
            if to_return == 0:
                return 0
            self.menu = -1
            return -1 if to_return == -1 else to_return - 1

        for action in self.actions:
            if note not in action['keys'] or (action['only_downpress'] and not on):
                continue
            for function in action['functions']:
                if function is None:
                    continue
                if function[0] == 'menu':
                    self.menu = function[1]
                    continue
                function[0].function(
                    {'key': note,
                     'on': on,
                     'vel': vel,
                     'state': state
                     },
                    *function[1].split()
                )
            return action['return']


main_menu = Menu(menu_data)
print("Menus loaded, listening started.")

# Main loop
try:
    while state.running:
        msg = midi_in.getMessage(8)
        if not msg or not msg.isNoteOnOrOff():
            continue
        print(f"Note: {msg.getMidiNoteName(msg.getNoteNumber())}"
              f"({msg.getNoteNumber()}), "
              f"{'on' if msg.isNoteOn() else 'off'}, "
              f"{msg.isNoteOn()}, "
              f"velocity: {msg.getVelocity()}")
        main_menu.press(msg.getNoteNumber(), msg.isNoteOn(), msg.getVelocity())
        if config['audio_volume'] == 0.0:
            continue
        if msg.isNoteOn():
            sound_on.set_volume(msg.getVelocity() / 127)
            sound_on.play()
        elif msg.isNoteOff():
            sound_off.set_volume(0.5)
            sound_off.play()
except KeyboardInterrupt:
    pass
finally:
    if state.icon is not None:
        state.icon.stop()
    midi_in.closePort()
    print("\nExiting..")
