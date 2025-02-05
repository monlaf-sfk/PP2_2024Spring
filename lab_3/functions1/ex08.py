def spy_game(nums):
    id = -1
    while True:
        try:
            id = nums.index(7, id+1)
            if nums[:id].count(0) >= 2:
                return True
        except:
            #return False
            break
    return False
# def spy_game(nums):
#     zero_count = 0  #
#     for num in nums:
#         if num == 0:
#             zero_count += 1
#         elif num == 7 and zero_count >= 2:
#             return True
#     return False

spy_game([1,2,4,0,0,7,5]) #True
spy_game([1,0,2,4,0,5,7]) #True
spy_game([1,7,2,0,4,5,0]) #False


print(spy_game([1,2,4,0,0,7,5])) #True
print(spy_game([1,0,2,4,0,5,7])) #True
print(spy_game([1,7,2,0,4,5,0])) #False