---
title: 力扣Hot100的C++题解与复杂度分析
date: 2026-03-14 10:32:30
categories: 计算机
tags:
  - 算法
  - Leetcode
cover: /img/cover_32.jpg
abbrlink: 3324325653
description: 记录一下写题
---

>  解题均采用C++

## 哈希

### 两数之和

-  暴力遍历

```c++
class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        for(int i=0;i<nums.size()-1;i++)
        for(int j=i+1;j<nums.size();j++)
        {
            if(nums[i]+nums[j]==target)
            return {i,j};
        }
    return {};
    }
};
```

复杂度O(n²)，击败69.02%

-  哈希表

```c++
class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        unordered_map<int, int>hash_map;
        for(int i =0;i<nums.size();i++)
        {
            int complentary=target-nums[i];
            if(hash_map.find(complentary)!=hash_map.end())
            return {hash_map[complentary],i};
            hash_map[nums[i]]=i;
        }
        return{};
        }
};
```

复杂度O(n)，击败100%。

### 字母异位词分组

-  标准排序后的字符串为哈希键

```c++
class Solution {
public:
    vector<vector<string>> groupAnagrams(vector<string>& strs) {
        unordered_map<string, vector<string>> hash_map;
        for (const string& s : strs) {
        string key = s;
        sort(key.begin(), key.end());
        hash_map[key].push_back(s);
        }
        vector<vector<string>> result;
        for (auto& pair : hash_map) {
            result.push_back(pair.second);
        }
        return result;

    }
};
```

>  15ms 击败78.46%
>
>  复杂度O(n × k log k)，半靠AI写的，主要是要想到以字符串为键，我原先单纯以int为键，string为value，判断has_map存在顺序版本再加进去，就需要创建多个hash_map版本，很丑陋

-  用质数作哈希键

```c++
class Solution {
public:
    vector<vector<string>> groupAnagrams(vector<string>& strs) {
        int primes[] = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101};
        unordered_map<unsigned long long, vector<string>> hash_map;
        for (const string& s : strs) {
            unsigned long long key = 1;
             const long long MOD = 1e9 + 7;
            for (char c : s) {
                key = (key*primes[c - 'a'])%MOD;
            }
            hash_map[key].push_back(s);
        }
        vector<vector<string>> result;
        for (auto& pair : hash_map) {
            result.push_back(pair.second);
        }
        return result;
    }
};
```

>12ms 击败85.23%
>
>23.59MB 击败91.32%
>
>不再直接用字符串作键，无论速度还是内存都更好，只是MOD需要足够大，不然key会重复，算是逃课做法，正经应该有处理冲突

### 最长连续序列

```c++
class Solution {
public:
    int longestConsecutive(vector<int>& nums) {
       unordered_set<int> hash_set(nums.begin(),nums.end());
        int longest=0;
        for (int num:hash_set)
        {
            if(!hash_set.count(num-1))
            {
                int current_num=num;
                int current_length=1;
                while(hash_set.count(current_num+1))
                {
                    current_num+=1;
                    current_length+=1;
                }
                longest=max(current_length,longest);
            }
        }
        return longest;
    }
};
```

>91ms 击败83.17%
>
>学了一种新的哈希表unordered_set，他的count()适合判断某个值是否存在过
>
>另外一个有趣的是直接遍历nums会超时，但如果遍历整理过的hash_set不会超时

## 双指针

### 移动零

```c++
class Solution {
public:
    void moveZeroes(vector<int>& nums) {
        int fast=0,slow=0;
        for(fast=0;fast<nums.size();fast++)
        {
            if(nums[fast]!=0)
            {   
                int temp=nums[fast];
                nums[fast]=0;
                nums[slow++]=temp;
                
            }
        }
    }
};
```

>复杂度O（n)
>
>0ms 击败100.00%
>
>维护双指针即可

### 盛最多的水

-  暴力遍历

```c++
class Solution {
public:
    int maxArea(vector<int>& height) {
        int fast=0,slow=0;
        int maxArea=0;
        for(slow=0;slow<height.size();slow++)
            for(fast=height.size()-1;fast>slow;fast--)
            {
                int length=min(height[slow],height[fast]);
                int wide = fast-slow;
                maxArea=max(maxArea,length*wide);
            }
        return maxArea;
    }
};
```

O(n^2)超时

-  贪心双指针

