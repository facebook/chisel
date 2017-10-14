// Copyright 2004-present Facebook. All Rights Reserved.

#import <Foundation/Foundation.h>

@interface FBGraphChiselCommands : NSObject

/**
 Functions for Chisel to hook into.
 All functions return a NSString for easy printability.
 */

/**
 Finds all incoming and outgoing strong references to an object.
 */
+ (NSString *)findStrongReferences:(id)object;

/**
 Finds any duplicates of an object.
 */
+ (NSString *)findDuplicates:(id)object;

/**
 Finds all retain cycles in memory.
 This logic differ slightly from that found in FBRetainCycleDetector.
 We are able to traverse the graph in its entirety since we have a cached graph in a halted state -
 essentially this will find any and all retain cycles within the memory graph, without a root object.

 For more information on the algorithm:
 https://en.wikipedia.org/wiki/Kosaraju%27s_algorithm
 */
+ (NSString *)findRetainCycles;

@end
