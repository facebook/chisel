/**
 * Copyright (c) 2016-present, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

#import "Struct.h"

#import <algorithm>

namespace FB { namespace RetainCycleDetector { namespace Parser {
  void Struct::passTypePath(std::vector<std::string> typePath) {
    this->typePath = typePath;
    
    if (name.length() > 0) {
      typePath.emplace_back(name);
    }
    if (structTypeName.length() > 0 && structTypeName != "?") {
      typePath.emplace_back(structTypeName);
    }
    
    for (auto &type: typesContainedInStruct) {
      type->passTypePath(typePath);
    }
  }
  
  std::vector<std::shared_ptr<Type>> Struct::flattenTypes() {
    std::vector<std::shared_ptr<Type>> flattenedTypes;
    
    for (const auto &type:typesContainedInStruct) {
      const auto maybeStruct = std::dynamic_pointer_cast<Struct>(type);
      if (maybeStruct) {
        // Complex type, recursively grab all references
        flattenedTypes.reserve(flattenedTypes.size() + std::distance(maybeStruct->typesContainedInStruct.begin(),
                                                                     maybeStruct->typesContainedInStruct.end()));
        flattenedTypes.insert(flattenedTypes.end(),
                              maybeStruct->typesContainedInStruct.begin(),
                              maybeStruct->typesContainedInStruct.end());
      } else {
        // Simple type
        flattenedTypes.emplace_back(type);
      }
    }
    
    return flattenedTypes;
  }
  
} } }
