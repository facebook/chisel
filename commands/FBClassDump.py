#!/usr/bin/python

# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import string

import fbchisellldbbase as fb
import fbchisellldbobjcruntimehelpers as runtimeHelpers


def lldbcommands():
    return [FBPrintMethods(), FBPrintProperties(), FBPrintBlock()]


class FBPrintMethods(fb.FBCommand):
    def name(self):
        return "pmethods"

    def description(self):
        return "Print the class and instance methods of a class."

    def options(self):
        return [
            fb.FBCommandArgument(
                short="-a",
                long="--address",
                arg="showaddr",
                help="Print the implementation address of the method",
                default=False,
                boolean=True,
            ),
            fb.FBCommandArgument(
                short="-i",
                long="--instance",
                arg="insmethod",
                help="Print the instance methods",
                default=False,
                boolean=True,
            ),
            fb.FBCommandArgument(
                short="-c",
                long="--class",
                arg="clsmethod",
                help="Print the class methods",
                default=False,
                boolean=True,
            ),
            fb.FBCommandArgument(
                short="-n",
                long="--name",
                arg="clsname",
                help="Take the argument as class name",
                default=False,
                boolean=True,
            ),
        ]

    def args(self):
        return [
            fb.FBCommandArgument(
                arg="instance or class",
                type="instance or Class",
                help="an Objective-C Class.",
            )
        ]

    def run(self, arguments, options):
        cls = getClassFromArgument(arguments[0], options.clsname)

        if options.clsmethod:
            print("Class Methods:")
            printClassMethods(cls, options.showaddr)

        if options.insmethod:
            print("\nInstance Methods:")
            printInstanceMethods(cls, options.showaddr)

        if not options.clsmethod and not options.insmethod:
            print("Class Methods:")
            printClassMethods(cls, options.showaddr)
            print("\nInstance Methods:")
            printInstanceMethods(cls, options.showaddr)


class FBPrintProperties(fb.FBCommand):
    def name(self):
        return "pproperties"

    def description(self):
        return "Print the properties of an instance or Class"

    def options(self):
        return [
            fb.FBCommandArgument(
                short="-n",
                long="--name",
                arg="clsname",
                help="Take the argument as class name",
                default=False,
                boolean=True,
            )
        ]

    def args(self):
        return [
            fb.FBCommandArgument(
                arg="instance or class",
                type="instance or Class",
                help="an Objective-C Class.",
            )
        ]

    def run(self, arguments, options):
        cls = getClassFromArgument(arguments[0], options.clsname)

        printProperties(cls)


class FBPrintBlock(fb.FBCommand):
    def name(self):
        return "pblock"

    def description(self):
        return "Print the block`s implementation address and signature"

    def args(self):
        return [
            fb.FBCommandArgument(arg="block", help="The block object you want to print")
        ]

    def run(self, arguments, options):
        block = arguments[0]

        # http://clang.llvm.org/docs/Block-ABI-Apple.html
        tmpString = """
        enum {
          BLOCK_HAS_COPY_DISPOSE =  (1 << 25),
          BLOCK_HAS_CTOR =          (1 << 26), // helpers have C++ code
          BLOCK_IS_GLOBAL =         (1 << 28),
          BLOCK_HAS_STRET =         (1 << 29), // IFF BLOCK_HAS_SIGNATURE
          BLOCK_HAS_SIGNATURE =     (1 << 30),
        };
        struct Block_literal_1 {
          void *isa; // initialized to &_NSConcreteStackBlock or &_NSConcreteGlobalBlock
          int flags;
          int reserved;
          void (*invoke)(void *, ...);
          struct Block_descriptor_1 {
              unsigned long int reserved; // NULL
              unsigned long int size;         // sizeof(struct Block_literal_1)
              // optional helper functions
              void (*copy_helper)(void *dst, void *src);     // IFF (1<<25)
              void (*dispose_helper)(void *src);             // IFF (1<<25)
              // required ABI.2010.3.16
              const char *signature;                         // IFF (1<<30)
          } *descriptor;
          // imported variables
        };
        struct Block_literal_1 real = *((__bridge struct Block_literal_1 *)$block);
        NSMutableDictionary *dict = (id)[NSMutableDictionary dictionary];
        
        [dict setObject:(id)[NSNumber numberWithLong:(long)real.invoke] forKey:@"invoke"];
        
        if (real.flags & BLOCK_HAS_SIGNATURE) {
          char *signature;
          if (real.flags & BLOCK_HAS_COPY_DISPOSE) {
              signature = (char *)(real.descriptor)->signature;
          } else {
              signature = (char *)(real.descriptor)->copy_helper;
          }

          NSMethodSignature *sig = [NSMethodSignature signatureWithObjCTypes:signature];
          NSMutableArray *types = [NSMutableArray array];

          [types addObject:(id)[NSString stringWithUTF8String:(char *)[sig methodReturnType]]];

          for (NSUInteger i = 0; i < sig.numberOfArguments; i++) {
              char *type = (char *)[sig getArgumentTypeAtIndex:i];
              [types addObject:(id)[NSString stringWithUTF8String:type]];
          }
          
          [dict setObject:types forKey:@"signature"];
        }
        
        RETURN(dict);
        """
        command = string.Template(tmpString).substitute(block=block)
        json = fb.evaluate(command)

        signature = json["signature"]
        if not signature:
            print("Imp: " + hex(json["invoke"]))
            return

        sigStr = "{} ^(".format(decode(signature[0]))
        # the block`s implementation always take the block as it`s first argument, so we ignore it
        sigStr += ", ".join([decode(m) for m in signature[2:]])
        sigStr += ");"

        print("Imp: " + hex(json["invoke"]) + "    Signature: " + sigStr)