```c++
class Solution {
public:
    int maxArea(vector<int>& height) {
        int left=0,right=height.size()-1;
        int maxArea=0;
        while(right>left)
        {
            int length=min(height[left],height[right]);
            int wide = right-left;
            maxArea=max(maxArea,length*wide);
            if (height[left] < height[right]) left++;
            else right--;
        }
        return maxArea;
    }
};
```

>  复杂度O(n)
>
>  4ms击败25.93%

-  再进行一些工程上的小优化

```c++
class Solution {
public:
    int maxArea(vector<int>& height) {
        int left=0,right=height.size()-1;
        int maxArea=0;
        while(right>left)
        {
            int length=min(height[left],height[right]);
            int wide = right-left;
            maxArea=max(maxArea,length*wide);

            if (height[left] < height[right]) {
                int last_h = height[left];
                while (left < right && height[left] <= last_h) left++;
            } 
            else {
                int last_h = height[right];
                while (left < right && height[right] <= last_h) right--;
            }
        }
        return maxArea;
    }
};
```

>  相当于一个小剪枝吧
>
>  0ms 击败100.00%

### 三数之和

-  哈希表

```c++
class Solution {
public:
    vector<vector<int>> threeSum(vector<int>& nums) {
        if (nums.size() < 3) return {};
       sort(nums.begin(), nums.end());
        int i=0,j=0;
        int length=nums.size();
        vector<vector<int>> res;
        for(i=0;i<length;i++)
        {
            if (nums[i] > 0) break;
            while(i>0 && i<length && nums[i]==nums[i-1]) i++;
            unordered_set<int>seen;
            for(j=i+1;j<length;j++)
            {
                int complentary=-nums[j]-nums[i];
                if(seen.count(complentary))
                    {
                        res.push_back({nums[i],nums[j],complentary});
                        while(j+1<length && nums[j]==nums[j+1]) j++;
                    }
                seen.insert(nums[j]);
            }

        }
        return res;
    }
};
```

复杂度O(n^2)

-  双指针

```c++
class Solution {
public:
    vector<vector<int>> threeSum(vector<int>& nums) {
        if (nums.size() < 3) return {};
        sort(nums.begin(), nums.end());
        int length=nums.size();
        vector<vector<int>>res;
        for(int i=0;i<length;i++)
        {
            if(nums[i]>0)break;
            while(i>0 && i<length && nums[i]==nums[i-1]) i++;
            int l=i+1,r=length-1;
            while(r>l)
            {
                int num = nums[i]+nums[r]+nums[l];
                if(num==0)
                {
                    res.push_back({nums[i],nums[r],nums[l]});
                    while(l+1<r && nums[l]==nums[l+1]) l++;
                    while(r-1>l && nums[r]==nums[r-1]) r--;
                    l++;
                    r--;
                }
                else if(num>0)
                    {
                        while(r-1>l && nums[r]==nums[r-1]) r--;
                        r--;
                    }
                else
                {
                    while(l+1<r && nums[l]==nums[l+1]) l++;
                    l++;
                }
            }
        }
        return res;
    }
};
```

>63ms 击败31.78%

-  双指针——更激进的剪枝

```c++
class Solution {
public:
    vector<vector<int>> threeSum(vector<int>& nums) {
        if (nums.size() < 3) return {};
        sort(nums.begin(), nums.end());
        int length=nums.size();
        vector<vector<int>>res;
        for(int i=0;i<length-2;i++)
        {
            if(nums[i]>0)break;
            if (i > 0 && nums[i] == nums[i - 1]) continue;
            if ((long)nums[i] + nums[i + 1] + nums[i + 2] > 0) break; 
            if ((long)nums[i] + nums[length - 2] + nums[length - 1] < 0) continue;
            int l=i+1,r=length-1;
            int target = -nums[i];
            while(r>l)
            {
                int num = nums[l] + nums[r];
                if(num==target)
                {
                    res.push_back({nums[i],nums[r],nums[l]});
                    
                    while(l+1<r && nums[l]==nums[l+1]) l++;
                    l++;
                    
                    while(r-1>l && nums[r]==nums[r-1]) r--; 
                    r--; 
                }
                else if(num>target)
                    {
                        // while(r-1>l && nums[r]==nums[r-1]) r--;
                        r--;
                    }
                else
                {
                    // while(l+1<r && nums[l]==nums[l+1]) l++;
                    l++;
                }
            }
        }
        return res;
    }
};
```

