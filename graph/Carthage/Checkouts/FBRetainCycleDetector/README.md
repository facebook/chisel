# FBRetainCycleDetector
[![Build Status](https://travis-ci.org/facebook/FBRetainCycleDetector.svg?branch=master)](https://travis-ci.org/facebook/FBRetainCycleDetector)
[![Carthage compatible](https://img.shields.io/badge/Carthage-compatible-4BC51D.svg?style=flat)](https://github.com/Carthage/Carthage)
[![CocoaPods](https://img.shields.io/cocoapods/v/FBRetainCycleDetector.svg?maxAge=2592000)]()
[![License](https://img.shields.io/cocoapods/l/FBRetainCycleDetector.svg)](https://github.com/facebook/FBRetainCycledetector/blob/master/LICENSE)

An iOS library that finds retain cycles using runtime analysis.

## About
Retain cycles are one of the most common ways of creating memory leaks. It's incredibly easy to create a retain cycle, and tends to be hard to spot it.
The goal of FBRetainCycleDetector is to help find retain cycles at runtime.
The features of this project were influenced by [Circle](https://github.com/mikeash/Circle).

## Installation

### Carthage

To your Cartfile add: 

    github "facebook/FBRetainCycleDetector"

`FBRetainCycleDetector` is built out from non-debug builds, so when you want to test it, use 

    carthage update --configuration Debug

### CocoaPods

To your podspec add:

    pod 'FBRetainCycleDetector'

You'll be able to use `FBRetainCycleDetector` fully only in `Debug` builds. This is controlled by [compilation flag](https://github.com/facebook/FBRetainCycleDetector/blob/master/FBRetainCycleDetector/Detector/FBRetainCycleDetector.h#L83) that can be provided to the build to make it work in other configurations.

## Example usage

Let's quickly dive in

```objc
#import <FBRetainCycleDetector/FBRetainCycleDetector.h>
```

```objc
FBRetainCycleDetector *detector = [FBRetainCycleDetector new];
[detector addCandidate:myObject];
NSSet *retainCycles = [detector findRetainCycles];
NSLog(@"%@", retainCycles);
```

`- (NSSet<NSArray<FBObjectiveCGraphElement *> *> *)findRetainCycles` will return a set of arrays of wrapped objects. It's pretty hard to look at at first, but let's go through it. Every array in this set will represent one retain cycle. Every element in this array is a wrapper around one object in this retain cycle. Check [FBObjectiveCGraphElement](https://github.com/facebook/FBRetainCycleDetector/blob/master/FBRetainCycleDetector/Graph/FBObjectiveCGraphElement.h).

Example output could look like this:
```
{(
    (
        "-> MyObject ",
        "-> _someObject -> __NSArrayI "
    )
)}
```
`MyObject` through `someObject` property retained `NSArray` that it was a part of.

FBRetainCycleDetector will look for cycles that are no longer than 10 objects.
We can make it bigger (although it's going to be slower!).

```objc
FBRetainCycleDetector *detector = [FBRetainCycleDetector new];
[detector addCandidate:myObject];
NSSet *retainCycles = [detector findRetainCyclesWithMaxCycleLength:100];
```

### Filters

There could also be retain cycles that we would like to omit. It's because not every retain cycle is a leak, and we might want to filter them out.
To do so we need to specify filters:

```objc
NSMutableArray *filters = @[
  FBFilterBlockWithObjectIvarRelation([UIView class], @"_subviewCache"),
];

// Configuration object can describe filters as well as some options
FBObjectGraphConfiguration *configuration =
[[FBObjectGraphConfiguration alloc] initWithFilterBlocks:filters
                                     shouldInspectTimers:YES];
FBRetainCycleDetector *detector = [[FBRetainCycleDetector alloc] initWithConfiguration:configuration];
[detector addCandidate:myObject];
NSSet *retainCycles = [detector findRetainCycles];
```

Every filter is a block that having two `FBObjectiveCGraphElement` objects can say, if their relation is valid.

Check [FBStandardGraphEdgeFilters](FBRetainCycleDetector/Filters/FBStandardGraphEdgeFilters.h) to learn more about how to use filters.

### NSTimer

NSTimer can be troublesome as it will retain it's target. Oftentimes it means a retain cycle. `FBRetainCycleDetector` can detect those,
but if you want to skip them, you can specify that in the configuration you are passing to `FBRetainCycleDetector`.

```objc
FBObjectGraphConfiguration *configuration =
[[FBObjectGraphConfiguration alloc] initWithFilterBlocks:someFilters
                                     shouldInspectTimers:NO];
FBRetainCycleDetector *detector = [[FBRetainCycleDetector alloc] initWithConfiguration:configuration];
```

### Associations

Objective-C let's us set associated objects for every object using [objc_setAssociatedObject](https://developer.apple.com/library/mac/documentation/Cocoa/Reference/ObjCRuntimeRef/#//apple_ref/c/func/objc_setAssociatedObject).

These associated objects can lead to retain cycles if we use retaining policies, like `OBJC_ASSOCIATION_RETAIN_NONATOMIC`. FBRetainCycleDetector can catch these kinds of cycles, but to do so we need to set it up. Early in the application's lifetime, preferably in `main.m` we can add this:

```objc
#import <FBRetainCycleDetector/FBAssociationManager.h>

int main(int argc, char * argv[]) {
  @autoreleasepool {
    [FBAssociationManager hook];
    return UIApplicationMain(argc, argv, nil, NSStringFromClass([AppDelegate class]));
  }
}
```

In the code above `[FBAssociationManager hook]` will use [fishhook](https://github.com/facebook/fishhook) to interpose functions `objc_setAssociatedObject` and `objc_resetAssociatedObjects` to track associations before they are made.

## Getting Candidates

If you want to profile your app, you might want to have an abstraction over how to get candidates for `FBRetainCycleDetector`. While you can simply track it your own, you can also use [FBAllocationTracker](https://github.com/facebook/FBAllocationTracker). It's a small tool we created that can help you track the objects. It offers simple API that you can query for example for all instances of given class, or all class names currently tracked, etc.

`FBAllocationTracker` and `FBRetainCycleDetector` can work nicely together. We have created a small example and drop-in project called [FBMemoryProfiler](https://github.com/facebook/FBMemoryProfiler) that leverages both these projects. It offers you very basic UI that you can use to track all allocations and force retain cycle detection from UI.

## Contributing
See the [CONTRIBUTING](CONTRIBUTING) file for how to help out.

## License
[`FBRetainCycleDetector` is BSD-licensed](LICENSE). We also provide an additional [patent grant](PATENTS).
