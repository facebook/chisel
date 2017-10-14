/**
 * Copyright (c) 2016-present, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

#import <UIKit/UIKit.h>
#import <XCTest/XCTest.h>

#import <FBRetainCycleDetector/FBObjectiveCBlock.h>
#import <FBRetainCycleDetector/FBObjectiveCGraphElement+Internal.h>
#import <FBRetainCycleDetector/FBObjectiveCObject.h>
#import <FBRetainCycleDetector/FBRetainCycleDetector+Internal.h>

typedef void (^_RCDTestBlockType)();

typedef struct {
  id<NSObject> model;
  __weak id<NSObject> weakModel;
} _RCDTestStruct;

@interface _RCDTestClass : NSObject
@property (nonatomic, strong) NSObject *object;
@property (nonatomic, strong) NSObject *secondObject;
@property (nonatomic, copy) NSArray *array;
@property (nonatomic, weak) NSObject *weakObject;
@property (nonatomic, strong) _RCDTestBlockType block;
@property (nonatomic, assign) _RCDTestStruct someStruct;
@end
@implementation _RCDTestClass
@end

@interface _RCDTestSubclass : _RCDTestClass
@end
@implementation _RCDTestSubclass
@end

@interface _RCDTestGraphElement : FBObjectiveCGraphElement
- (instancetype)initWithObject:(id)object
                  fakedAddress:(size_t)address
                     className:(NSString *)className;
@end

@implementation _RCDTestGraphElement
{
  size_t _address;
  FBObjectiveCObject *_object;
  NSString *_className;
}

- (instancetype)initWithObject:(id)object
                  fakedAddress:(size_t)address
                     className:(NSString *)className
{
  if (self = [super init]) {
    _address = address;
    _object = [[FBObjectiveCObject alloc] initWithObject:object];
    _className = className;
  }

  return self;
}

- (NSSet *)allRetainedObjects
{
  return [_object allRetainedObjects];
}

- (size_t)objectAddress
{
  return _address;
}

- (NSString *)classNameOrNull
{
  return _className;
}

- (Class)objectClass
{
  return nil;
}

@end

@interface FBRetainCycleDetectorTests : XCTestCase
@end

@implementation FBRetainCycleDetectorTests

#if _INTERNAL_RCD_ENABLED

- (void)testThatDetectorWillFindNoCyclesInEmptyObject
{
  _RCDTestClass *testObject = [_RCDTestClass new];
  FBRetainCycleDetector *detector = [FBRetainCycleDetector new];
  [detector addCandidate:testObject];
  NSSet *retainCycles = [detector findRetainCycles];

  XCTAssertEqual([retainCycles count], 0);
}

- (void)testThatDetectorWillFindCycleCreatedByOneObjectWithItself
{
  _RCDTestClass *testObject = [_RCDTestClass new];
  testObject.object = testObject;

  FBRetainCycleDetector *detector = [FBRetainCycleDetector new];
  [detector addCandidate:testObject];
  NSSet *retainCycles = [detector findRetainCycles];

  NSSet *expectedSet = [NSSet setWithObject:@[[[FBObjectiveCObject alloc] initWithObject:testObject]]];

  XCTAssertEqualObjects(retainCycles, expectedSet);
}

- (void)testThatDetectorWillFindNoCycleIfOneIsUsingWeakProperty
{
  _RCDTestClass *testObject = [_RCDTestClass new];
  testObject.weakObject = testObject;

  FBRetainCycleDetector *detector = [FBRetainCycleDetector new];
  [detector addCandidate:testObject];
  NSSet *retainCycles = [detector findRetainCycles];

  XCTAssertEqual([retainCycles count], 0);
}

/**
    1 -> 2 -> 3
    ^         |
    \_________/
 */
