// Copyright 2004-present Facebook. All Rights Reserved.

#import "FBGraphChiselCommands.h"

#import <FBRetainCycleDetector/FBObjectGraphConfiguration.h>
#import <FBRetainCycleDetector/FBObjectiveCGraphElement.h>
#import <FBRetainCycleDetector/FBRetainCycleUtils.h>
#import <FBRetainCycleDetectorExtension/FBHeapEnumerationHelper.h>

#import "FBObjectiveCGraph.h"
#import "FBObjectiveCGraphNode.h"

static void _FindCyclesFromNode(FBObjectiveCGraphNode *graphNode,
                           NSMutableSet<FBObjectiveCGraphNode *> *visitedNodes,
                           NSMutableArray<FBObjectiveCGraphNode *> *cycleList)
{
  [visitedNodes addObject:graphNode];
  [cycleList addObject:graphNode];

  // We're interested in the reverse of the graph AKA the incoming edges
  for (FBObjectiveCGraphNode *incomingNode in graphNode.incomingReferences) {
    if (![visitedNodes containsObject:incomingNode]) {
      // Recursive call to traverse
      _FindCyclesFromNode(incomingNode, visitedNodes, cycleList);
    }
  }
}

static void _FillStack(NSMutableArray<FBObjectiveCGraphNode *> *stack,
                       NSMutableSet<FBObjectiveCGraphNode *> *visitedNodes,
                       FBObjectiveCGraphNode *graphNode)
{
  [visitedNodes addObject:graphNode];

  for (FBObjectiveCGraphNode *outgoingNode in graphNode.outgoingReferences) {
    if (![visitedNodes containsObject:outgoingNode]) {
      // Recursive call to fill stack
      _FillStack(stack, visitedNodes, outgoingNode);
    }
  }

  // Push onto stack
  [stack addObject:graphNode];
}

static NSSet<NSArray<FBObjectiveCGraphNode *> *> *_FindCycles(NSSet<FBObjectiveCGraphNode *> *graphNodes)
{
  NSMutableSet<NSArray<FBObjectiveCGraphNode *> *> *retainCycles = [NSMutableSet new];
  NSMutableSet<FBObjectiveCGraphNode *> *visitedNodes = [NSMutableSet new];
  NSMutableArray<FBObjectiveCGraphNode *> *stack = [NSMutableArray new];

  // 1st DFS: Fill up stack according to finish times of nodes
  for (FBObjectiveCGraphNode *graphNode in graphNodes)  {
    if (![visitedNodes containsObject:graphNode]) {
      _FillStack(stack, visitedNodes, graphNode);
    }
  }

  // Clear path
  [visitedNodes removeAllObjects];

  // 2nd DFS: Traverse reverse of the graph
  while ([stack count] > 0) {
    // Pop off the top of the stack
    FBObjectiveCGraphNode *node = [stack lastObject];
    [stack removeLastObject];

    if (![visitedNodes containsObject:node]) {
      NSMutableArray<FBObjectiveCGraphNode *> *cycleList = [NSMutableArray new];

      _FindCyclesFromNode(node, visitedNodes, cycleList);

      // We're only interested in strongly connected components that aren't singular
      if ([cycleList count] > 1) {
        [retainCycles addObject:cycleList];
      }
    }
  }

  return retainCycles;
}

@implementation FBGraphChiselCommands

+ (FBObjectiveCGraph *)buildGraphWithHeap
{
  FBObjectiveCGraph *graph = [FBObjectiveCGraph new];

  FBObjectGraphConfiguration *configuration = [[FBObjectGraphConfiguration alloc] initWithFilterBlocks:@[]
                                                                                   shouldInspectTimers:NO];
  NSArray<FBObjectiveCGraphElement *> *graphElements = [FBHeapEnumerationHelper wrappedElementsFromHeap:configuration];
  [graph buildGraph:graphElements];
  return graph;
}

+ (NSString *)findStrongReferences:(id)object
{
  NSMutableString *descriptionString = [NSMutableString new];

  @autoreleasepool {
    FBObjectiveCGraph *graph = [self buildGraphWithHeap];

    FBObjectiveCGraphElement *graphElement = FBWrapObjectGraphElement(nil, object, [graph graphConfiguration]);
    FBObjectiveCGraphNode *graphNode = [graph nodeForElement:graphElement];

    [descriptionString appendFormat:@"Object: <%@: %zu>\nIncoming References:\n", [graphElement objectClass], [graphElement objectAddress]];
    for (FBObjectiveCGraphNode *incomingNode in graphNode.incomingReferences) {
      [descriptionString appendFormat:@"<- <%@: %zu>\n", [incomingNode.graphElement objectClass],
       [incomingNode.graphElement objectAddress]];
    }
    [descriptionString appendString:@"Outgoing References:\n"];
    for (FBObjectiveCGraphNode *outgoingNode in graphNode.outgoingReferences) {
      [descriptionString appendFormat:@"-> <%@: %zu>\n", [outgoingNode.graphElement objectClass],
       [outgoingNode.graphElement objectAddress]];
    }
  }
  return descriptionString;
}

+ (NSString *)findDuplicates:(id)object
{
  NSMutableString *descriptionString = [NSMutableString new];

  @autoreleasepool {
    FBObjectiveCGraph *graph = [self buildGraphWithHeap];
    int count = 0;

    NSSet<FBObjectiveCGraphNode *> *graphNodes = [graph graphNodes];
    FBObjectiveCGraphElement *wrappedElement = FBWrapObjectGraphElement(nil, object, [graph graphConfiguration]);

    [descriptionString appendFormat:@"Object: <%@: %zu>\n", [wrappedElement objectClass], [wrappedElement objectAddress]];
    for (FBObjectiveCGraphNode *graphNode in graphNodes) {
      if ([wrappedElement hash] == [graphNode.graphElement hash] && [wrappedElement isEqual:graphNode.graphElement]) {
        count++;
        // Duplicate will occur at 2 instances in the graph element list
        if (count > 1) {
          [descriptionString appendFormat:@"<%@: %zu>\n", [graphNode.graphElement objectClass], [graphNode.graphElement objectAddress]];
        }
      }
    }
    [descriptionString appendFormat:@"Duplicate objects: %d", count - 1];
  }
  return descriptionString;
}

+ (NSString *)findRetainCycles
{
  NSMutableString *descriptionString = [NSMutableString new];

  @autoreleasepool {
    FBObjectiveCGraph *graph = [self buildGraphWithHeap];
    NSSet<NSArray<FBObjectiveCGraphNode *> *> *retainCycles = _FindCycles([graph graphNodes]);

    for (NSArray<FBObjectiveCGraphNode *> *cycle in retainCycles) {
      for (FBObjectiveCGraphNode *nodeInPath in cycle) {
        [descriptionString appendFormat:@" -> <%@: %zu>", [nodeInPath.graphElement objectClass], [nodeInPath.graphElement objectAddress]];
      }
      [descriptionString appendString:@"\n"];
    }
  }
  return descriptionString;
}

@end
