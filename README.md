A highly customizable Windows utility to map a MIDI Controller to various functions.

# USAGE
To use download the latest release and extract the archive or clone the repo. After configuring run once for the startup and start menu shortcuts to be created.
## Configuration
All configuration uses YAML. The basic configuration is located in the `config.yaml` file. The options are:
| Option | Value | Default | Description |
| ------ | ----- | ------- | ----------- |
| tray_icon | on/off | on | Toggle system tray icon. Clicking the icon exits the mapper. |
| autostart | on/off | off | Toggle autostart. |
| start_menu_shortcut | on/off | off | Toggle start menu shortcut. |
| midi_port | integer | 0 | The MIDI port to map from. Check the log.txt file after startup for a list of connected MIDI devices and their corresponding ports. |
| start_key | 0-127 | 0 | The first key on your MIDI keyboard. Check the log to see pressed keys. |
| end_key | 0-127 | 127 | The last key on your MIDI keyboard. Check the log to see pressed keys. |
| audio_volume | 0-100 | 100 | The volume of the sound effects. |
| sound_on | file path | assets\switch.ogg | The path of the press down sound effect. |
| sound_off | file path | assets\switch.ogg | The path of the release sound effect. |
## Menus
All mappings are defined using YAML files called menus. They can all be found in the `/Menus/` directory. Their current syntax is as follows:
```yaml
# All fields are optional.
actions:  # Contains a list of all actions in this menu
- function: <function>  # The function to be activated
  functions: [<functions>]  # Contains a list of functions to be activated, can be used instead of "function"
  key: <key>  # The key that is to activate the action when pressed
  keys: [<keys>]  # A list of keys that are to activate the action when pressed, can be used instead of "key"
  only_downpress: <boolean>  # Toggle whether the function should be activated only when the key is pressed, and not released, defaults to off
  return: <int>  # By how many menus it should go back after the action, if positive will go back that many steps, 0 to disable, -1 to go back to the main menu
menus:  # Contains a list of all sub-menus of this menu
- name: <menu_name>  # The name of the sub-menu without the yaml extension, a menu file with that name must exist in the /Menus/ directory
  key: <key>  # The key that is to enter the sub-menu when pressed
  keys: [<keys>]  # A list of keys that are to enter the sub-menu when pressed, can be used instead of "key"
```
All menus except the main one are automatically bound to return to their parent menus when the first black key is pressed.
### Keys
They keys can be written in the following ways:
| Syntax | Description |
| ------ | ----------- |
| <0-127> | The absolute MIDI key. |
| r<-127-127> | The relative key. 0 is the first and -1 is the last key. |
| w<-127-127> | The relative white key. 0 is the first and -1 is the last white key. |
| b<-127-127> | The relative black key. 0 is the first and -1 is the last black key. |
## Functions
Here are the currently implemented functions:
| Name | Arguments | Description |
| ---- | --------- | ----------- |
| log | text | Outputs the text in the log. |
| run | command | Executes the command in a shell. Accepts any shell command, passes arguments. |
| press | keys | Press the keys. Can accept single keys or shortcuts. Shortcuts must be written as `key1+key2`. Modifier keys should go first. Do not use with `only_downpress`.
| quit | - | Exits the utility. Must be used before any other aplications can use the MIDI device. |
### Custom Functions
You may add custom functions to the `/Mods/` directory using Python scripts. The function will be named after the python file. The simplest way to make a function is to define a function in your file:
```python
# The function must accept a dictionary containing data about the press, as well as any other arguments your function may use split by whitespaces.
# The dictionary contains the following data:
# 'key': <int> - The MIDI key that was pressed, 0-127
# 'on': <boolean> - Whether the key was pressed or released
# 'vel': <int> - The velocity the key was pressed at, 0-127
# 'state': <state> - A state object containing some properties about the utility, such as the config, which is a dict containg the entire configuration, and a quit method that exits the utility.
def function(info):
    # Code to be run when pressed
```
If your function needs to store data, you may use a class:
```python
# The class is initialized upon startup
class Handler:
    def __init__(self):
        # Your code
    # Function as described previously
    def function(self, info):
        # Code to be run when pressed
```
