# Chisel
`Chisel` is a collection of `LLDB` commands to assist in the debugging of iOS apps.

[[Installation](#installation) &bull; [Commands](#commands) &bull; [Custom Commands](#custom-commands) &bull; [Development Workflow](#development-workflow) [Contributing](#contributing) &bull; [License](#license)]

For a comprehensive overview of LLDB, and how Chisel complements it, read Ari Grant's [Dancing in the Debugger — A Waltz with LLDB](http://www.objc.io/issue-19/lldb-debugging.html) in issue 19 of [objc.io](http://www.objc.io/).

## Installation

```shell
brew update
brew install chisel
```

if `.lldbinit` file doesn't exist you can create it & open it by tapping on the terminal

 ```shell
 touch .lldbinit 
 open .lldbinit 
```

Then add the following line to your `~/.lldbinit` file.

```Python
# ~/.lldbinit
...
command script import /usr/local/opt/chisel/libexec/fblldb.py
```

Alternatively, download chisel and add the following line to your _~/.lldbinit_ file.

```Python
# ~/.lldbinit
...
command script import /path/to/fblldb.py

```

The commands will be available the next time `Xcode` starts.

## Commands
There are many commands; here's a few:
*(Compatibility with iOS/Mac indicated at right)*

|Command          |Description     |iOS    |OS X   |
|-----------------|----------------|-------|-------|
|pviews           |Print the recursive view description for the key window.|Yes|Yes|
|pvc              |Print the recursive view controller description for the key window.|Yes|No|
|visualize        |Open a `UIImage`, `CGImageRef`, `UIView`, `CALayer`, `NSData` (of an image), `UIColor`, `CIColor`, or `CGColorRef` in Preview.app on your Mac.|Yes|No|
|fv               |Find a view in the hierarchy whose class name matches the provided regex.|Yes|No|
|fvc              |Find a view controller in the hierarchy whose class name matches the provided regex.|Yes|No|
|show/hide        |Show or hide the given view or layer. You don't even have to continue the process to see the changes!|Yes|Yes|
|mask/unmask      |Overlay a view or layer with a transparent rectangle to visualize where it is.|Yes|No|
|border/unborder  |Add a border to a view or layer to visualize where it is.|Yes|Yes|
|caflush          |Flush the render server (equivalent to a "repaint" if no animations are in-flight).|Yes|Yes|
|bmessage         |Set a symbolic breakpoint on the method of a class or the method of an instance without worrying which class in the hierarchy actually implements the method.|Yes|Yes|
|wivar            |Set a watchpoint on an instance variable of an object.|Yes|Yes|
|presponder       |Print the responder chain starting from the given object.|Yes|Yes|
|...              |... and many more!|

To see the list of **all** of the commands execute the help command in `LLDB` or go to the [Wiki](https://github.com/facebook/chisel/wiki).

```Python
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

```python
#!/usr/bin/python
# Example file with custom commands, located at /magical/commands/example.py

import lldb
import fblldbbase as fb

def lldbcommands():
  return [ PrintKeyWindowLevel() ]
  
class PrintKeyWindowLevel(fb.FBCommand):
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

```Python
# ~/.lldbinit
...
command script import /path/to/fblldb.py
script fblldb.loadCommandsInDirectory('/magical/commands/')

```

There's also builtin support to make it super easy to specify the arguments and options that a command takes. See the _border_ and _pinvocation_ commands for example use.

## Development Workflow
Developing commands, whether for local use or contributing to `Chisel` directly, both follow the same workflow. Create a command as described in the [Custom Commands](#custom-commands) section and then

1. Start `LLDB`
2. Reach a breakpoint (or simply pause execution via the pause button in `Xcode`'s debug bar or `process interrupt` if attached directly)
3. Execute `command source ~/.lldbinit` in LLDB to source the commands
4. Run the command you are working on
5. Modify the command
6. Optionally run `script reload(modulename)`
7. Repeat steps 3-6 until the command becomes a source of happiness

## Contributing
Please contribute any generic commands that you make. If it helps you then it will likely help many others! :D See `CONTRIBUTING.md` to learn how to contribute.

## License
`Chisel` is BSD-licensed. See `LICENSE`.