- (void)testThatDetectorWillFindCycleBetweenThreeElements
{
  _RCDTestClass *testObject1 = [_RCDTestClass new];
  _RCDTestClass *testObject2 = [_RCDTestClass new];
  _RCDTestClass *testObject3 = [_RCDTestClass new];

  testObject1.object = testObject2;
  testObject2.object = testObject3;
  testObject3.object = testObject1;

  FBRetainCycleDetector *detector = [FBRetainCycleDetector new];
  [detector addCandidate:testObject1];
  NSSet *retainCycles = [detector findRetainCycles];

  NSSet *expectedSet = [NSSet setWithObject:[detector _shiftToUnifiedCycle:
                                              @[[[FBObjectiveCObject alloc] initWithObject:testObject1],
                                                [[FBObjectiveCObject alloc] initWithObject:testObject2],
                                                [[FBObjectiveCObject alloc] initWithObject:testObject3],
                                                ]]];

  XCTAssertEqualObjects(retainCycles, expectedSet);
}

/**
 The following example could technically be tricky with illed implemented DFS.
         1
        / \
       /   \
      2 <-- 3
 */
- (void)testThatDetectorWillFindNoCycleIfObjectsWithCommonParentReferThemselves
{
  _RCDTestClass *testObject1 = [_RCDTestClass new];
  _RCDTestClass *testObject2 = [_RCDTestClass new];
  _RCDTestClass *testObject3 = [_RCDTestClass new];
  testObject1.object = testObject2;
  testObject1.secondObject = testObject3;
  testObject3.object = testObject2;

  FBRetainCycleDetector *detector = [FBRetainCycleDetector new];
  [detector addCandidate:testObject1];
  NSSet *retainCycles = [detector findRetainCycles];

  XCTAssertEqual([retainCycles count], 0);
}

- (void)testThatDetectorWillFindCycleIfArrayIsPartOfIt
{
  _RCDTestClass *testObject = [_RCDTestClass new];
  NSArray *array = @[testObject];
  testObject.array = array;

  FBRetainCycleDetector *detector = [FBRetainCycleDetector new];
  [detector addCandidate:testObject];
  NSSet *retainCycles = [detector findRetainCycles];

  NSSet *expectedSet = [NSSet setWithObject:[detector _shiftToUnifiedCycle:
                                              @[[[FBObjectiveCObject alloc] initWithObject:testObject],
                                                [[FBObjectiveCObject alloc] initWithObject:array]]]];

  XCTAssertEqualObjects(retainCycles, expectedSet);
}

- (void)testThatDetectorWillFindCycleIfCandidateIsNotPartOfTheCycle
{
  _RCDTestClass *testObjectThatWontBePartOfRetainCycle = [_RCDTestClass new];

  _RCDTestClass *testObject1 = [_RCDTestClass new];
  _RCDTestClass *testObject2 = [_RCDTestClass new];
  _RCDTestClass *testObject3 = [_RCDTestClass new];

  testObjectThatWontBePartOfRetainCycle.object = testObject1;
  testObject1.object = testObject2;
  testObject2.object = testObject3;
  testObject3.object = testObject1;

  FBRetainCycleDetector *detector = [FBRetainCycleDetector new];
  [detector addCandidate:testObjectThatWontBePartOfRetainCycle];
  NSSet *retainCycles = [detector findRetainCycles];

  NSSet *expectedSet = [NSSet setWithObject:[detector _shiftToUnifiedCycle:
                                              @[[[FBObjectiveCObject alloc] initWithObject:testObject1],
                                                [[FBObjectiveCObject alloc] initWithObject:testObject2],
                                                [[FBObjectiveCObject alloc] initWithObject:testObject3]]]];

  XCTAssertEqualObjects(retainCycles, expectedSet);
}

- (void)testThatDetectorWillFindCycleIfDictionaryIsPartOfIt
{
  _RCDTestClass *testObject = [_RCDTestClass new];
  NSDictionary *dictionary = @{@"irrelevantKey": testObject};
  testObject.object = dictionary;

  FBRetainCycleDetector *detector = [FBRetainCycleDetector new];
  [detector addCandidate:testObject];
  NSSet *retainCycles = [detector findRetainCycles];

  NSSet *expectedSet = [NSSet setWithObject:[detector _shiftToUnifiedCycle:
                                              @[[[FBObjectiveCObject alloc] initWithObject:testObject],
                                                [[FBObjectiveCObject alloc] initWithObject:dictionary]]]];

  XCTAssertEqualObjects(retainCycles, expectedSet);
}