# helpers
def isClassObject(arg):
    return runtimeHelpers.class_isMetaClass(runtimeHelpers.object_getClass(arg))


def getClassFromArgument(arg, is_classname):
    cls = arg
    if is_classname:
        cls = runtimeHelpers.objc_getClass(cls)
        if not int(cls, 16):
            raise Exception('Class "{}" not found'.format(arg))
    else:
        if not isClassObject(cls):
            cls = runtimeHelpers.object_getClass(cls)
            if not isClassObject(cls):
                raise Exception(
                    "Invalid argument. Please specify an instance or a Class."
                )

    return cls


def printInstanceMethods(cls, showaddr=False, prefix="-"):
    methods = getMethods(cls)
    if not methods:
        print("No methods were found")

    for m in methods:
        if showaddr:
            print(prefix + " " + m.prettyPrintString() + " " + str(m.imp))
        else:
            print(prefix + " " + m.prettyPrintString())


def printClassMethods(cls, showaddr=False):
    printInstanceMethods(runtimeHelpers.object_getClass(cls), showaddr, "+")


def printProperties(cls, showvalue=False):
    props = getProperties(cls)
    for p in props:
        print(p.prettyPrintString())


def decode(code):
    encodeMap = {
        "c": "char",
        "i": "int",
        "s": "short",
        "l": "long",
        "q": "long long",
        "C": "unsigned char",
        "I": "unsigned int",
        "S": "unsigned short",
        "L": "unsigned long",
        "Q": "unsigned long long",
        "f": "float",
        "d": "double",
        "B": "bool",
        "v": "void",
        "*": "char *",
        "@": "id",
        "#": "Class",
        ":": "SEL",
    }

    ret = code
    if code in encodeMap:
        ret = encodeMap[code]
    elif ret[0:1] == "@":
        if ret[1:2] == "?":  # @? represent a block
            ret = code
        elif ret[2:3] == "<":  # @"<aDelegate><bDelegate>"
            ret = "id" + ret[2:-1].replace("><", ", ")
        else:
            ret = ret[2:-1] + " *"
    elif ret[0:1] == "^":
        ret = decode(ret[1:]) + " *"

    return ret


# Notice that evaluateExpression doesn't work with variable arguments. such as -[NSString stringWithFormat:]
# I remove the "free(methods)" because it would cause evaluateExpressionValue to raise exception some time.
def getMethods(klass):
    tmpString = """
    unsigned int outCount;
    Method *methods = (Method *)class_copyMethodList((Class)$cls, &outCount);
    NSMutableArray *result = (id)[NSMutableArray array];
    
    for (int i = 0; i < outCount; i++) {
      NSMutableDictionary *m = (id)[NSMutableDictionary dictionary];

      SEL name = (SEL)method_getName(methods[i]);
      [m setObject:(id)NSStringFromSelector(name) forKey:@"name"];
      
      char * encoding = (char *)method_getTypeEncoding(methods[i]);
      [m setObject:(id)[NSString stringWithUTF8String:encoding] forKey:@"type_encoding"];
      
      NSMutableArray *types = (id)[NSMutableArray array];
      NSInteger args = (NSInteger)method_getNumberOfArguments(methods[i]);
      for (int idx = 0; idx < args; idx++) {
          char *type = (char *)method_copyArgumentType(methods[i], idx);
          [types addObject:(id)[NSString stringWithUTF8String:type]];
      }
      [m setObject:types forKey:@"parameters_type"];
      
      char *ret_type = (char *)method_copyReturnType(methods[i]);
      [m setObject:(id)[NSString stringWithUTF8String:ret_type] forKey:@"return_type"];
      
      long imp = (long)method_getImplementation(methods[i]);
      [m setObject:[NSNumber numberWithLongLong:imp] forKey:@"implementation"];
      
      [result addObject:m];
    }
    RETURN(result);
  """
    command = string.Template(tmpString).substitute(cls=klass)
    methods = fb.evaluate(command)
    return [Method(m) for m in methods]


