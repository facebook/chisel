// Copyright 2004-present Facebook. All Rights Reserved.

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