- (void)testThatDetectorWillFindAllCyclesIfCandidateIsPartOfMoreThanOneCycle
{
  _RCDTestClass *testObject1 = [_RCDTestClass new];
  _RCDTestClass *testObject2 = [_RCDTestClass new];
  _RCDTestClass *testObject3 = [_RCDTestClass new];

  testObject1.object = testObject2;
  testObject1.secondObject = testObject3;
  testObject2.object = testObject1;
  testObject3.object = testObject1;

  FBRetainCycleDetector *detector = [FBRetainCycleDetector new];
  [detector addCandidate:testObject1];
  NSSet *retainCycles = [detector findRetainCycles];

  NSArray *firstCycle = [detector _shiftToUnifiedCycle:
                         @[[[FBObjectiveCObject alloc] initWithObject:testObject1],
                           [[FBObjectiveCObject alloc] initWithObject:testObject2]]];
  NSArray *secondCycle = [detector _shiftToUnifiedCycle:
                          @[[[FBObjectiveCObject alloc] initWithObject:testObject1],
                            [[FBObjectiveCObject alloc] initWithObject:testObject3]]];

  XCTAssertTrue([retainCycles containsObject:firstCycle]);
  XCTAssertTrue([retainCycles containsObject:secondCycle]);
}

/**
       /---> 1 <----\
       |    / \     |
       |   /   3 -->|
       |  2 <-
       | / \  \
       |/   \  \
       4     5  \
            / \ |
           /   \|
          6     7
 3 cycles:
 1-2-4-1
 2-5-7-2
 1-3-1
 */
- (void)testThatDetectorWillFindAllCyclesInMoreComplicatedObjectGraph
{
  _RCDTestClass *testObject1 = [_RCDTestClass new];
  _RCDTestClass *testObject2 = [_RCDTestClass new];
  _RCDTestClass *testObject3 = [_RCDTestClass new];
  _RCDTestClass *testObject4 = [_RCDTestClass new];
  _RCDTestClass *testObject5 = [_RCDTestClass new];
  _RCDTestClass *testObject6 = [_RCDTestClass new];
  _RCDTestClass *testObject7 = [_RCDTestClass new];

  testObject1.object = testObject2;
  testObject1.secondObject = testObject3;
  testObject2.object = testObject4;
  testObject2.secondObject = testObject5;
  testObject5.object = testObject6;
  testObject5.secondObject = testObject7;

  // Cycling
  testObject3.object = testObject1;
  testObject4.object = testObject1;
  testObject7.object = testObject2;

  FBRetainCycleDetector *detector = [FBRetainCycleDetector new];
  [detector addCandidate:testObject1];
  NSSet *retainCycles = [detector findRetainCycles];

  NSArray *firstCycle = [detector _shiftToUnifiedCycle:
                         @[[[FBObjectiveCObject alloc] initWithObject:testObject1],
                           [[FBObjectiveCObject alloc] initWithObject:testObject2],
                           [[FBObjectiveCObject alloc] initWithObject:testObject4]]];
  NSArray *secondCycle = [detector _shiftToUnifiedCycle:
                          @[[[FBObjectiveCObject alloc] initWithObject:testObject2],
                            [[FBObjectiveCObject alloc] initWithObject:testObject5],
                            [[FBObjectiveCObject alloc] initWithObject:testObject7]]];
  NSArray *thirdCycle = [detector _shiftToUnifiedCycle:
                         @[[[FBObjectiveCObject alloc] initWithObject:testObject1],
                           [[FBObjectiveCObject alloc] initWithObject:testObject3]]];

  XCTAssertTrue([retainCycles containsObject:firstCycle]);
  XCTAssertTrue([retainCycles containsObject:secondCycle]);
  XCTAssertTrue([retainCycles containsObject:thirdCycle]);
}

