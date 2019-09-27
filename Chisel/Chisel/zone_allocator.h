// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
//
// This source code is licensed under the MIT license found in the
// LICENSE file in the root directory of this source tree.

#pragma once

#include <memory>

#include <malloc/malloc.h>

template <typename T>
struct zone_allocator {
  using value_type = T;

  T *allocate(std::size_t n)
  {
    auto allocation = malloc_zone_malloc(_zone.get(), n * sizeof(T));
    return reinterpret_cast<T *>(allocation);
  }

  void deallocate(T *p, __unused std::size_t n)
  {
    malloc_zone_free(_zone.get(), p);
  }

  const malloc_zone_t *zone() const
  {
    return _zone.get();
  }

private:
  std::shared_ptr<malloc_zone_t> _zone{malloc_create_zone(0x200, 0), &malloc_destroy_zone};
};

template <typename T, typename U>
bool operator==(const zone_allocator<T> &a, const zone_allocator<T> &b) noexcept
{
  return a.zone() == b.zone();
}

template <typename T, typename U>
bool operator!=(const zone_allocator<T> &a, const zone_allocator<T> &b) noexcept
{
  return !(a == b);
}
