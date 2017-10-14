/**
 * Copyright (c) 2016-present, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

#import <Foundation/Foundation.h>

#import "FBObjectiveCGraphElement.h"

typedef NS_ENUM(NSUInteger, FBGraphEdgeType) {
  FBGraphEdgeValid,
  FBGraphEdgeInvalid,
};

@protocol FBObjectReference;

/**
 Every filter has to be of type FBGraphEdgeFilterBlock. Filter, given two object graph elements, it should decide,
 whether a reference between them should be filtered out or not.
 @see FBGetStandardGraphEdgeFilters()
 */
typedef FBGraphEdgeType (^FBGraphEdgeFilterBlock)(FBObjectiveCGraphElement *_Nullable fromObject,
                                                  NSString *_Nullable byIvar,
                                                  Class _Nullable toObjectOfClass);

/**
 FBObjectGraphConfiguration represents a configuration for object graph walking.
 It can hold filters and detector specific options.
 */
@interface FBObjectGraphConfiguration : NSObject

/**
 Every block represents a filter that every reference must pass in order to be inspected.
 Reference will be described as relation from one object to another object. See definition of
 FBGraphEdgeFilterBlock above.
 
 Invalid relations would be the relations that we are guaranteed are going to be broken at some point.
 Be careful though, it's not so straightforward to tell if the relation will be broken *with 100%
 certainty*, and if you'll filter out something that could otherwise show retain cycle that leaks -
 it would never be caught by detector.

 For examples of what are the relations that will be broken at some point check FBStandardGraphEdgeFilters.mm
 */
@property (nonatomic, readonly, copy, nullable) NSArray<FBGraphEdgeFilterBlock> *filterBlocks;

/**
 Decides if object graph walker should look for retain cycles inside NSTimers.
 */
@property (nonatomic, readonly) BOOL shouldInspectTimers;

/**
 Will cache layout
 */
@property (nonatomic, readonly, nullable) NSMutableDictionary<Class, NSArray<id<FBObjectReference>> *> *layoutCache;
@property (nonatomic, readonly) BOOL shouldCacheLayouts;

- (nonnull instancetype)initWithFilterBlocks:(nonnull NSArray<FBGraphEdgeFilterBlock> *)filterBlocks
                         shouldInspectTimers:(BOOL)shouldInspectTimers NS_DESIGNATED_INITIALIZER;

@end