- (void)testThatDetectorWillFindCycleWithFewCollectionsMixedInIt
{
  _RCDTestClass *testObject = [_RCDTestClass new];
  NSArray *array = @[testObject];
  NSSet *set = [NSSet setWithObject:array];
  NSDictionary *dictionary = @{@"set": set};
  testObject.object = dictionary;

  FBRetainCycleDetector *detector = [FBRetainCycleDetector new];
  [detector addCandidate:set];
  NSSet *retainCycles = [detector findRetainCycles];

  NSSet *expectedSet = [NSSet setWithObject:[detector _shiftToUnifiedCycle:
                                              @[[[FBObjectiveCObject alloc] initWithObject:set],
                                                [[FBObjectiveCObject alloc] initWithObject:array],
                                                [[FBObjectiveCObject alloc] initWithObject:testObject],
                                                [[FBObjectiveCObject alloc] initWithObject:dictionary]]]];

  XCTAssertEqualObjects(retainCycles, expectedSet);
}

- (void)testThatDetectorWillFindAllCyclesThatArrayIsPartOf
{
  _RCDTestClass *testObject1 = [_RCDTestClass new];
  _RCDTestClass *testObject2 = [_RCDTestClass new];
  NSArray *array = @[testObject1, testObject2];
  testObject1.object = array;
  testObject2.object = array;

  FBRetainCycleDetector *detector = [FBRetainCycleDetector new];
  [detector addCandidate:testObject1];
  NSSet *retainCycles = [detector findRetainCycles];

  NSArray *firstCycle = [detector _shiftToUnifiedCycle:
                         @[[[FBObjectiveCObject alloc] initWithObject:testObject1],
                           [[FBObjectiveCObject alloc] initWithObject:array]]];
  NSArray *secondCycle = [detector _shiftToUnifiedCycle:
                         @[[[FBObjectiveCObject alloc] initWithObject:array],
                           [[FBObjectiveCObject alloc] initWithObject:testObject2]]];

  XCTAssertTrue([retainCycles containsObject:firstCycle]);
  XCTAssertTrue([retainCycles containsObject:secondCycle]);
}

- (void)testThatDetectorWillFindOnlyOneRetainCycleIfArrayRefersToSameObjectTwice
{
  _RCDTestClass *testObject = [_RCDTestClass new];
  NSArray *array = @[testObject, testObject];
  testObject.object = array;

  FBRetainCycleDetector *detector = [FBRetainCycleDetector new];
  [detector addCandidate:testObject];
  NSSet *retainCycles = [detector findRetainCycles];

  NSSet *expectedSet = [NSSet setWithObject:[detector _shiftToUnifiedCycle:
                                       @[[[FBObjectiveCObject alloc] initWithObject:testObject],
                                         [[FBObjectiveCObject alloc] initWithObject:array]]]];

  XCTAssertEqualObjects(retainCycles, expectedSet);
}

// Negative Tests

/**
     1
    / \
   2   3
    \ /
     4
 */
- (void)testThatDetectorWillNotFindCycleInDiamondDAG
{
  _RCDTestClass *testObject1 = [_RCDTestClass new];
  _RCDTestClass *testObject2 = [_RCDTestClass new];
  _RCDTestClass *testObject3 = [_RCDTestClass new];
  _RCDTestClass *testObject4 = [_RCDTestClass new];

  testObject1.object = testObject2;
  testObject1.secondObject = testObject3;
  testObject2.object = testObject4;
  testObject3.object = testObject4;

  FBRetainCycleDetector *detector = [FBRetainCycleDetector new];
  [detector addCandidate:testObject1];
  NSSet *retainCycles = [detector findRetainCycles];

  XCTAssertEqual([retainCycles count], 0);
}

- (void)testThatDetectorWillNotFindCycleInCommonDelegationPattern
{
  _RCDTestClass *testObject1 = [_RCDTestClass new];
  _RCDTestClass *testObject2 = [_RCDTestClass new];

  testObject1.object = testObject2;
  testObject2.weakObject = testObject1;

  FBRetainCycleDetector *detector = [FBRetainCycleDetector new];
  [detector addCandidate:testObject1];
  NSSet *retainCycles = [detector findRetainCycles];

  XCTAssertEqual([retainCycles count], 0);
}