>  40ms 击败96.08%

### 接雨水

-  快慢双指针

```c++
class Solution {
public:
    int trap(vector<int>& height) {
        int n = height.size();
        if (n < 3) return 0;

        int total = 0;
        int peak = 0;
        int slow = 0;
        for (int fast = 1; fast < n; ++fast) {
            if(height[fast]==0)continue;
            if (height[fast] >= height[slow]) {
                for (int i = slow + 1; i < fast; ++i) {
                    total += (height[slow] - height[i]);
                }
                slow = fast;
            }
        }
        peak = slow;
        slow = n-1;
        for(int fast = n-2;fast>=peak;fast--)
        {
            if(height[fast]==0)continue;
            if (height[fast] >= height[slow]) {
                for (int i = slow - 1; i > fast; --i) {
                    total += (height[slow] - height[i]);
                }
                slow = fast;
                }
        }
    return total;
        
    }
};
```

>  自己胡乱搞的方法，竟然效果不错，时间复杂度O(n),空间复杂度O(1)
>
>  0ms 击败100.00%

-  左右双指针

```c++
class Solution {
public:
    int trap(vector<int>& height) {
        int n = height.size();
        if (n < 3) return 0;

        int left = 0,right=n-1;
        int total = 0;
        int leftMax=0,rightMax=0;
        while(left<right)
        {
            if(height[left]<height[right])
            {
                if(height[left]>=leftMax)
                    leftMax=height[left];
                else
                    total+=leftMax-height[left];
                left++;
            }
            else
            {
                if(height[right]>=rightMax)
                    rightMax=height[right];
                else
                    total+=rightMax-height[right];
                right--;
            }
        }
        return total;
        
    }
};
```

>  也是时间复杂度O(n),空间复杂度O(1)，0ms 击败100.00%
>
>  但我觉得应该是这种方法更快

## 滑动窗口

### 无重复字符的最长子串

```c++
class Solution {
public:
    int lengthOfLongestSubstring(string s) {
        int n = s.size();
        vector<int> last_pos(128, -1);
        int left=-1;
        int MaxLength=0;
        for (int right = 0; right < s.size(); ++right)
        {
            int current_left = last_pos[s[right]];
            if(current_left>left)
                left = current_left;
            last_pos[s[right]]=right;
            MaxLength = max(MaxLength,AIright-left);
        }   
        return MaxLength;
    }
};
```

>  AI给的解法思路，确实相当精妙
>
>  复杂度O(n)
>
>  0ms 击败100.00%

### 字母异位词

```c++
class Solution {
public:
    vector<int> findAnagrams(string s, string p) {
        int n = s.size();
        int m = p.size();
        if(n<m) return {};
        vector<int> char_pcnt(26, 0);
        vector<int> char_ncnt(26, 0);
        vector<int> res;
        
        for(int i=0;i<m;i++)
        {
            char_pcnt[p[i]-'a']++;
            char_ncnt[s[i]-'a']++;
        }
        int i=0;
        while(i+m-1<n)
        {
            if(char_ncnt==char_pcnt)
                res.push_back(i);
            char_ncnt[s[i]-'a']--;
            if(i+m<n)
            char_ncnt[s[i+m]-'a']++;
            i++;
            
        }
        return res;
    }
};
```

>  复杂度O(n)，只是char_ncnt==char_pcnt这样内含26次比较，可进一步优化
>
>  0ms 击败100.00%

## 子串

### 和为k的子数组

-  暴力遍历

```c++
class Solution {
public:
    int subarraySum(vector<int>& nums, int k) {
        int n = nums.size();
        int cnt=0;
        for(int i = 0;i<n;i++)
        {
            int result = 0;
            for(int j = i;j<n;j++)
            {
                result+=nums[j];
                if(result==k)
                    {
                        cnt++;
                    }
            }
        }
        return cnt;
    }
};
```

>  复杂度O(n^2)，2904ms 击败5.01%

-  遍历前缀和

```c++
class Solution {
public:
    int subarraySum(vector<int>& nums, int k) {
        int n = nums.size();
        int *prefix = (int*)malloc((n+1) * sizeof(int));
        int cnt=0;
        for(int i=1;i<=n;i++)
            prefix[i]=prefix[i-1]+nums[i-1];
        for(int i = 0;i<n;i++)
        {
            for(int j = i;j<n;j++)
            {
                if(prefix[j+1]-prefix[i]==k)
                cnt++;
            }
        }
        return cnt;
    }
};
```

