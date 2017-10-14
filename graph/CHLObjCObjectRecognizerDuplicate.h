// Copyright 2004-present Facebook. All Rights Reserved.

#import <Foundation/Foundation.h>

#import <FBBaseLite/FBBaseDefines.h>
#import <FBRetainCycleDetector/FBObjectiveCGraphElement.h>
#import <malloc/malloc.h>

FB_EXTERN_C_BEGIN

@interface CHLObjCObjectRecognizerDuplicate : NSObject

/**
 This will do basic validation of the object on the following criteria:
 - Exists in the set of all classes at runtime
 - Correct instance size
 - Correct alloc usage
 And also checks all of its ivars on the same criteria.

 We will defer the checks by wrapping them and later checking them against static or pointee variables.
 */
- (BOOL)examineRange:(vm_range_t)range
        deferredList:(NSHashTable<FBObjectiveCGraphElement *> *)deferredList
           validList:(NSHashTable<FBObjectiveCGraphElement *> *)validList;


/**
 This will help us verify later whether or not a deferred object was statically referenced
 */
- (void)checkStaticObjects:(NSHashTable<FBObjectiveCGraphElement *> *)deferredList
               pointeeList:(NSHashTable<FBObjectiveCGraphElement *> *)pointeeList;

@end


FB_EXTERN_C_END
