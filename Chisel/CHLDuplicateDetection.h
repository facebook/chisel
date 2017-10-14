//
//  CHLDuplicateDetection.h
//  Chisel
//
//  Copyright © 2016 Facebook. All rights reserved.
//

#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/**
 * Finds duplicates of objects in memory using `equalFunction` to compare.
 */
NSArray *CHLFindDuplicates(Class cls, BOOL (^equalFunction)(id left, id right));

NS_ASSUME_NONNULL_END