>  还是O(n^2)，但节省了每次计算result
>
>  2116ms 击败12.89%

-  哈希优化

```c++
class Solution {
public:
    int subarraySum(vector<int>& nums, int k) {
        int n = nums.size();
        int *prefix = (int*)calloc(n+1, sizeof(int)); 
        unordered_map<int, int> hash_map;
        int cnt=0;
        for(int i=1;i<=n;i++)
            prefix[i]=prefix[i-1]+nums[i-1];
        for(int i = 0;i<n;i++)
        {
            hash_map[prefix[i]]++;
            int target = prefix[i+1] - k;
            if(hash_map.count(target)) {
                cnt += hash_map[target];
            }
        }
        return cnt;
    }
};
```

>  复杂度O(n)
>
>  51ms 击败43.88%

-  前缀和计算优化

```c++
class Solution {
public:
    int subarraySum(vector<int>& nums, int k) {
        int n = nums.size();
        unordered_map<int, int> hash_map;
        int cnt=0;
        int pre=0;
        for(int i = 0;i<n;i++)
        {
            hash_map[pre]++;
            pre+=nums[i];
            int target = pre - k;
            if(hash_map.find(pre-k)!=hash_map.end()) {
                cnt += hash_map[target];
            }
        }
        return cnt;
    }
};
```

>  前缀和的计算可以放在循环中来优化，另外发现hash_map.find()比hash_map.count()更快
>
>  复杂度O(n) 36ms 击败88.47%

### 滑动窗口最大值

-  遍历维护

```c++
class Solution {
public:
    void max_update(int& now_max, int new_num, int old_num, vector<int>& nums, int start, int end) {
        if (new_num >= now_max) {
            now_max = new_num;
        } else if (old_num == now_max) {
            now_max = nums[start];
            for (int i = start + 1; i <= end; i++) {
                if (nums[i] > now_max) now_max = nums[i];
            }
        }
    }

    vector<int> maxSlidingWindow(vector<int>& nums, int k) {
        if (nums.empty()) return {};
        vector<int> res;
        int max_num = nums[0];
        for (int i = 1; i < k; i++) {
            max_num = max(max_num, nums[i]);
        }
        res.push_back(max_num);
        for (int i = k; i < nums.size(); i++) {
            int old_num = nums[i - k];
            int new_num = nums[i];
            max_update(max_num, new_num, old_num, nums, i - k + 1, i);
            
            res.push_back(max_num);
        }
        
        return res;
    }
};
```

>  复杂度O(NK)，超时

-  双口deque

```c++
class Solution {
public:
    void deque_update(deque<int>&dq,int old_num,int new_num)
    {
        if (dq.front()==old_num)
            dq.pop_front();
        while(!dq.empty()&&dq.back()<new_num)
            dq.pop_back();
        dq.push_back(new_num);
    }
    vector<int> maxSlidingWindow(vector<int>& nums, int k) {
        if (nums.empty()) return {};
        vector<int> res;
        deque<int>dq;
        for(int i=0;i<k;i++)
        {   while (!dq.empty() && dq.back() < nums[i]) 
            dq.pop_back();
            dq.push_back(nums[i]);
        }
        res.push_back(dq.front());
        for(int i=k;i<nums.size();i++)
        {
            int old_idx=i-k;
            int new_idx=i;
            int old_num=nums[old_idx];
            int new_num=nums[new_idx];
            deque_update(dq,old_num,new_num);
            res.push_back(dq.front());
        }
        return res;
    }
};
```

>  复杂度O(N)，queue中只需存放大于new_num的数
>
>  23ms 击败82.29%

### 最小覆盖子串

```c++
class Solution {
public:
    string minWindow(string s, string t) {
        int m = s.size();
        int n = t.size();
        if(m<n)return{};
        int need[128] = {0};
        int window[128] = {0};
        pair<int, int> result = {0, INT_MAX};

        int left=0,right=0,valid=0,requiredTypes=0;
        for (char c : t) {
            if (need[c] == 0) requiredTypes++;
            need[c]++;
        }
        while (right < m) {
            char c = s[right];
            right++;
            if (need[c] > 0) {
                window[c]++;
                if (window[c] == need[c]) {
                    valid++;
                }
            }
            while (valid == requiredTypes) {
                if (right - left < result.second - result.first) {
                    result = {left, right};
                }
                char d = s[left++];
                if (need[d] > 0) {
                    if (window[d] == need[d]) valid--;
                    window[d]--;
                }
    }
            
        }
        if (result.second==INT_MAX) return {};
        int start = result.first;
        int len = result.second - result.first; 
        string sub = s.substr(start, len);
        return sub;
    }
};
```