class Method:
    def __init__(self, json):
        self.name = json["name"]
        self.type_encoding = json["type_encoding"]
        self.parameters_type = json["parameters_type"]
        self.return_type = json["return_type"]
        self.imp = self.toHex(json["implementation"])

    def prettyPrintString(self):
        argnum = len(self.parameters_type)
        names = self.name.split(":")

        # the argnum count must be bigger then 2, index 0 for self, index 1 for SEL
        for i in range(2, argnum):
            arg_type = self.parameters_type[i]
            names[i - 2] = names[i - 2] + ":(" + decode(arg_type) + ")arg" + str(i - 2)

        string = " ".join(names)
        return "({}){}".format(decode(self.return_type), string)

    def toHex(self, addr):
        return hex(addr)

    def __str__(self):
        return (
            "<Method:"
            + self.oc_method
            + "> "
            + self.name
            + " --- "
            + self.type
            + " --- "
            + self.imp
        )


def getProperties(klass):
    tmpString = """
      NSMutableArray *result = (id)[NSMutableArray array];
      unsigned int count;
      objc_property_t *props = (objc_property_t *)class_copyPropertyList((Class)$cls, &count);
      for (int i = 0; i < count; i++) {
          NSMutableDictionary *dict = (id)[NSMutableDictionary dictionary];
          
          char *name = (char *)property_getName(props[i]);
          [dict setObject:(id)[NSString stringWithUTF8String:name] forKey:@"name"];
          
          char *attrstr = (char *)property_getAttributes(props[i]);
          [dict setObject:(id)[NSString stringWithUTF8String:attrstr] forKey:@"attributes_string"];
          
          NSMutableDictionary *attrsDict = (id)[NSMutableDictionary dictionary];
          unsigned int pcount;
          objc_property_attribute_t *attrs = (objc_property_attribute_t *)property_copyAttributeList(props[i], &pcount);
          for (int i = 0; i < pcount; i++) {
              NSString *name = (id)[NSString stringWithUTF8String:(char *)attrs[i].name];
              NSString *value = (id)[NSString stringWithUTF8String:(char *)attrs[i].value];
              [attrsDict setObject:value forKey:name];
          }
          [dict setObject:attrsDict forKey:@"attributes"];
          
          [result addObject:dict];
      }
      RETURN(result);
    """
    command = string.Template(tmpString).substitute(cls=klass)
    propsJson = fb.evaluate(command)
    return [Property(m) for m in propsJson]


class Property:
    def __init__(self, json):
        self.name = json["name"]
        self.attributes_string = json["attributes_string"]
        self.attributes = json["attributes"]

    # https://developer.apple.com/library/mac/documentation/Cocoa/Conceptual/ObjCRuntimeGuide/Articles/ocrtPropertyIntrospection.html#//apple_ref/doc/uid/TP40008048-CH101-SW1
    def prettyPrintString(self):
        attrs = []
        if self.attributes.has_key("N"):
            attrs.append("nonatomic")
        else:
            attrs.append("atomic")

        if self.attributes.has_key("&"):
            attrs.append("strong")
        elif self.attributes.has_key("C"):
            attrs.append("copy")
        elif self.attributes.has_key("W"):
            attrs.append("weak")
        else:
            attrs.append("assign")

        if self.attributes.has_key("R"):
            attrs.append("readonly")

        if self.attributes.has_key("G"):
            attrs.append("getter={}".format(self.attributes["G"]))
        if self.attributes.has_key("S"):
            attrs.append("setter={}".format(self.attributes["S"]))

        return "@property ({}) {} {};".format(
            ", ".join(attrs), decode(self.attributes["T"]), self.name
        )
