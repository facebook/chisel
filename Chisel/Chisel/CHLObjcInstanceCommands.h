// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
//
// This source code is licensed under the MIT license found in the
// LICENSE file in the root directory of this source tree.

@class NSPredicate;

#if defined(__cplusplus)
extern "C" {
#endif

// Debugger interface for finding and printing instances of a type, with an optional predicate.
// The predicate format is anything supported by NSPredicate.
void PrintInstances(const char *type, const char *pred);

#if defined(__cplusplus)
}
#endif
