# Chisel
`Chisel` is a collection of `LLDB` commands to assist in the debugging of iOS apps.

[[Installation](#installation) &bull; [Commands](#commands) &bull; [Custom Commands](#custom-commands) &bull; [Development Workflow](#development-workflow) [Contributing](#contributing) &bull; [License](#license)]

## Installation
Add the following line to your _~/.lldbinit_ file. If it doesn't exist, create it.

```
# ~/.lldbinit
...
command script import /path/to/chisel/fblldb.py

```

The commands will be available the next time `Xcode` starts.

## Commands
There are many commands; here's a few:

|Command                           |Description|
|----------------------------------|-----------|
|pviews                            |Print the recursive view description for the key window.|
|pvc                               |Print the recursive view controller description for the key window.|
|show{view,image,layer,imageref}|Draw the argument into an image and open it in Preview.app.|
|fv                                |Find a view in the hierarchy whose class name matches the provided regex.|
|fvc                               |Find a view controller in the hierarchy whose class name matches the provided regex.|
|show/hide                         |Show or hide the given view or layer. You don't even have to continue the process to see the changes!|
|mask/unmask                       |Overlay a view or layer with a transparent rectangle to visualize where it is.|
|border/unborder                   |Add a border to a view or layer to visualize where it is.|
|caflush                           |Flush the render server (equivalent to a "repaint" if no animations are in-flight).)|
|bmessage                          |Set a symbolic breakpoint on the method of a class or the method of an instance without worrying which class in the hierarchy actually implements the method.|
|wivar                             |Set a watchpoint on an instance variable of an object.|
|presponder                        |Print the responder chain starting from the given object.|
|...                               |... and many more!|

To see the list of **all** of the commands execute the help command in `LLDB`.

```
(lldb) help
The following is a list of built-in, permanent debugger commands:
...

The following is a list of your current user-defined commands:
...
```

The bottom of the list will contain all of the commands sourced from `Chisel`.

You can also inspect a specific command by passing its name as an argument to the help command (as with all other `LLDB` commands). 

```
(lldb) help border
Draws a border around <viewOrLayer>. Color and width can be optionally provided.

Arguments:
  <viewOrLayer>; Type: UIView*; The view to border.

Options:
  --color/-c <color>; Type: string; A color name such as 'red', 'green', 'magenta', etc.
  --width/-w <width>; Type: CGFloat; Desired width of border.

Syntax: border [--color=color] [--width=width] <viewOrLayer>
```

All of the commands provided by `Chisel` come with verbose help. Be sure to read it when in doubt!

## Custom Commands
You can add local, custom commands. Here's a contrived example.

```
#!/usr/bin/python
# Example file with custom commands, located at /magical/commands/example.py

import lldb
import fblldbbase as fb

def lldbcommands():
  return [ PrintKeyWindowLevel() ]
  
class PrintCurrentWindowLevel(fb.FBCommand):
  def name(self):
    return 'pkeywinlevel'
    
  def description(self):
    return 'An incredibly contrived command that prints the window level of the key window.'
    
  def run(self, arguments, options):
    # It's a good habit to explicitly cast the type of all return
    # values and arguments. LLDB can't always find them on its own.
    lldb.debugger.HandleCommand('p (CGFloat)[(id)[(id)[UIApplication sharedApplication] keyWindow] windowLevel]')
```

Then all that's left is to source the commands in lldbinit. `Chisel` has a python function just for this, _loadCommandsInDirectory_ in the _fblldb.py_ module.

```
# ~/.lldbinit
...
command source /path/to/fblldb.py
script fblldb.loadCommandsInDirectory('/magical/commands/')

```

There's also builtin support to make it super easy to specify the arguments and options that a command takes. See the _border_ and _pinvocation_ commands for example use.

## Development Workflow
Developing commands, whether for local use or contributing to `Chisel` directly, both follow the same workflow. Create a command as described in the [Custom Commands](#custom-commands) section and then

1. Start `LLDB`
2. Reach a breakpoint (or simply pause execution via the pause button in `Xcode`'s debug bar or `process interrupt` if attached directly)
3. Execute _command source ~/.lldbinit_ in `LLDB` to source the commands
4. Run the command you are working on
5. Modify the command
6. Repeat steps 3-5 until the command becomes a source of happiness

## Contributing
Please contribute any generic commands that you make. If it helps you then it will likely help many others! :D See `CONTRIBUTING.md` to learn how to contribute.

## License
`Chisel` is BSD-licensed. See `LICENSE`.