- (void)testThatDetectorWillNotFindCycleWhenObjectIsWrappedInNSValue
{
  _RCDTestClass *testObject = [_RCDTestClass new];
  NSValue *value = [NSValue valueWithNonretainedObject:testObject];
  testObject.object = value;

  FBRetainCycleDetector *detector = [FBRetainCycleDetector new];
  [detector addCandidate:testObject];
  NSSet *retainCycles = [detector findRetainCycles];

  XCTAssertEqual([retainCycles count], 0);
}

// Blocks

- (void)testThatDetectorWillNotFindCycleInBlockIfItHoldsWeakReferenceToObject
{
  _RCDTestClass *testObject = [_RCDTestClass new];

  __weak NSObject *weakTestObject = testObject;
  __block NSObject *unretainedObject;

  _RCDTestBlockType block = ^{
    unretainedObject = weakTestObject;
  };
  testObject.block = block;

  FBRetainCycleDetector *detector = [FBRetainCycleDetector new];
  [detector addCandidate:testObject];
  NSSet *retainCycles = [detector findRetainCycles];

  XCTAssertEqual([retainCycles count], 0);
}

- (void)testThatDetectorWillFindCycleBetweenBlockAndObject
{
  _RCDTestClass *testObject = [_RCDTestClass new];
  __block NSObject *unretainedObject;

  _RCDTestBlockType block = ^{
    unretainedObject = testObject;
  };
  testObject.block = block;

  FBRetainCycleDetector *detector = [FBRetainCycleDetector new];
  [detector addCandidate:testObject];
  NSSet *retainCycles = [detector findRetainCycles];

  NSSet *expectedSet = [NSSet setWithObject:[detector _shiftToUnifiedCycle:
                                             @[[[FBObjectiveCObject alloc] initWithObject:testObject],
                                               [[FBObjectiveCBlock alloc] initWithObject:block]]]];

  XCTAssertEqualObjects(retainCycles, expectedSet);
}

- (void)testThatDetectorWillFindCycleBetweenBlockAndObjectHeldByArray
{
  _RCDTestClass *testObject = [_RCDTestClass new];
  NSArray *array = @[testObject];
  __block NSObject *unretainedObject;

  _RCDTestBlockType block = ^{
    unretainedObject = array;
  };
  testObject.block = block;

  FBRetainCycleDetector *detector = [FBRetainCycleDetector new];
  [detector addCandidate:testObject];
  NSSet *retainCycles = [detector findRetainCycles];

  NSSet *expectedSet = [NSSet setWithObject:[detector _shiftToUnifiedCycle:
                                             @[[[FBObjectiveCObject alloc] initWithObject:testObject],
                                               [[FBObjectiveCBlock alloc] initWithObject:block],
                                               [[FBObjectiveCObject alloc] initWithObject:array]]]];

  XCTAssertEqualObjects(retainCycles, expectedSet);
}

- (void)testThatDetectorWillFindCycleIfMultipleBlocksArePartOfIt
{
  _RCDTestClass *testObject1 = [_RCDTestClass new];
  _RCDTestClass *testObject2 = [_RCDTestClass new];

  __block NSObject *unretainedObject;

  _RCDTestBlockType block1 = ^{unretainedObject = testObject1;};
  _RCDTestBlockType block2 = ^{unretainedObject = testObject2;};

  testObject1.block = block2;
  testObject2.block = block1;

  FBRetainCycleDetector *detector = [FBRetainCycleDetector new];
  [detector addCandidate:block1];
  NSSet *retainCycles = [detector findRetainCycles];

  NSSet *expectedSet = [NSSet setWithObject:[detector _shiftToUnifiedCycle:
                                             @[[[FBObjectiveCBlock alloc] initWithObject:block1],
                                               [[FBObjectiveCObject alloc] initWithObject:testObject1],
                                               [[FBObjectiveCBlock alloc] initWithObject:block2],
                                               [[FBObjectiveCObject alloc] initWithObject:testObject2]]]];

  XCTAssertEqualObjects(retainCycles, expectedSet);
}

