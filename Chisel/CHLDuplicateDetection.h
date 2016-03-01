//
//  CHLDuplicateDetection.h
//  Chisel
//
//  Copyright © 2016 Facebook. All rights reserved.
//

#ifndef CHLDuplicateDetection_h
#define CHLDuplicateDetection_h

#import <Foundation/Foundation.h>

/**
 * Finds duplicates of objects in memory using `equalFunction` to compare.
 */
NSArray *CHLFindDuplicates(Class aCls, BOOL (^equalFunction)(id left, id right));

#endif /* CHLDuplicateDetection_h */
