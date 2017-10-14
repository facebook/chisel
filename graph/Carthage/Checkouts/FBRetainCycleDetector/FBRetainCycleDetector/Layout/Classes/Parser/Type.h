/**
 * Copyright (c) 2016-present, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

#import <Foundation/Foundation.h>

#import <memory>
#import <string>
#import <vector>

#import "BaseType.h"

namespace FB { namespace RetainCycleDetector { namespace Parser {
  class Type: public BaseType {
  public:
    const std::string name;
    const std::string typeEncoding;
    
    Type(const std::string &name,
         const std::string &typeEncoding): name(name), typeEncoding(typeEncoding) {}
    Type(Type&&) = default;
    Type &operator=(Type&&) = default;
    
    Type(const Type&) = delete;
    Type &operator=(const Type&) = delete;
    
    virtual void passTypePath(std::vector<std::string> typePath) {
      this->typePath = typePath;
    }
    
    std::vector<std::string> typePath;
  };
} } }
