/**
 * Copyright (c) 2016-present, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

#import <Foundation/Foundation.h>

//! Project version number for FBRetainCycleDetector.
FOUNDATION_EXPORT double FBRetainCycleDetectorVersionNumber;

//! Project version string for FBRetainCycleDetector.
FOUNDATION_EXPORT const unsigned char FBRetainCycleDetectorVersionString[];

#import "FBAssociationManager.h"
#import "FBObjectiveCBlock.h"
#import "FBObjectiveCGraphElement.h"
#import "FBObjectiveCNSCFTimer.h"
#import "FBObjectiveCObject.h"
#import "FBObjectGraphConfiguration.h"
#import "FBStandardGraphEdgeFilters.h"

/**
 Retain Cycle Detector is enabled by default in DEBUG builds, but you can also force it in other builds by
 uncommenting the line below. Beware, Retain Cycle Detector uses some private APIs that shouldn't be compiled in
 production builds.
 */
//#define RETAIN_CYCLE_DETECTOR_ENABLED 1

/**
 FBRetainCycleDetector

 The main class responsible for detecting retain cycles.

 Be cautious, the class is NOT thread safe.

 The process of detecting retain cycles is relatively slow and consumes a lot of CPU.
 */

@interface FBRetainCycleDetector : NSObject

/**
 Designated initializer

 @param configuration Configuration for detector. Can include specific filters and options.
 @see FBRetainCycleDetectorConfiguration
 */
- (nonnull instancetype)initWithConfiguration:(nonnull FBObjectGraphConfiguration *)configuration NS_DESIGNATED_INITIALIZER;

/**
 Adds candidate you are interested in getting retain cycles from.

 @param candidate Any Objective-C object you want to verify for cycles.
 */
- (void)addCandidate:(nonnull id)candidate;

/**
 Searches for all retain cycles for all candidates the detector has been
 provided with.

 @return NSSet with retain cycles. An element of this array will be
 an array representing retain cycle. That array will hold elements
 of type FBObjectiveCGraphElement.

 @discussion For given candidate, the detector will go through all object graph rooted in this candidate and return
 ALL retain cycles that this candidate references. It will also take care of removing duplicates. It will not look for
 cycles longer than 10 elements. If you want to look for longer ones use findRetainCyclesWithMaxCycleLenght:
 */
- (nonnull NSSet<NSArray<FBObjectiveCGraphElement *> *> *)findRetainCycles;

- (nonnull NSSet<NSArray<FBObjectiveCGraphElement *> *> *)findRetainCyclesWithMaxCycleLength:(NSUInteger)length;

/**
 This macro is used across FBRetainCycleDetector to compile out sensitive code.
 If you do not define it anywhere, Retain Cycle Detector will be available in DEBUG builds.
 */
#ifdef RETAIN_CYCLE_DETECTOR_ENABLED
#define _INTERNAL_RCD_ENABLED RETAIN_CYCLE_DETECTOR_ENABLED
#else
#define _INTERNAL_RCD_ENABLED DEBUG
#endif

@end
