//
//  CHLObjCObjectRecognizer.h
//  Chisel
//
//  Copyright © 2016 Facebook. All rights reserved.
//

#import <Foundation/Foundation.h>

#import <malloc/malloc.h>

@interface CHLObjCObjectRecognizer : NSObject

- (BOOL)appearsToRecognize:(vm_range_t)range;

@end
