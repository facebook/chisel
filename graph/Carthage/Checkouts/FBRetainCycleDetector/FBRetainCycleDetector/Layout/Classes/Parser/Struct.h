/**
 * Copyright (c) 2016-present, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

#import <Foundation/Foundation.h>

#import "Type.h"

#import <memory>
#import <string>
#import <vector>

namespace FB { namespace RetainCycleDetector { namespace Parser {
  class Struct: public Type {
  public:
    const std::string structTypeName;
    
    Struct(const std::string &name,
           const std::string &typeEncoding,
           const std::string &structTypeName,
           std::vector<std::shared_ptr<Type>> &typesContainedInStruct)
    : Type(name, typeEncoding),
      structTypeName(structTypeName),
    typesContainedInStruct(std::move(typesContainedInStruct)) {};
    Struct(Struct&&) = default;
    Struct &operator=(Struct&&) = default;
    
    Struct(const Struct&) = delete;
    Struct &operator=(const Struct&) = delete;
    
    std::vector<std::shared_ptr<Type>> flattenTypes();
    
    virtual void passTypePath(std::vector<std::string> typePath);
    std::vector<std::shared_ptr<Type>> typesContainedInStruct;
  };
} } }
