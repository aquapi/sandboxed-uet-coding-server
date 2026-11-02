def swap[T](nums: list[T], i: int, j: int):
    nums[i], nums[j] = nums[j], nums[i]


def bubble(nums: list[float]):
    nums_len = len(nums)

    for i in range(nums_len):
        not_swapped = True
        for j in range(nums_len - i - 1):
            if nums[j] > nums[j + 1]:
                swap(nums, j, j + 1)
                not_swapped = False

        if not_swapped:
            break

    return nums


def selection(nums: list[float]):
    nums_len = len(nums)

    for i in range(nums_len):
        min_idx = i
        for j in range(i + 1, nums_len):
            if nums[j] < nums[min_idx]:
                min_idx = j

        if i != min_idx:
            swap(nums, i, min_idx)

    return nums


def insertion(nums: list[float]):
    for i in range(1, len(nums)):
        num = nums[i]

        while i > 0 and nums[i - 1] > num:
            nums[i] = nums[i - 1]
            i -= 1

        nums[i] = num

    return nums


def _merge(nums: list[float], out_nums: list[float], start_idx: int, end_idx: int):
    mid = (start_idx + end_idx) >> 1
    if mid != start_idx:
        _merge(nums, out_nums, start_idx, mid)
        _merge(nums, out_nums, mid, end_idx)

        left_idx = start_idx
        right_idx = mid

        cur_idx = start_idx

        # move to temporary array
        while left_idx < mid and right_idx < end_idx:
            if nums[left_idx] > nums[right_idx]:
                out_nums[cur_idx] = nums[right_idx]
                right_idx += 1
            else:
                out_nums[cur_idx] = nums[left_idx]
                left_idx += 1
            cur_idx += 1

        # paste remaining parts
        while left_idx < mid:
            out_nums[cur_idx] = nums[left_idx]
            left_idx += 1
            cur_idx += 1

        # paste the result back to nums
        for i in range(start_idx, cur_idx):
            nums[i] = out_nums[i]


def merge(nums: list[float]):
    _merge(nums, nums.copy(), 0, len(nums))
    return nums


def lomuto_partition(nums: list[float], start_idx: int, last_idx: int):
    pivot = nums[last_idx]

    pi = start_idx
    for j in range(start_idx, last_idx):
        if nums[j] <= pivot:
            swap(nums, pi, j)
            pi += 1

    swap(nums, pi, last_idx)
    return pi


def hoare_partition(nums: list[float], start_idx: int, last_idx: int) -> int:
    pivot = nums[start_idx]

    while True:
        while nums[start_idx] < pivot:
            start_idx += 1

        while nums[last_idx] > pivot:
            last_idx -= 1

        if start_idx >= last_idx:
            return last_idx

        swap(nums, start_idx, last_idx)

        start_idx += 1
        last_idx -= 1


def _quick(nums: list[float], start_idx: int, last_idx: int):
    if start_idx < last_idx:
        pi = hoare_partition(nums, start_idx, last_idx)
        _quick(nums, start_idx, pi)
        _quick(nums, pi + 1, last_idx)


def quick(nums: list[float]):
    _quick(nums, 0, len(nums) - 1)
    return nums


def builtin(nums: list[float]):
    nums.sort()
    return nums


nums = [float(x) for x in input().split()]

print("bubble sort:", bubble(nums.copy()))
print("selection sort:", selection(nums.copy()))
print("insertion sort:", insertion(nums.copy()))
print("merge sort:", merge(nums.copy()))
print("quick sort:", quick(nums.copy()))
print("builtin sort:", builtin(nums.copy()))
