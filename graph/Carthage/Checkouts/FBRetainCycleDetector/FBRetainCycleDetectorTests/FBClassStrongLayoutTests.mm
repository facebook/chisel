/**
 * Copyright (c) 2016-present, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

#import <memory>

#import <UIKit/UIKit.h>
#import <XCTest/XCTest.h>

#import <FBRetainCycleDetector/FBClassStrongLayout.h>
#import <FBRetainCycleDetector/FBRetainCycleDetector.h>

@interface _RCDTestEmptyClass : NSObject
@end
@implementation _RCDTestEmptyClass
@end

@interface _RCDTestClassWithWeakProperty : NSObject
@property (nonatomic, weak) NSObject *object;
@end
@implementation _RCDTestClassWithWeakProperty
@end

@interface _RCDTestClassWithStrongProperty : NSObject
@property (nonatomic, strong) NSObject *object;
@end
@implementation _RCDTestClassWithStrongProperty
@end

@interface _RCDTestClassWithMixedWeakAndStrongProperties : NSObject
@property (nonatomic, strong) NSObject *object1;
@property (nonatomic, strong) NSObject *object2;
@property (nonatomic, strong) NSObject *object3;
@property (nonatomic, weak) NSObject *object4;
@property (nonatomic, strong) NSObject *object5;
@property (nonatomic, weak) NSObject *object6;
@end
@implementation _RCDTestClassWithMixedWeakAndStrongProperties
@end

@interface _RCDTestClassWithSimpleInheritance : _RCDTestEmptyClass
@property (nonatomic, strong) NSObject *object1;
@property (nonatomic, weak) NSObject *object2;
@end
@implementation _RCDTestClassWithSimpleInheritance
@end

@interface _RCDTestClassSubclassingClassWithStrongProperties : _RCDTestClassWithMixedWeakAndStrongProperties
@property (nonatomic, weak) NSObject *object7;
@end
@implementation _RCDTestClassSubclassingClassWithStrongProperties
@end

typedef struct {
  int someInt;
  char someCharacter;
  unsigned long long someUnsignedLongLong;
} _RCDTestStructWithPrimitives;

@interface _RCDTestClassWithSimpleStruct : NSObject
@property (nonatomic, assign) _RCDTestStructWithPrimitives structure;
@end
@implementation _RCDTestClassWithSimpleStruct
@end

typedef struct {
  NSObject *retainedObject;
  int number;
  NSObject *anotherRetainedObject;
} _RCDTestStructWithObjects;

@interface _RCDTestClassWithStructContainingObjects : NSObject
@property (nonatomic, assign) _RCDTestStructWithObjects structure;
@end
@implementation _RCDTestClassWithStructContainingObjects
@end

typedef struct {
  __weak NSObject *object;
} _RCDTestStructWithWeakObject;

@interface _RCDTestClassWithStructContainingWeakObject : NSObject
@property (nonatomic, assign) _RCDTestStructWithWeakObject structure;
@end
@implementation _RCDTestClassWithStructContainingWeakObject
@end

typedef struct {
  int a;
  _RCDTestStructWithObjects someStruct;
  char b;
  int c;
  int d;
  __weak NSObject *object;
  float *e;
  void *f;
  NSObject *g;
  _RCDTestStructWithObjects someStruct2;
} _RCDTestStructWithComplicatedLayout;

@interface _RCDTestClassWithComplicatedStruct : NSObject
@property (nonatomic, assign) _RCDTestStructWithComplicatedLayout testStruct;
@end
@implementation _RCDTestClassWithComplicatedStruct
@end

typedef struct {
  unsigned somebit1: 1;
  unsigned somebit2: 1;
  unsigned somebit3: 1;
  unsigned somebit4: 1;
  unsigned somebit5: 6;
} _RCDTestStructWithBitfields;

@interface _RCDTestClassWithBitfieldStructAndStrongProperties : NSObject
@property (nonatomic, strong) NSObject *object1;
@property (nonatomic, assign) _RCDTestStructWithBitfields someStruct;
@property (nonatomic, strong) NSObject *object2;
@end
@implementation _RCDTestClassWithBitfieldStructAndStrongProperties
@end

@interface _RCDTestClassWithEnumValue : NSObject
@end
@implementation _RCDTestClassWithEnumValue
{
  UIRectEdge rectEdge;
}
@end

@interface _RCDTestClassWithSharedPointer : NSObject
@end
@implementation _RCDTestClassWithSharedPointer
{
  std::shared_ptr<_RCDTestStructWithObjects> _sharedPointer;
}
- (instancetype)init
{
  if (self = [super init]) {
    _sharedPointer = std::shared_ptr<_RCDTestStructWithObjects> (new _RCDTestStructWithObjects);
  }

  return self;
}
@end

@interface _RCDTestClassWithCppStructAndStrongProperty : NSObject
@end
@implementation _RCDTestClassWithCppStructAndStrongProperty
{
  std::atomic<bool> _someAtomicValue;
  NSObject *_object;
}
@end

@interface FBClassStrongLayoutTests : XCTestCase
@end

@implementation FBClassStrongLayoutTests

- (void)testLayoutForEmptyClassWillBeEmpty
{
  NSArray *ivars = FBGetObjectStrongReferences([_RCDTestEmptyClass new], nil);

  XCTAssertEqual([ivars count], 0);
}

- (void)testLayoutForClassWithWeakPropertyWillBeEmpty
{
  NSArray *ivars = FBGetObjectStrongReferences([_RCDTestClassWithWeakProperty new], nil);

  XCTAssertEqual([ivars count], 0);
}

- (void)testLayoutForClassWithStrongPropertyWillHaveOneReference
{
  NSArray *ivars = FBGetObjectStrongReferences([_RCDTestClassWithStrongProperty new], nil);

  XCTAssertEqual([ivars count], 1);
}

- (void)testLayoutForClassWithMixedStrongAndWeakWillFetchOnlyStrong
{
  NSArray *ivars = FBGetObjectStrongReferences([_RCDTestClassWithMixedWeakAndStrongProperties new], nil);

  XCTAssertEqual([ivars count], 4);
}

- (void)testLayoutForClassSubclassingEmptyClassWillFetchPropertiesProperly
{
  NSArray *ivars = FBGetObjectStrongReferences([_RCDTestClassWithSimpleInheritance new], nil);

  XCTAssertEqual([ivars count], 1);
}

- (void)testLayoutForClassSubclassingClassWithStrongPropertiesWillFetchParentsClassProperties
{
  NSArray *ivars = FBGetObjectStrongReferences([_RCDTestClassSubclassingClassWithStrongProperties new], nil);

  XCTAssertEqual([ivars count], 4);
}

- (void)testLayoutForClassWithStructAsIvarWillNotCrash
{
  NSArray *ivars = FBGetObjectStrongReferences([_RCDTestClassWithSimpleStruct new], nil);

  XCTAssertEqual([ivars count], 0);
}

- (void)testLayoutForClassWithStructContainingObjectsWillFetchThoseObjects
{
  NSArray *ivars = FBGetObjectStrongReferences([_RCDTestClassWithStructContainingObjects new], nil);

  XCTAssertEqual([ivars count], 2);
}

- (void)testLayoutForClassWithStructContainingWeakObjectWillBeEmpty
{
  NSArray *ivars = FBGetObjectStrongReferences([_RCDTestClassWithStructContainingWeakObject new], nil);

  XCTAssertEqual([ivars count], 0);
}

- (void)testLayoutForClassWithComplicatedStructWillWorkProperly
{
  NSArray *ivars = FBGetObjectStrongReferences([_RCDTestClassWithComplicatedStruct new], nil);

  XCTAssertEqual([ivars count], 5);
}

- (void)testLayoutForClassWithBitfieldsWillNotCrash
{
  NSArray *ivars = FBGetObjectStrongReferences([_RCDTestClassWithBitfieldStructAndStrongProperties new], nil);

  XCTAssertEqual([ivars count], 2);
}

- (void)testLayoutForClassWithEnumValueWillNotCrash
{
  NSArray *ivars = FBGetObjectStrongReferences([_RCDTestClassWithEnumValue new], nil);

  XCTAssertEqual([ivars count], 0);
}

- (void)testLayoutForClassWithSharedPointerWillNotCrash
{
  NSArray *ivars = FBGetObjectStrongReferences([_RCDTestClassWithSharedPointer new], nil);

  XCTAssertEqual([ivars count], 0);
}

- (void)testLayoutForClassWithCppStructAndStrongPropertyWillNotCrashAndFetchStrongProperty
{
  NSArray *ivars = FBGetObjectStrongReferences([_RCDTestClassWithCppStructAndStrongProperty new], nil);

  XCTAssertEqual([ivars count], 1);
}

@end
