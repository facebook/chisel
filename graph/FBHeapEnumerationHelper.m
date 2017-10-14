// Copyright 2004-present Facebook. All Rights Reserved.

#if __has_feature(objc_arc)
#error FBHeapEnumerationHelper.m expects ARC to be disabled.
#endif

#import "FBHeapEnumerationHelper.h"

#import <objc/runtime.h>

#import <UIKit/UIKit.h>

#import <FBRetainCycleDetector/FBObjectGraphConfiguration.h>
#import <FBRetainCycleDetector/FBObjectiveCBlock.h>
#import <FBRetainCycleDetector/FBObjectiveCGraphElement.h>
#import <FBRetainCycleDetector/FBObjectiveCObject.h>
#import <FBRetainCycleDetector/FBRetainCycleUtils.h>
#import <FBRetainCycleDetectorExtension/CHLAllocationsDuplicate.h>
#import <FBRetainCycleDetectorExtension/CHLObjCObjectRecognizerDuplicate.h>
#import <FBRetainCycleDetectorExtension/FBObjectiveCGraph.h>
#import <FBRetainCycleDetectorExtension/FBObjectiveCGraphNode.h>
#import <malloc/malloc.h>

@implementation FBHeapEnumerationHelper

+ (NSArray<FBObjectiveCGraphElement *> *)wrappedElementsFromHeap:(FBObjectGraphConfiguration *)configuration
{
  NSMutableArray<FBObjectiveCGraphElement *> *elementArray = [NSMutableArray new];
  NSHashTable<FBObjectiveCGraphElement *> *deferredList = [NSHashTable weakObjectsHashTable];
  NSHashTable<FBObjectiveCGraphElement *> *pointeeList = [NSHashTable weakObjectsHashTable];

  CHLObjCObjectRecognizerDuplicate *validator = [CHLObjCObjectRecognizerDuplicate new];

  [validator checkStaticObjects:deferredList pointeeList:pointeeList];

  void (^enumerationBlock)(vm_range_t) = ^void(vm_range_t obj) {
    id tryObj = (id)obj.address;

    BOOL isValid = [validator examineRange:obj
                              deferredList:deferredList
                                 validList:pointeeList];
    if (isValid && [self isWhitelisted:tryObj]) {
      FBObjectiveCGraphElement *graphElement = FBWrapObjectGraphElement(nil, tryObj, configuration);
      [elementArray addObject:graphElement];
    }
  };

  duplicateCHLEnumerateAllocationsWithBlock(enumerationBlock);

  for (FBObjectiveCGraphElement *potentialElement in deferredList) {
    if ([self isWhitelisted:[potentialElement objectClass]]) {
      if ([pointeeList containsObject:potentialElement]) {
        [elementArray addObject:potentialElement];
      }
    }
  }

  return elementArray;
}

+ (BOOL)isWhitelisted:(id)object
{
  Class class = object_getClass(object);
  NSString *className = NSStringFromClass(class);

  if (!className
      || ![class isSubclassOfClass:[NSObject class]]
      || [className isEqualToString:@""]
      || [className length] == 0
      || [class isSubclassOfClass:NSClassFromString(@"__ARCLite__")]
      || [class isSubclassOfClass:NSClassFromString(@"NSCFTimer")]
      || [class isSubclassOfClass:NSClassFromString(@"__NSCFTimer")]
      || [class isSubclassOfClass:[FBObjectiveCObject class]]
      || [class isSubclassOfClass:[FBObjectiveCBlock class]]
      || [class isSubclassOfClass:[FBObjectiveCGraphNode class]]
      || [class isSubclassOfClass:[FBObjectGraphConfiguration class]]
      || [class isSubclassOfClass:[FBObjectiveCGraphElement class]]
      ) {
    return NO;
  }
  return YES;
}

@end