>  复杂度是 <img src="https://www.zhihu.com/equation?tex=O(m + n)" alt="O(m + n)" class="ee_img tr_noresize" eeimg="1"> ,0ms 击败100.00%

### 最大数组和

-  前缀和

```c++
class Solution {
public:
    int maxSubArray(vector<int>& nums) {
        int n = nums.size();
        int max_subsum=nums[0],min_sum=0;
        int current_pre_sum=0;
        for(int i = 0;i<n;i++)
        {
            current_pre_sum+=nums[i];
            max_subsum=max(max_subsum,current_pre_sum-min_sum);
            min_sum=min(min_sum,current_pre_sum);
        }
        return max_subsum;
    }
};
```

>  复杂度O(n),0ms 击败100.00%
>
>  也是比较简单的，只要那当前最大前缀和减去在这之前的最小前缀和即可

-  动态规划

```c++
class Solution {
public:
    int maxSubArray(vector<int>& nums) {
        int max_res=nums[0];
        int current_dp=0;
        for(int x:nums)
        {
            current_dp=max(x,current_dp+x);
            max_res=max(max_res,current_dp);
        }
        return max_res;
    }
};
```

>  复杂度O(n),0ms 击败100.00%
>
>  也是比较经典的了

### 合并区间

-  排序后合并

```c++
class Solution {
public:
    vector<vector<int>> merge(vector<vector<int>>& intervals) {
        vector<vector<int>>res;
        
        sort(intervals.begin(), intervals.end());
        res.push_back(intervals[0]);
        int n = intervals.size();
        for(int i=1;i<n;i++)
        {
            vector<int>& last = res.back();
            vector<int>  now = intervals[i];
            if(now[0]<=last[1]&&now[1]>=last[1])
                last[1]=now[1];
            else if(now[0]>last[1])
                res.push_back(now);
        }
        return res;
    }
};
```

>  复杂度 <img src="https://www.zhihu.com/equation?tex=O(n \log n)" alt="O(n \log n)" class="ee_img tr_noresize" eeimg="1"> （都在sort上了）15ms 击败13.61%

```c++
class Solution {
public:
    vector<vector<int>> merge(vector<vector<int>>& intervals) {
        if (intervals.empty()) return {};
        vector<vector<int>>res;
        sort(intervals.begin(), intervals.end());
        res.push_back(intervals[0]);
        int n = intervals.size();
        for(int i=1;i<n;i++)
        {
            vector<int>& last = res.back();
            vector<int>  now = intervals[i];
            if (now[0] <= last[1]) {
                last[1] = max(last[1], now[1]);
            }
            else
                res.push_back(now);
        }
        return res;
    }
};
```

>  简单优化掉了一些判断逻辑 7ms击败60.63%

### 缺失的第一个正数

```c++
class Solution {
public:
    int firstMissingPositive(vector<int>& nums) {
        int n=nums.size();
        for(int i=0;i<n;i++)
        {
            while(nums[i]>0 &&nums[i]-1<n&& nums[nums[i]-1]!=nums[i])
                swap(nums[i],nums[nums[i]-1]);
        }
        for(int i=0;i<n;i++)
            if(nums[i]!=i+1)
                return i+1;
        return n+1;
    }
};
```

>换凳子想法，复杂度O(n)（虽然有个while，但大部分很早能停止）
>
>0ms 击败100.00%
>
>前面写一个哈希表的，直接插入，到最后看哪个不在，更好想，但六十多ms

## 矩阵

### 矩阵置零

