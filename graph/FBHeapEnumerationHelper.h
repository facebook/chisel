// Copyright 2004-present Facebook. All Rights Reserved.

#import <Foundation/Foundation.h>

#import <FBRetainCycleDetector/FBObjectGraphConfiguration.h>
#import <FBRetainCycleDetector/FBObjectiveCGraphElement.h>
#import <FBRetainCycleDetectorExtension/FBObjectiveCGraphNode.h>

/**
 Helper to prevent objects from being retained when wrapped as FBObjectiveCGraphElements
 */
@interface FBHeapEnumerationHelper : NSObject

/**
 Returns a set of objects wrapped as FBObjectiveCGraphElements
 */
+ (NSArray<FBObjectiveCGraphElement *> *)wrappedElementsFromHeap:(FBObjectGraphConfiguration *)configuration;

@end
