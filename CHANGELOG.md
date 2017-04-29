# Change Log

## [Unreleased](https://github.com/facebook/chisel/tree/HEAD)

[Full Changelog](https://github.com/facebook/chisel/compare/1.2.0...HEAD)

**Implemented enhancements:**

- Add target/action commands [\#59](https://github.com/facebook/chisel/issues/59)

**Fixed bugs:**

- bmessage: Consult skip-prologue setting on x86 [\#89](https://github.com/facebook/chisel/issues/89)

- 'vs' command broken? [\#88](https://github.com/facebook/chisel/issues/88)

**Closed issues:**

- Adding ComponentKit's debugging commands to Chisel [\#85](https://github.com/facebook/chisel/issues/85)

- Update homebrew formula [\#82](https://github.com/facebook/chisel/issues/82)

**Merged pull requests:**

- Add `pactions` command to print the target/actions of a UIControl [\#95](https://github.com/facebook/chisel/pull/95) ([kastiglione](https://github.com/kastiglione))

- pep8; removed unused vars [\#93](https://github.com/facebook/chisel/pull/93) ([aledista](https://github.com/aledista))

- Fixed ‘vs’ command by: [\#92](https://github.com/facebook/chisel/pull/92) ([palcalde](https://github.com/palcalde))

- Don't skip prologue for `bmessage` breakpoints [\#90](https://github.com/facebook/chisel/pull/90) ([kastiglione](https://github.com/kastiglione))

- add ppath command [\#72](https://github.com/facebook/chisel/pull/72) ([dopcn](https://github.com/dopcn))

## [1.2.0](https://github.com/facebook/chisel/tree/1.2.0) (2015-03-26)

[Full Changelog](https://github.com/facebook/chisel/compare/1.1.0...1.2.0)

**Implemented enhancements:**

- Detect if debugging an iOS or Mac app and use NSView vs UIView appropriately. [\#34](https://github.com/facebook/chisel/issues/34)

**Fixed bugs:**

- command 'mask' always get wrong [\#63](https://github.com/facebook/chisel/issues/63)

- libobjc required [\#47](https://github.com/facebook/chisel/issues/47)

- pvc doesn't work when running on 64-bit devices [\#46](https://github.com/facebook/chisel/issues/46)

- The mask command breaks if the orientation is portrait upside down. [\#26](https://github.com/facebook/chisel/issues/26)

**Closed issues:**

- border <view\> not working on osx [\#81](https://github.com/facebook/chisel/issues/81)

- Mine painter crash [\#71](https://github.com/facebook/chisel/issues/71)

- bmessage breakpoints fail on methods defined in categories [\#57](https://github.com/facebook/chisel/issues/57)

- pviews output incorrectly [\#44](https://github.com/facebook/chisel/issues/44)

- Tag new release and upgrade Homebrew formula [\#39](https://github.com/facebook/chisel/issues/39)

- Install instructions from `brew` misses information [\#37](https://github.com/facebook/chisel/issues/37)

- show{view,layer...} could not work, didi i miss something? [\#27](https://github.com/facebook/chisel/issues/27)

**Merged pull requests:**

- Add pcomponents/dcomponents/rcomponents for debugging in ComponentKit [\#86](https://github.com/facebook/chisel/pull/86) ([natansh](https://github.com/natansh))

- Add pdata command to print content of NSData object. [\#83](https://github.com/facebook/chisel/pull/83) ([bartoszj](https://github.com/bartoszj))

- Fixed incorrect usage of global foundElement causing crashes in some searches [\#76](https://github.com/facebook/chisel/pull/76) ([gkassabli](https://github.com/gkassabli))

- Fix spelling error in README [\#75](https://github.com/facebook/chisel/pull/75) ([wincent](https://github.com/wincent))

- Added print accessibility tree command. Find accessibility element command reworked [\#70](https://github.com/facebook/chisel/pull/70) ([gkassabli](https://github.com/gkassabli))

- support x86\_64h [\#69](https://github.com/facebook/chisel/pull/69) ([samjohn](https://github.com/samjohn))

- Add basic Swift support \(requires Xcode 6\) [\#68](https://github.com/facebook/chisel/pull/68) ([mblsha](https://github.com/mblsha))

- Added 'slow' command. [\#67](https://github.com/facebook/chisel/pull/67) ([bartoszj](https://github.com/bartoszj))

- Add reload tip to Development Workflow [\#65](https://github.com/facebook/chisel/pull/65) ([kastiglione](https://github.com/kastiglione))

- Fix mask: tweak casting within mask implementation [\#64](https://github.com/facebook/chisel/pull/64) ([kastiglione](https://github.com/kastiglione))

- Implement pvc with +\[UIViewController \_printHierarchy\] [\#61](https://github.com/facebook/chisel/pull/61) ([kastiglione](https://github.com/kastiglione))

- Add "Dancing in the Debugger" link to README [\#60](https://github.com/facebook/chisel/pull/60) ([kastiglione](https://github.com/kastiglione))

- bmessage: use regex breakpoint to match category [\#58](https://github.com/facebook/chisel/pull/58) ([kastiglione](https://github.com/kastiglione))

- Remove references to Ivar [\#56](https://github.com/facebook/chisel/pull/56) ([kastiglione](https://github.com/kastiglione))

- pkp: po alternative to lookup via valueForKeyPath: [\#53](https://github.com/facebook/chisel/pull/53) ([KingOfBrian](https://github.com/KingOfBrian))

- PEP 8 \(mostly\) [\#52](https://github.com/facebook/chisel/pull/52) ([kastiglione](https://github.com/kastiglione))

- fix alamborder - missing import [\#51](https://github.com/facebook/chisel/pull/51) ([haikusw](https://github.com/haikusw))

- Add support for setting breakpoints in a library by file address [\#49](https://github.com/facebook/chisel/pull/49) ([mmmulani](https://github.com/mmmulani))

- OS X Support \(for major commands\)  [\#45](https://github.com/facebook/chisel/pull/45) ([kolinkrewinkel](https://github.com/kolinkrewinkel))

- Add bordering / unbordering Auto Layout ambiguous views commands [\#43](https://github.com/facebook/chisel/pull/43) ([mattjgalloway](https://github.com/mattjgalloway))

- Cast things and use UIApplication to get the keyWindow [\#42](https://github.com/facebook/chisel/pull/42) ([mattjgalloway](https://github.com/mattjgalloway))

- Add depth parameter to pviews [\#41](https://github.com/facebook/chisel/pull/41) ([mattjgalloway](https://github.com/mattjgalloway))

- Add Auto Layout trace command [\#40](https://github.com/facebook/chisel/pull/40) ([mattjgalloway](https://github.com/mattjgalloway))

## [1.1.0](https://github.com/facebook/chisel/tree/1.1.0) (2014-03-31)

[Full Changelog](https://github.com/facebook/chisel/compare/1.0.0...1.1.0)

**Implemented enhancements:**

- Merge `show{view,layer,image,imageref}` into `visualize` [\#17](https://github.com/facebook/chisel/issues/17)

**Closed issues:**

- 123456789 [\#33](https://github.com/facebook/chisel/issues/33)

- Can't install chisel [\#30](https://github.com/facebook/chisel/issues/30)

- Preview not show up [\#24](https://github.com/facebook/chisel/issues/24)

- Doesn't seem to work for me [\#14](https://github.com/facebook/chisel/issues/14)

- 'import' is not a valid command [\#9](https://github.com/facebook/chisel/issues/9)

- Installation issues [\#5](https://github.com/facebook/chisel/issues/5)

**Merged pull requests:**

- Update README.md [\#38](https://github.com/facebook/chisel/pull/38) ([dstnbrkr](https://github.com/dstnbrkr))

- Changed regex handling for commands fv/fvc [\#32](https://github.com/facebook/chisel/pull/32) ([sgl0v](https://github.com/sgl0v))

- Update README.md [\#31](https://github.com/facebook/chisel/pull/31) ([dstnbrkr](https://github.com/dstnbrkr))

- Add upwards option to pviews command [\#29](https://github.com/facebook/chisel/pull/29) ([mattjgalloway](https://github.com/mattjgalloway))

- fix bug in example defining a custom command [\#28](https://github.com/facebook/chisel/pull/28) ([algal](https://github.com/algal))

- Merged show{view,layer,image,imageref} into visualize [\#25](https://github.com/facebook/chisel/pull/25) ([antons](https://github.com/antons))

- Add homebrew instructions [\#23](https://github.com/facebook/chisel/pull/23) ([dstnbrkr](https://github.com/dstnbrkr))

- Fixed issues which prevented show view and layer commands from working on 64 bits [\#22](https://github.com/facebook/chisel/pull/22) ([antons](https://github.com/antons))

- Added commands to show NSData as string and image [\#20](https://github.com/facebook/chisel/pull/20) ([soniccat](https://github.com/soniccat))

- Cast the border/unborder width input to CGFloat [\#19](https://github.com/facebook/chisel/pull/19) ([JJSaccolo](https://github.com/JJSaccolo))

- Added Find Owning View Controller command [\#13](https://github.com/facebook/chisel/pull/13) ([jkubicek](https://github.com/jkubicek))

- showview command uses a category method [\#11](https://github.com/facebook/chisel/pull/11) ([bencochran](https://github.com/bencochran))

- Added syntax highlighting to code blocks in README [\#10](https://github.com/facebook/chisel/pull/10) ([Ashton-W](https://github.com/Ashton-W))

- Check vc is not nil to prevent infinite recursion [\#8](https://github.com/facebook/chisel/pull/8) ([simonwhitaker](https://github.com/simonwhitaker))

- Updated with correct installation instructions. Closes \#5 [\#6](https://github.com/facebook/chisel/pull/6) ([RichardSimko](https://github.com/RichardSimko))

- Added taplog command. [\#4](https://github.com/facebook/chisel/pull/4) ([VTopoliuk](https://github.com/VTopoliuk))

- Remove pyc files and add gitignore to ignore any future pyc files [\#3](https://github.com/facebook/chisel/pull/3) ([mattjgalloway](https://github.com/mattjgalloway))

## [1.0.0](https://github.com/facebook/chisel/tree/1.0.0) (2014-03-05)

**Merged pull requests:**

- Make {un,}border work on views and layer expressions [\#1](https://github.com/facebook/chisel/pull/1) ([kastiglione](https://github.com/kastiglione))



\* *This Change Log was automatically generated by [github_changelog_generator](https://github.com/skywinder/Github-Changelog-Generator)*