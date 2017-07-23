// Copyright 2004-present Facebook. All Rights Reserved.

#import "CHLPredicateTools.h"

static bool isEqualToConstantComparison(NSComparisonPredicate *predicate)
{
  bool equality = predicate.predicateOperatorType == NSEqualToPredicateOperatorType;
  bool direct = predicate.comparisonPredicateModifier == NSDirectPredicateModifier;
  bool constantLeft = predicate.leftExpression.expressionType == NSConstantValueExpressionType;
  bool constantRight = predicate.rightExpression.expressionType == NSConstantValueExpressionType;
  return equality && direct && (constantLeft || constantRight);
}

NSSet *CHLVariableKeyPaths(NSPredicate *predicate)
{
  if (predicate == nil) {
    return nil;
  }

  NSMutableSet *keyPaths = [NSMutableSet new];

  NSMutableArray *predicateStack = [NSMutableArray arrayWithObject:predicate];
  while (predicateStack.count > 0) {
    NSPredicate *subpredicate = [predicateStack lastObject];
    [predicateStack removeLastObject];

    if ([subpredicate isKindOfClass:[NSCompoundPredicate class]]) {
      NSCompoundPredicate *compoundPredicate = (NSCompoundPredicate *)subpredicate;
      [predicateStack addObjectsFromArray:compoundPredicate.subpredicates];
      continue;
    }

    if ([subpredicate isKindOfClass:[NSComparisonPredicate class]]) {
      NSComparisonPredicate *comparisonPredicate = (NSComparisonPredicate *)subpredicate;

      if (isEqualToConstantComparison(comparisonPredicate)) {
        // Keypaths equal to constants are not variable. Skip these to not be noisy.
        // ex `username == "jonalan"` or `alpha == 0`
        continue;
      }

      // TODO: Handle NSFunctionExpressionType
      if (comparisonPredicate.leftExpression.expressionType == NSKeyPathExpressionType) {
        [keyPaths addObject:comparisonPredicate.leftExpression.keyPath];
      }
      if (comparisonPredicate.rightExpression.expressionType == NSKeyPathExpressionType) {
        [keyPaths addObject:comparisonPredicate.rightExpression.keyPath];
      }
    }
  }

  return keyPaths;
}
