/**
 * Copyright (c) 2016-present, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

#import "FBAssociationManager.h"
#import "FBRetainCycleDetector.h"

#if _INTERNAL_RCD_ENABLED

namespace FB { namespace AssociationManager {

  void _threadUnsafeResetAssociationAtKey(id object, void *key);
  void _threadUnsafeSetStrongAssociation(id object, void *key, id value);
  void _threadUnsafeRemoveAssociations(id object);

  NSArray *associations(id object);

} }

#endif