- (void)testThatDetectorWillFindCycleIfParentClassPropertyIsAReasonForCycle
{
  _RCDTestSubclass *testObject = [_RCDTestSubclass new];
  testObject.object = testObject;

  FBRetainCycleDetector *detector = [FBRetainCycleDetector new];
  [detector addCandidate:testObject];
  NSSet *retainCycles = [detector findRetainCycles];

  NSSet *expectedSet = [NSSet setWithObject:@[[[FBObjectiveCObject alloc] initWithObject:testObject]]];

  XCTAssertEqualObjects(retainCycles, expectedSet);
}

- (void)testThatDetectorWillFindCycleBetweenObjectAndItsSubclass
{
  _RCDTestSubclass *testObject = [_RCDTestSubclass new];
  _RCDTestClass *testObject2 = [_RCDTestClass new];
  testObject.object = testObject2;
  testObject2.object = testObject;

  FBRetainCycleDetector *detector = [FBRetainCycleDetector new];
  [detector addCandidate:testObject];
  NSSet *retainCycles = [detector findRetainCycles];

  NSSet *expectedSet = [NSSet setWithObject:[detector _shiftToUnifiedCycle:
                                             @[[[FBObjectiveCObject alloc] initWithObject:testObject],
                                               [[FBObjectiveCObject alloc] initWithObject:testObject2]]]];

  XCTAssertEqualObjects(retainCycles, expectedSet);
}

- (void)testThatDetectorWillFindCycleIfPartOfItIsElementOfStruct
{
  _RCDTestClass *testObject1 = [_RCDTestClass new];
  _RCDTestClass *testObject2 = [_RCDTestClass new];

  testObject1.someStruct = _RCDTestStruct {
    .model = testObject2
  };
  testObject2.object = testObject1;

  FBRetainCycleDetector *detector = [FBRetainCycleDetector new];
  [detector addCandidate:testObject1];
  NSSet *retainCycles = [detector findRetainCycles];

  NSSet *expectedSet = [NSSet setWithObject:[detector _shiftToUnifiedCycle:
                                             @[[[FBObjectiveCObject alloc] initWithObject:testObject1],
                                               [[FBObjectiveCObject alloc] initWithObject:testObject2]]]];

  XCTAssertEqualObjects(retainCycles, expectedSet);
}

- (void)testThatDetectorWillNotFindCycleIfItGoesThroughStructsWeakReference
{
  _RCDTestClass *testObject1 = [_RCDTestClass new];
  _RCDTestClass *testObject2 = [_RCDTestClass new];

  testObject1.someStruct = _RCDTestStruct {
    .weakModel = testObject2
  };
  testObject2.object = testObject1;

  FBRetainCycleDetector *detector = [FBRetainCycleDetector new];
  [detector addCandidate:testObject1];
  NSSet *retainCycles = [detector findRetainCycles];

  XCTAssertEqual([retainCycles count], 0);
}

- (void)testRetainCycleInStandardViewControllerDelegation
{
  UIViewController<UITableViewDelegate> *vc = [UIViewController<UITableViewDelegate> new];
  UITableView *tv = [UITableView new];
  tv.delegate = vc;

  FBRetainCycleDetector *detector = [FBRetainCycleDetector new];
  [detector addCandidate:vc];
  NSSet *retainCycles = [detector findRetainCycles];

  XCTAssertEqual([retainCycles count], 0);
}

- (void)testThatDetectorWillNotFindCyclesDeeperThanItsStackDepth
{
  _RCDTestClass *testObject1 = [_RCDTestClass new];
  _RCDTestClass *testObject2 = [_RCDTestClass new];
  _RCDTestClass *testObject3 = [_RCDTestClass new];

  testObject1.object = testObject2;
  testObject2.object = testObject3;
  testObject3.object = testObject1;

  FBRetainCycleDetector *detector = [FBRetainCycleDetector new];
  [detector addCandidate:testObject1];
  NSSet *retainCycles = [detector findRetainCyclesWithMaxCycleLength:2];

  XCTAssertEqual([retainCycles count], 0);
}

