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

@interface FBRCDTestCollection : NSMutableDictionary
@end


@implementation FBRCDTestCollection
{
  NSMutableDictionary *_proxy;

  NSUInteger _currentIndex;
}

- (void)setObject:(id)anObject forKey:(id<NSCopying>)aKey
{
  [_proxy setObject:anObject forKeyedSubscript:aKey];
}

- (void)removeObjectForKey:(id)aKey
{
  [_proxy removeObjectForKey:aKey];
}

- (instancetype)initWithObjects:(const id _Nonnull __unsafe_unretained *)objects forKeys:(const id<NSCopying> _Nonnull __unsafe_unretained *)keys count:(NSUInteger)cnt
{
  return [self init];
}

- (instancetype)init
{
  if (self = [super init]) {
    _proxy = [NSMutableDictionary new];
  }

  return self;
}

- (NSUInteger)count
{
  return _proxy.count;
}

- (id)objectForKey:(id)aKey
{
  _proxy[@"i_am_big_troll"] = @YES;

  return [_proxy objectForKey:aKey];
}

- (NSUInteger)countByEnumeratingWithState:(NSFastEnumerationState *)state objects:(__unsafe_unretained id _Nonnull *)buffer count:(NSUInteger)len
{
  return [_proxy countByEnumeratingWithState:state objects:buffer count:len];
}

@end

@interface FBRCDCollectionTests : XCTestCase
@end

@implementation FBRCDCollectionTests

#if _INTERNAL_RCD_ENABLED

- (void)testThatRetainCycleDetectorSkipsWhenCollectionIsMutatedWhileEnumeration
{
  FBRCDTestCollection *testCollection = [FBRCDTestCollection new];
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wobjc-circular-container"
  testCollection[@"a"] = testCollection;
  testCollection[@"b"] = testCollection;
#pragma clang diagnostic pop

  FBRetainCycleDetector *detector = [FBRetainCycleDetector new];

  [detector addCandidate:testCollection];
  NSSet *retainCycles = [detector findRetainCycles];

  XCTAssertFalse([retainCycles containsObject:[[FBObjectiveCObject alloc] initWithObject:testCollection]]);
}

#endif //_INTERNAL_RCD_ENABLED

@end
