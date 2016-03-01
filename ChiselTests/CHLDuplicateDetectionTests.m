//
//  CHLDuplicateDetectionTests.m
//  Chisel
//
//  Copyright © 2016 Facebook. All rights reserved.
//

#import <XCTest/XCTest.h>

#import "CHLDuplicateDetection.h"

@interface _CHLTestClass : NSObject
@property (nonatomic, strong) NSString *identifier;
@end
@implementation _CHLTestClass
@end

@interface CHLDuplicateDetectionTests : XCTestCase
@end

@implementation CHLDuplicateDetectionTests

- (void)testDuplicateDetectionCanFindTwoCustomObjects
{
  @autoreleasepool {
    _CHLTestClass *testObject1 = [_CHLTestClass new];
    _CHLTestClass *testObject2 = [_CHLTestClass new];
    testObject1.identifier = @"Test";
    testObject2.identifier = @"Test";
    
    BOOL (^equalityFunction)(_CHLTestClass *, _CHLTestClass *) = ^(_CHLTestClass *left, _CHLTestClass *right) {
      return ([left.identifier isEqualToString:right.identifier]);
    };
    
    NSArray *duplicates = CHLFindDuplicates([_CHLTestClass class], equalityFunction);
    XCTAssertTrue([duplicates containsObject:testObject1]);
    XCTAssertTrue([duplicates containsObject:testObject2]);
  }
}

- (void)testDuplicateDetectionCanFindMoreCustomObjects
{
  @autoreleasepool {
    _CHLTestClass *testObject1 = [_CHLTestClass new];
    _CHLTestClass *testObject2 = [_CHLTestClass new];
    _CHLTestClass *testObject3 = [_CHLTestClass new];
    _CHLTestClass *testObject4 = [_CHLTestClass new];
    _CHLTestClass *testObject5 = [_CHLTestClass new];
    testObject1.identifier = @"Test";
    testObject2.identifier = @"Test";
    testObject3.identifier = @"Test";
    testObject4.identifier = @"Test2";
    testObject5.identifier = @"Test2";
    
    BOOL (^equalityFunction)(_CHLTestClass *, _CHLTestClass *) = ^(_CHLTestClass *left, _CHLTestClass *right) {
      return ([left.identifier isEqualToString:right.identifier]);
    };
    
    NSArray *duplicates = CHLFindDuplicates([_CHLTestClass class], equalityFunction);
    XCTAssertTrue([duplicates containsObject:testObject1]);
    XCTAssertTrue([duplicates containsObject:testObject2]);
    XCTAssertTrue([duplicates containsObject:testObject3]);
    XCTAssertTrue([duplicates containsObject:testObject4]);
    XCTAssertTrue([duplicates containsObject:testObject5]);
  }
}

@end