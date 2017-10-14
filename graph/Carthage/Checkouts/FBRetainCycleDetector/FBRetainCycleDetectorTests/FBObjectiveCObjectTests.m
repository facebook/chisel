/**
 * Copyright (c) 2016-present, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

#import <XCTest/XCTest.h>

#import <FBRetainCycleDetector/FBObjectiveCGraphElement+Internal.h>
#import <FBRetainCycleDetector/FBObjectiveCObject.h>
#import <FBRetainCycleDetector/FBRetainCycleDetector.h>

@interface _RCDObjectWrapperTestClass : NSObject
- (instancetype)initWithOtherObject:(_RCDObjectWrapperTestClass *)object;
@property (nonatomic, strong) NSObject *someObject;
@property (nonatomic, copy) NSString *someString;
@property (nonatomic, weak) NSObject *irrelevantObject;
@property (nonatomic, strong) id aCls;
@end
@implementation _RCDObjectWrapperTestClass
{
  _RCDObjectWrapperTestClass *_someTestClassInstance;
}

- (instancetype)initWithOtherObject:(_RCDObjectWrapperTestClass *)object
{
  if (self = [super init]) {
    _someTestClassInstance = object;
  }

  return self;
}

@end

@interface _RCDObjectWrapperTestClassSubclass : _RCDObjectWrapperTestClass
@end
@implementation _RCDObjectWrapperTestClassSubclass
@end

@interface FBObjectiveCObjectTests : XCTestCase
@end
@implementation FBObjectiveCObjectTests

#if _INTERNAL_RCD_ENABLED

- (void)testObjectsRetainedBySomeObjectWillBeFetched
{
  NSObject *someObject = [NSObject new];
  NSString *someString = @"someString";
  NSObject *irrelevant = [NSObject new];
  _RCDObjectWrapperTestClass *verifyObject = [_RCDObjectWrapperTestClass new];
  _RCDObjectWrapperTestClass *testObject = [[_RCDObjectWrapperTestClass alloc] initWithOtherObject:verifyObject];
  testObject.someObject = someObject;
  testObject.someString = someString;
  testObject.irrelevantObject = irrelevant;

  FBObjectiveCObject *object = [[FBObjectiveCObject alloc] initWithObject:testObject];
  NSSet *retainedObjects = [object allRetainedObjects];

  XCTAssertFalse([retainedObjects containsObject:[[FBObjectiveCObject alloc] initWithObject:irrelevant]]);
  XCTAssertTrue([retainedObjects containsObject:[[FBObjectiveCObject alloc] initWithObject:someObject]]);
  XCTAssertTrue([retainedObjects containsObject:[[FBObjectiveCObject alloc] initWithObject:someString]]);
  XCTAssertTrue([retainedObjects containsObject:[[FBObjectiveCObject alloc] initWithObject:verifyObject]]);

}

- (void)testObjectsRetainedByArrayWillBeFetched
{
  NSString *someString = @"someString";
  NSObject *someObject = [NSObject new];
  NSDictionary *someDictionary = [NSDictionary new];
  NSArray *testedArray = @[someString, someObject, someDictionary];

  FBObjectiveCObject *abstractedObject = [[FBObjectiveCObject alloc] initWithObject:testedArray];

  NSSet *retainedObjects = [abstractedObject allRetainedObjects];

  XCTAssertTrue([retainedObjects containsObject:[[FBObjectiveCObject alloc] initWithObject:someString]]);
  XCTAssertTrue([retainedObjects containsObject:[[FBObjectiveCObject alloc] initWithObject:someObject]]);
  XCTAssertTrue([retainedObjects containsObject:[[FBObjectiveCObject alloc] initWithObject:someDictionary]]);
}

- (void)testObjectsRetainedByDictionaryWillBeFetched
{
  NSString *someString = @"someString";
  NSObject *someObject = [NSObject new];

  NSDictionary *someDictionary = @{someString:someObject};

  FBObjectiveCObject *abstractedObject = [[FBObjectiveCObject alloc] initWithObject:someDictionary];

  NSSet *retainedObjects = [abstractedObject allRetainedObjects];

  XCTAssertTrue([retainedObjects containsObject:[[FBObjectiveCObject alloc] initWithObject:someString]]);
  XCTAssertTrue([retainedObjects containsObject:[[FBObjectiveCObject alloc] initWithObject:someObject]]);
}

- (void)testObjectsRetainedBySetWillBeFetched
{
  NSString *someString = @"someString";
  NSObject *someObject = [NSObject new];

  NSSet *someSet = [NSSet setWithObjects:someString, someObject, nil];

  FBObjectiveCObject *abstractedObject = [[FBObjectiveCObject alloc] initWithObject:someSet];

  NSSet *retainedObjects = [abstractedObject allRetainedObjects];

  XCTAssertTrue([retainedObjects containsObject:[[FBObjectiveCObject alloc] initWithObject:someString]]);
  XCTAssertTrue([retainedObjects containsObject:[[FBObjectiveCObject alloc] initWithObject:someObject]]);
}

- (void)testThatIfObjectHasStrongPropertyWithNilThenItWontFetchIt
{
  _RCDObjectWrapperTestClass *someObject = [_RCDObjectWrapperTestClass new];

  FBObjectiveCObject *abstractedObject = [[FBObjectiveCObject alloc] initWithObject:someObject];

  NSSet *retainedObjects = [abstractedObject allRetainedObjects];

  XCTAssertEqual([retainedObjects count], 0);
}

- (void)testObjectThatSubclassesFromObjectWithStrongPropertiesWillFetchPropertiesFromParentClass
{
  _RCDObjectWrapperTestClassSubclass *testObject = [_RCDObjectWrapperTestClassSubclass new];
  NSObject *someObject = [NSObject new];
  NSObject *irrelevantObject = [NSObject new];
  NSString *someString = @"someString";
  testObject.someObject = someObject;
  testObject.irrelevantObject = irrelevantObject;
  testObject.someString = someString;

  FBObjectiveCObject *abstractedObject = [[FBObjectiveCObject alloc] initWithObject:testObject];

  NSSet *retainedObjects = [abstractedObject allRetainedObjects];

  XCTAssertTrue([retainedObjects containsObject:[[FBObjectiveCObject alloc] initWithObject:someString]]);
  XCTAssertTrue([retainedObjects containsObject:[[FBObjectiveCObject alloc] initWithObject:someObject]]);
  XCTAssertFalse([retainedObjects containsObject:[[FBObjectiveCObject alloc] initWithObject:irrelevantObject]]);
}

- (void)testObjectRetainingClassConformingToFastEnumerationWillNotCrash
{
  _RCDObjectWrapperTestClass *someObject = [_RCDObjectWrapperTestClass new];
  someObject.aCls = [NSArray class];

  FBObjectiveCObject *abstractedObject = [[FBObjectiveCObject alloc] initWithObject:someObject];

  NSSet *retainedObjects = [abstractedObject allRetainedObjects];

  XCTAssertTrue([retainedObjects containsObject:[[FBObjectiveCObject alloc] initWithObject:[NSArray class]]]);
}

- (void)testHashTableWithWeakObjectsWillNotFetchThoseObjects
{
  NSHashTable *hashTable = [NSHashTable weakObjectsHashTable];

  _RCDObjectWrapperTestClass *someObject1 = [_RCDObjectWrapperTestClass new];
  _RCDObjectWrapperTestClass *someObject2 = [_RCDObjectWrapperTestClass new];
  _RCDObjectWrapperTestClass *someObject3 = [_RCDObjectWrapperTestClass new];

  [hashTable addObject:someObject1];
  [hashTable addObject:someObject2];
  [hashTable addObject:someObject3];

  FBObjectiveCObject *abstractedObject = [[FBObjectiveCObject alloc] initWithObject:hashTable];

  NSSet *retainedObjects = [abstractedObject allRetainedObjects];

  XCTAssertEqual([retainedObjects count], 0);
}

- (void)testHashTableWithStrongObjectsWillFetchThoseObjects
{
  NSHashTable *hashTable = [NSHashTable new];

  _RCDObjectWrapperTestClass *someObject1 = [_RCDObjectWrapperTestClass new];
  _RCDObjectWrapperTestClass *someObject2 = [_RCDObjectWrapperTestClass new];
  _RCDObjectWrapperTestClass *someObject3 = [_RCDObjectWrapperTestClass new];

  [hashTable addObject:someObject1];
  [hashTable addObject:someObject2];
  [hashTable addObject:someObject3];

  FBObjectiveCObject *abstractedObject = [[FBObjectiveCObject alloc] initWithObject:hashTable];

  NSSet *retainedObjects = [abstractedObject allRetainedObjects];

  XCTAssertTrue([retainedObjects containsObject:[[FBObjectiveCObject alloc] initWithObject:someObject1]]);
  XCTAssertTrue([retainedObjects containsObject:[[FBObjectiveCObject alloc] initWithObject:someObject2]]);
  XCTAssertTrue([retainedObjects containsObject:[[FBObjectiveCObject alloc] initWithObject:someObject3]]);
}

- (void)testMapTableWithWeakKeysAndValueWillNotFetchAnything
{
  NSMapTable *mapTable = [NSMapTable weakToWeakObjectsMapTable];

  _RCDObjectWrapperTestClass *keyObject = [_RCDObjectWrapperTestClass new];
  _RCDObjectWrapperTestClass *valueObject = [_RCDObjectWrapperTestClass new];

  [mapTable setObject:valueObject forKey:keyObject];

  FBObjectiveCObject *abstractedObject = [[FBObjectiveCObject alloc] initWithObject:mapTable];

  NSSet *retainedObjects = [abstractedObject allRetainedObjects];

  XCTAssertEqual([retainedObjects count], 0);
}

- (void)testMapTableWithWeakKeysAndStrongValuesWillFetchOnlyValues
{
  NSMapTable *mapTable = [NSMapTable weakToStrongObjectsMapTable];

  _RCDObjectWrapperTestClass *keyObject = [_RCDObjectWrapperTestClass new];
  _RCDObjectWrapperTestClass *valueObject = [_RCDObjectWrapperTestClass new];

  [mapTable setObject:valueObject forKey:keyObject];

  FBObjectiveCObject *abstractedObject = [[FBObjectiveCObject alloc] initWithObject:mapTable];

  NSSet *retainedObjects = [abstractedObject allRetainedObjects];

  XCTAssertEqual([retainedObjects count], 1);
  XCTAssertTrue([retainedObjects containsObject:[[FBObjectiveCObject alloc] initWithObject:valueObject]]);
}

- (void)testMapTableWithStrongKeysAndWeakValuesWillFetchOnlyKeys
{
  NSMapTable *mapTable = [NSMapTable strongToWeakObjectsMapTable];

  _RCDObjectWrapperTestClass *keyObject = [_RCDObjectWrapperTestClass new];
  _RCDObjectWrapperTestClass *valueObject = [_RCDObjectWrapperTestClass new];

  [mapTable setObject:valueObject forKey:keyObject];

  FBObjectiveCObject *abstractedObject = [[FBObjectiveCObject alloc] initWithObject:mapTable];

  NSSet *retainedObjects = [abstractedObject allRetainedObjects];

  XCTAssertEqual([retainedObjects count], 1);
  XCTAssertTrue([retainedObjects containsObject:[[FBObjectiveCObject alloc] initWithObject:keyObject]]);
}

- (void)testMapTableWithStrongKeysAndStrongValuesWillFetchBothKeysAndValues
{
  NSMapTable *mapTable = [NSMapTable strongToStrongObjectsMapTable];

  _RCDObjectWrapperTestClass *keyObject = [_RCDObjectWrapperTestClass new];
  _RCDObjectWrapperTestClass *valueObject = [_RCDObjectWrapperTestClass new];

  [mapTable setObject:valueObject forKey:keyObject];

  FBObjectiveCObject *abstractedObject = [[FBObjectiveCObject alloc] initWithObject:mapTable];

  NSSet *retainedObjects = [abstractedObject allRetainedObjects];

  XCTAssertEqual([retainedObjects count], 2);
  XCTAssertTrue([retainedObjects containsObject:[[FBObjectiveCObject alloc] initWithObject:keyObject]]);
  XCTAssertTrue([retainedObjects containsObject:[[FBObjectiveCObject alloc] initWithObject:valueObject]]);
}

- (void)testTollFreeBridgedDictionaryWillNotCrash
{
  CFDictionaryValueCallBacks cb = kCFTypeDictionaryValueCallBacks;
  cb.retain = NULL;
  cb.release = NULL;
  NSMutableDictionary *dictionary = (__bridge_transfer id)CFDictionaryCreateMutable(NULL, 0, NULL, &cb);
  NSInteger intV = 5;
  CFDictionarySetValue((CFMutableDictionaryRef)dictionary, (__bridge const void *)@"key", (const void *)intV);

  FBObjectiveCObject *abstractedObject = [[FBObjectiveCObject alloc] initWithObject:dictionary];

  NSSet *retainedObjects = [abstractedObject allRetainedObjects];

  XCTAssertEqual([retainedObjects count], 0);
}

#endif //_INTERNAL_RCD_ENABLED

@end