```python
class Solution {
public:
    void setZeroes(vector<vector<int>>& matrix) {
        int row = matrix.size();
        int column = matrix[0].size();
        bool column_0 =false;
        bool row_0=false;
        for(int j=0;j<column;j++)
        if(matrix[0][j]==0) row_0=true;
        for(int i=0;i<row;i++)
        if(matrix[i][0]==0) column_0=true;

        for(int j=1;j<column;j++)
        {
            for(int i=1;i<row;i++)
            {
                if(matrix[i][j]==0)
                {
                    matrix[i][0]=0;
                    matrix[0][j]=0;
                }
            }
        }
        for(int j=1;j<column;j++)
        if(matrix[0][j]==0)
        for(int i=1;i<row;i++)
        matrix[i][j]=0;
        for(int i=1;i<row;i++)
        if(matrix[i][0]==0)
        for(int j=1;j<column;j++)
        matrix[i][j]=0;
        if(column_0)
            for(int i=0;i<row;i++)
                matrix[i][0]=0;
        if(row_0)
            for(int j=0;j<column;j++)
                matrix[0][j]=0;
        
    }
};
```

>  复杂度O（N×M）
>
>  0ms 击败100.00%
>
>  代码逻辑写的有些冗杂，但能跑就行

### 螺旋矩阵

写死的四边界就不写了，题解有一个很高效的方法

```c++
class Solution {
public:
    static constexpr int dire[4][2] = {{0, 1}, {1, 0}, {0, -1}, {-1, 0}};
    vector<int> spiralOrder(vector<vector<int>>& matrix) {
        int m = matrix.size(), n = matrix[0].size();
        int size = m * n;
        vector<int> ans;
        int i = 0, j = -1;
        for (int di = 0; ans.size() < size; di = (di + 1) % 4) {
            for (int k = 0; k < n; ++k) {
                i += dire[di][0];
                j += dire[di][1];
                ans.push_back(matrix[i][j]);
            }
            swap(--m, n);
        }
        return ans;
    }
};
```

通过交换m,n收缩避免了四边界的冗余逻辑

### 转置矩阵

-  先旋转后转置

```python
class Solution {
public:
    void rotate(vector<vector<int>>& matrix) {
        int n = matrix.size();
        
        // 1. 转置矩阵（沿主对角线翻转）
        for (int i = 0; i < n; i++) {
            for (int j = i + 1; j < n; j++) {
                swap(matrix[i][j], matrix[j][i]);
            }
        }
        
        // 2. 每行翻转（左右翻转）
        for (int i = 0; i < n; i++) {
            reverse(matrix[i].begin(), matrix[i].end());
        }
    }
};
```

```python
class Solution {
public:
    void rotate(vector<vector<int>>& matrix) {
        int size=matrix.size();
        int start=0,end=size-1;
        while(end-start>0)
        {
        for(int i=start;i<end;i++)
        {
            int temp=start;
            int y=start,x=i;
            for(int j=0;j<3;j++)
            {swap(matrix[y][x],matrix[size-1-x][y]);
            int y_temp=y;
            y=size-1-x;
            x=y_temp;
            }
            
        }
        start++;
        end--;
        }
    }
};
```

自己写的比较脏的

### 搜索二维矩阵

暴力遍历

```c++
    bool searchMatrix(vector<vector<int>>& matrix, int target) {
        int m =matrix.size();
        int n =matrix[0].size();
        int y_idx=0,x_idx=0;
        while(y_idx<n&&matrix[0][y_idx++]<target);
        while(x_idx<m&&matrix[x_idx++][0]<target);
        for(int i=0;i<y_idx;i++)
        {
            if(matrix[0][i]>target) continue;
            if(matrix[x_idx-1][i]<target) continue;
        for(int j=0;j<x_idx;j++)
            if(matrix[j][i]==target)
            return true;
        }
        return false;
    }
```

>  自己写的比较脏的 63ms

右上角剪枝搜索

```c++
class Solution {
public:
    bool searchMatrix(vector<vector<int>>& matrix, int target) {
        int m =matrix.size();
        int n =matrix[0].size();
        int i=0,j=n-1;
        while(i<m&&j>=0)
        {
            
            if(matrix[i][j]>target)
                j--;
            else if(matrix[i][j]<target)
                i++;
            else 
                return true;
        }
        return false;
    }
};
```

>  复杂度O（m+n)，43ms

## 链表

### 相交链表

```c++
class Solution {
public:
    ListNode *getIntersectionNode(ListNode *headA, ListNode *headB) {
        if (headA == nullptr || headB == nullptr) 
            return nullptr;
        
        ListNode* pA = headA;
        ListNode* pB = headB;
        
        while (pA != pB) {
            pA = (pA == nullptr) ? headB : pA->next;
            pB = (pB == nullptr) ? headA : pB->next;
        }
        
        return pA;
    }
};
```

