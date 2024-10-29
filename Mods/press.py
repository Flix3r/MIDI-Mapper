from pynput.keyboard import Key, Controller

def function(info, combo):
    keyboard = Controller()
    for i in (combo.split('+') if info['on'] else reversed(combo.split('+'))):
        keyboard.touch(i if len(i) == 1 else getattr(Key, i.lower()), info['on'])