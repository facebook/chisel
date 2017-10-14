/**
 * Copyright (c) 2016-present, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

#import "FBStructEncodingParser.h"

#import <algorithm>
#import <memory>
#import <string>
#import <unordered_set>
#import <vector>

#import "BaseType.h"

namespace {
  class _StringScanner {
  public:
    const std::string string;
    size_t index;
    
    _StringScanner(const std::string &string): string(string), index(0) {}
    
    bool scanString(const std::string &stringToScan) {
      if (!(string.compare(index, stringToScan.length(), stringToScan) == 0)) {
        return false;
      }
      index += stringToScan.length();
      return true;
    }
    
    const std::string scanUpToString(const std::string &upToString) {
      size_t pos = string.find(upToString, index);
      if (pos == std::string::npos) {
        // Mark as whole string scanned
        index = string.length();
        return "";
      }
      
      std::string inBetweenString = string.substr(index, pos - index);
      index = pos;
      return inBetweenString;
    }
    
    const char currentCharacter() {
      return string[index];
    }
    
    const std::string scanUpToCharacterFromSet(const std::string &characterSet) {
      size_t pos = string.find_first_of(characterSet, index);
      if (pos == std::string::npos) {
        index = string.length();
        return "";
      }
      
      std::string inBetweenString = string.substr(index, pos-index);
      index = pos;
      return inBetweenString;
    }
  };
  
};

namespace FB { namespace RetainCycleDetector { namespace Parser {
  
  /**
   Intermediate struct object used inside the algorithm to pass some
   information when parsing nested structures.
   */
  struct _StructParseResult {
    std::vector<std::shared_ptr<Type>> containedTypes;
    const std::string typeName;
  };
  
  static const auto kOpenStruct = "{";
  static const auto kCloseStruct = "}";
  static const auto kLiteralEndingCharacters = "\"}";
  static const auto kQuote = "\"";
  
  static struct _StructParseResult _ParseStructEncodingWithScanner(_StringScanner &scanner) {
    std::vector<std::shared_ptr<BaseType>> types;
    
    // Every struct starts with '{'
    __unused const auto scannedCorrectly = scanner.scanString(kOpenStruct);
    NSCAssert(scannedCorrectly, @"The first character of struct encoding should be {");
    
    // Parse name
    const auto structTypeName = scanner.scanUpToString("=");
    scanner.scanString("=");
    
    while (!(scanner.scanString(kCloseStruct))) {
      if (scanner.scanString(kQuote)) {
        const auto parseResult = scanner.scanUpToString(kQuote);
        scanner.scanString(kQuote);
        if (parseResult.length() > 0) {
          types.push_back(std::make_shared<Unresolved>(parseResult));
        }
      } else if (scanner.currentCharacter() == '{') {
        // We do not want to consume '{' because we will call parser recursively
        const auto locBefore = scanner.index;
        auto parseResult = _ParseStructEncodingWithScanner(scanner);
        
        const auto nameFromBefore = std::dynamic_pointer_cast<Unresolved>(types.back());
        NSCAssert(nameFromBefore, @"There should always be a name from before if we hit a struct");
        types.pop_back();
        std::shared_ptr<Struct> type = std::make_shared<Struct>(nameFromBefore->value,
                                                                scanner.string.substr(locBefore, (scanner.index - locBefore)),
                                                                parseResult.typeName,
                                                                parseResult.containedTypes);
        
        types.emplace_back(type);
      } else {
        // It's a type name (literal), let's advance until we find '"', or '}'
        const auto parseResult = scanner.scanUpToCharacterFromSet(kLiteralEndingCharacters);
        std::string nameFromBefore = "";
        if (types.size() > 0) {
          if (std::shared_ptr<Unresolved> maybeUnresolved = std::dynamic_pointer_cast<Unresolved>(types.back())) {
            nameFromBefore = maybeUnresolved->value;
            types.pop_back();
          }
        }
        std::shared_ptr<Type> type = std::make_shared<Type>(nameFromBefore, parseResult);
        types.emplace_back(type);
      }
    }
    
    std::vector<std::shared_ptr<Type>> filteredVector;
    
    for (const auto &t: types) {
      if (const auto convertedType = std::dynamic_pointer_cast<Type>(t)) {
        filteredVector.emplace_back(convertedType);
      }
    }
    
    return {
      .containedTypes = filteredVector,
      .typeName = structTypeName,
    };
  }
  
  Struct parseStructEncoding(const std::string &structEncodingString) {
    return parseStructEncodingWithName(structEncodingString, "");
  }
  
  Struct parseStructEncodingWithName(const std::string &structEncodingString,
                                     const std::string &structName) {
    _StringScanner scanner = _StringScanner(structEncodingString);
    auto result = _ParseStructEncodingWithScanner(scanner);
    
    Struct outerStruct = Struct(structName,
                                structEncodingString,
                                result.typeName,
                                result.containedTypes);
    outerStruct.passTypePath({});
    return outerStruct;
  }
} } }