>  复杂度O(m+n)

### 反转链表

```c++
/**
 * Definition for singly-linked list.
 * struct ListNode {
 *     int val;
 *     ListNode *next;
 *     ListNode() : val(0), next(nullptr) {}
 *     ListNode(int x) : val(x), next(nullptr) {}
 *     ListNode(int x, ListNode *next) : val(x), next(next) {}
 * };
 */
class Solution {
public:
    ListNode* reverseList(ListNode* head) {
        if (head == nullptr || head->next == nullptr) {
        return head;
        }
        ListNode* newHead=reverseList(head->next);
        head->next->next=head;
        head->next=nullptr;
        return newHead;

    }
};
```

>  关键是要想通

### 环形链表

```c++
/**
 * Definition for singly-linked list.
 * struct ListNode {
 *     int val;
 *     ListNode *next;
 *     ListNode(int x) : val(x), next(NULL) {}
 * };
 */
class Solution {
public:
    bool hasCycle(ListNode *head) {
        while(head!=nullptr)
        {
            if(head->val == INT_MAX)
                return true;
            head->val=INT_MAX;
            head=head->next;
        }
        return false;

    }
};
```

>  逃课写法 复杂度O(n)
>
>  12ms 击败42.83%

-  快慢指针

```c++
/**
 * Definition for singly-linked list.
 * struct ListNode {
 *     int val;
 *     ListNode *next;
 *     ListNode(int x) : val(x), next(NULL) {}
 * };
 */
class Solution {
public:
    bool hasCycle(ListNode *head) {
        if (head == nullptr || head->next == nullptr) {
            return false;
        }
        ListNode* slow = head;
        ListNode* fast = head->next;
        while(slow != nullptr && fast != nullptr && fast->next != nullptr)
        {
            if(slow == fast)
                return true;
            slow = slow->next;
            fast = fast->next->next;
        }
        return false;
    }
}; 
```

>  复杂度O(n)，一样12ms

### k个一组翻转链表

-  递归的局部翻转

```c++

class Solution {
public:
    ListNode* Reverse(ListNode* head, int k)
    {
        if(k==1)return head;
        ListNode* newhead=Reverse(head->next,k-1);
        head->next->next=head;
        head->next=nullptr;
        return newhead;
    }
    ListNode* reverseKGroup(ListNode* head, int k) {

        ListNode*nexthead=head;
        if(!head)return nullptr;
        for(int i=0;i<k;i++)
        {
            if(!nexthead)
                return head;
            nexthead=nexthead->next;
        }
        ListNode*newhead=Reverse(head,k);
        head->next=reverseKGroup(nexthead,k);
        return newhead;
    }
};
```

-  迭代翻转

```c++

class Solution {
public:
    ListNode* Reverse(ListNode* head, int k)
    {
        if(k==1)return head;
        ListNode* curr=head->next;
        ListNode* newhead=head->next;
        ListNode* prev=head;
        for(int i=0;i<k-1;i++)
        {
            ListNode*tmp=curr->next;
            curr->next=prev;
            prev=curr;
            curr=tmp;
        }
        return prev;
    }
    ListNode* reverseKGroup(ListNode* head, int k) {

        ListNode*nexthead=head;
        if(!head)return nullptr;
        for(int i=0;i<k;i++)
        {
            if(!nexthead)
                return head;
            nexthead=nexthead->next;
        }
        ListNode*newhead=Reverse(head,k);
        head->next=reverseKGroup(nexthead,k);
        return newhead;
    }
};
```

>  复杂度一样，只是迭代翻转用内存更少，能用递归还是递归吧，逻辑更清晰

### 二叉搜索树第k小

```c++
/**
 * Definition for a binary tree node.
 * struct TreeNode {
 *     int val;
 *     TreeNode *left;
 *     TreeNode *right;
 *     TreeNode() : val(0), left(nullptr), right(nullptr) {}
 *     TreeNode(int x) : val(x), left(nullptr), right(nullptr) {}
 *     TreeNode(int x, TreeNode *left, TreeNode *right) : val(x), left(left), right(right) {}
 * };
 */
class Solution {
public:
    int kthSmallest(TreeNode* root, int k) {
        stack<TreeNode*>s;
        TreeNode* curr=root;
        int count=k;

        while(curr||!s.empty())
        {
            while(curr)
            {
                s.push(curr);
                curr=curr->left;
            }
            curr=s.top();
            s.pop();
            count--;
            if(count==0) return curr->val;
            curr=curr->right;
        }
        return 0;
    }
};
```