- (void)testThatDetectorWillShiftCycleToLowestAddressFirstWhenItsPlacedInTheMiddle
{
  _RCDTestClass *testObject1 = [_RCDTestClass new];
  _RCDTestClass *testObject2 = [_RCDTestClass new];
  _RCDTestClass *testObject3 = [_RCDTestClass new];
  _RCDTestClass *testObject4 = [_RCDTestClass new];
  _RCDTestClass *testObject5 = [_RCDTestClass new];

  _RCDTestGraphElement *wrapped1 = [[_RCDTestGraphElement alloc] initWithObject:testObject1
                                                                   fakedAddress:0
                                                                      className:@"3"];
  _RCDTestGraphElement *wrapped2 = [[_RCDTestGraphElement alloc] initWithObject:testObject2
                                                                   fakedAddress:1
                                                                      className:@"2"];
  _RCDTestGraphElement *wrapped3 = [[_RCDTestGraphElement alloc] initWithObject:testObject3
                                                                   fakedAddress:4
                                                                      className:@"0"];
  _RCDTestGraphElement *wrapped4 = [[_RCDTestGraphElement alloc] initWithObject:testObject4
                                                                   fakedAddress:7
                                                                      className:@"7"];
  _RCDTestGraphElement *wrapped5 = [[_RCDTestGraphElement alloc] initWithObject:testObject5
                                                                   fakedAddress:8
                                                                      className:@"4"];

  FBRetainCycleDetector *detector = [FBRetainCycleDetector new];

  NSArray *shifted = [detector _shiftToUnifiedCycle:@[wrapped1,
                                                      wrapped2,
                                                      wrapped3,
                                                      wrapped4,
                                                      wrapped5]];
  NSArray *expectedShift = @[wrapped3, wrapped4, wrapped5, wrapped1, wrapped2];
  XCTAssertEqualObjects(shifted, expectedShift);
}

/**
         A
         |
         B
        / \
       C   D
        \ /
         E <-\
         |   |
         F --/

 It could register duplicate since we can get to E from two different paths.
 */
- (void)testThatDetectorWillRemoveDuplicateCycles
{
  _RCDTestClass *testObject1 = [_RCDTestClass new];
  _RCDTestClass *testObject2 = [_RCDTestClass new];
  _RCDTestClass *testObject3 = [_RCDTestClass new];
  _RCDTestClass *testObject4 = [_RCDTestClass new];
  _RCDTestClass *testObject5 = [_RCDTestClass new];
  _RCDTestClass *testObject6 = [_RCDTestClass new];

  testObject1.object = testObject2;
  testObject2.object = testObject3;
  testObject2.secondObject = testObject4;
  testObject3.object = testObject5;
  testObject4.object = testObject5;
  testObject5.object = testObject6;
  testObject6.object = testObject5;

  FBRetainCycleDetector *detector = [FBRetainCycleDetector new];
  [detector addCandidate:testObject1];
  NSSet *retainCycles = [detector findRetainCycles];

  NSSet *expectedSet = [NSSet setWithObject:[detector _shiftToUnifiedCycle:
                                             @[[[FBObjectiveCObject alloc] initWithObject:testObject5],
                                               [[FBObjectiveCObject alloc] initWithObject:testObject6]]]];

  XCTAssertEqualObjects(retainCycles, expectedSet);
}

- (void)testThatDetectorWillRemoveDuplicatesIfOneOfThemIsCyclicShiftOfOther
{
  _RCDTestClass *testObject1 = [_RCDTestClass new];
  _RCDTestClass *testObject2 = [_RCDTestClass new];

  testObject1.object = testObject2;
  testObject2.object = testObject1;

  FBRetainCycleDetector *detector = [FBRetainCycleDetector new];
  [detector addCandidate:testObject1];
  [detector addCandidate:testObject2];
  NSSet *retainCycles = [detector findRetainCycles];

  NSSet *expectedSet = [NSSet setWithObject:[detector _shiftToUnifiedCycle:
                                             @[[[FBObjectiveCObject alloc] initWithObject:testObject1],
                                               [[FBObjectiveCObject alloc] initWithObject:testObject2]]]];

  XCTAssertEqualObjects(retainCycles, expectedSet);
}

#endif //_INTERNAL_RCD_ENABLED

@end
