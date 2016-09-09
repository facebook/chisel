/**
 * Copyright (c) 2016-present, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

#import <Foundation/Foundation.h>

#import "FBObjectGraphConfiguration.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 Standard filters mostly filters excluding some UIKit references we have caught during testing on some apps.
 */
NSArray<FBGraphEdgeFilterBlock> *_Nonnull FBGetStandardGraphEdgeFilters();

/**
 Helper functions for some typical patterns.
 */
FBGraphEdgeFilterBlock _Nonnull FBFilterBlockWithObjectIvarRelation(Class _Nonnull aCls,
                                                                    NSString *_Nonnull ivarName);
FBGraphEdgeFilterBlock _Nonnull FBFilterBlockWithObjectToManyIvarsRelation(Class _Nonnull aCls,
                                                                           NSSet<NSString *> *_Nonnull ivarNames);
FBGraphEdgeFilterBlock _Nonnull FBFilterBlockWithObjectIvarObjectRelation(Class _Nonnull fromClass,
                                                                          NSString *_Nonnull ivarName,
                                                                          Class _Nonnull toClass);

#ifdef __cplusplus
}
#endif