>  直接中序遍历就可，题解有考虑更复杂场景的操作

## 图

### 岛屿数量

```c++
class Solution {
public:
int dx[4]={1,0,-1,0};
int dy[4]={0,1,0,-1};
int m,n;
int count;
void dfs(int x,int y, vector<vector<char>>& grid,vector<vector<bool>>& visited) {
    visited[x][y]=true;
    for(int i=0;i<4;i++)
    {
        int new_x=x+dx[i];
        int new_y=y+dy[i];
        bool x_in=new_x>=0&&new_x<m;
        bool y_in=new_y>=0&&new_y<n;
        if(x_in&&y_in&&!visited[new_x][new_y]&&grid[new_x][new_y]=='1')
        dfs(new_x,new_y,grid,visited);
    }
    }
    int numIslands(vector<vector<char>>& grid) {
        m=grid.size();
        n=grid[0].size();
        vector<vector<bool>> visited(m, vector<bool>(n, false));

        for(int i=0;i<m;i++)
        for(int j=0;j<n;j++)
        {
            if(!visited[i][j]&&grid[i][j]=='1')
            {
            count++;
            dfs(i,j,grid,visited);
            }
        }
        return count;
    }
};
```

### 课程表

```c++
class Solution {
public:
    bool canFinish(int numCourses, vector<vector<int>>& prerequisites) {
        int zero_count=0;
        vector<vector<int>> adj(numCourses);
        vector<int> in_degrees(numCourses, 0);
        for(const auto& pair:prerequisites)
        {
            adj[pair[1]].push_back(pair[0]);
            in_degrees[pair[0]]++;
        }
        queue<int>zero_in;
        for(int i=0;i<numCourses;i++)
            if(in_degrees[i]==0)
            zero_in.push(i);
        while(!zero_in.empty())
        {
            int tmp=zero_in.front();
            zero_in.pop();
            zero_count++;
            for(int next_course:adj[tmp])
                {
                    in_degrees[next_course]--;
                    if(in_degrees[next_course]==0)
                        zero_in.push(next_course);
                }
        }
        return zero_count==numCourses;
    }
};
```

>  拓扑排序判断是否有环：不断剔除入度为0的点，若最后有没有剔除的节点，证明有环

```c++
class Solution {
public:
    bool canFinish(int numCourses, vector<vector<int>>& prerequisites) {
        int16_t zero_count=0;
        vector<vector<int16_t>> adj(numCourses);
        vector<int16_t> in_degrees(numCourses, 0);
        for(const auto& pair:prerequisites)
        {
            adj[pair[1]].push_back(pair[0]);
            in_degrees[pair[0]]++;
        }
        queue<int16_t>zero_in;
        for(int16_t i=0;i<numCourses;i++)
            if(in_degrees[i]==0)
            zero_in.push(i);
        while(!zero_in.empty())
        {
            int16_t tmp=zero_in.front();
            zero_in.pop();
            zero_count++;
            for(int16_t next_course:adj[tmp])
                {
                    in_degrees[next_course]--;
                    if(in_degrees[next_course]==0)
                        zero_in.push(next_course);
                }
        }
        return zero_count==numCourses;
    }
};
```

>  全部换成int16_t，速度和内存都快了，也是逃课方法吧

## 回溯

### 全排列

```c++
class Solution {
public:
    vector<vector<int>> res;
    vector<int>Path;
    int n;
    void backtracking(vector<int>& nums,vector<bool>& visited)
    {

        if(Path.size()==nums.size()) 
        {
            res.push_back(Path);
            return;
        }
        for(int i=0;i<n;i++)
        {
            if(visited[i])continue;
            Path.push_back(nums[i]);
            visited[i]=true;
            backtracking(nums,visited);
            Path.pop_back();
            visited[i]=false;
        }

    }
    vector<vector<int>> permute(vector<int>& nums) {
        n=nums.size();
        vector<bool> visited(n,false);
        backtracking(nums,visited);
        return res;
    }
};
```

>  0ms击败100.00%
>
>  学习了下回溯算法